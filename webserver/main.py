from flask import Flask, jsonify, render_template
import dotenv
import time
from _inference import predict
from lsl import list_available_lsl_streams, start_eeg_stream
import numpy as np
import os


# --- envs
dotenv.load_dotenv()


# --- main handling function
glob_last_inference:float = time.time()  # return seconds since epoch
glob_cogload = 0    # between 0 and 1 (corresponds to 100% and 200% video speed)
glob_focus = 0  # between 0 and 1 (corresponds to completely drowsy vs full focus)


def handle_eeg(buffer, sfreq):
    global glob_last_inference, glob_cogload, glob_focus
    
    # run every half second max
    if (time.time() - glob_last_inference) < 0.5:
        return
    
    glob_last_inference = time.time()

    
    # 4 seconds needed for cogload
    if len(buffer) >= (sfreq * 4):
        start = time.perf_counter()

        data = np.array(buffer[-sfreq*4:]).T
        probs = predict(data)
        pred = np.argmax(probs, axis=1) # 0 for low, 1 for high probably
        
        end = time.perf_counter()
        confidence = probs[0][pred[0]]
        
        glob_cogload = confidence
        print(f"predicted {pred[0]} at {confidence}% in: {(end - start) * 1000:.3f} ms")
    
    # 15 seconds needed for focus
    if len(buffer) >= (sfreq * 15):
        pass # TODO

# --- init
app = Flask(__name__)


        
# --- routes
@app.get("/data")
def dataRoute():
    global glob_cogload, glob_focus
    
    return jsonify({
        "cogload": str(glob_cogload),
        "focus": str(glob_focus)
    })
    
@app.get("/")
def mainRoute():
    return render_template("main.html")
    



# --- running
if __name__ == "__main__":
    streams = list_available_lsl_streams()
    
    if not streams:
        print("No LSL streams found. Make sure your devices are connected and streaming.")
        exit()

    stream_idx = int(input("Enter the number of the stream you want to capture: ")) - 1
    stream_info = start_eeg_stream(stream_index=stream_idx, handle_eeg=handle_eeg, max_rate=128)
    
    expected_channels = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']
    expected_sfreq = 128    
    
    real_channels = stream_info["ch_names"]
    real_sfreq = stream_info["sfreq"]
    
    if real_channels != expected_channels:
        stream_info['stop_flag'].set()
        raise Exception(f"{str(real_channels)} is not as expected")
    
    if real_sfreq != expected_sfreq:
        stream_info['stop_flag'].set()
        raise Exception(f"{str(real_sfreq)} is not as expected")
    
    print("starting webserver")
    app.run(port=8080, debug=True)
    
    print("flask exited, closing stream")
    stream_info['stop_flag'].set()