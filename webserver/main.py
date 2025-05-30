from flask import Flask, jsonify, render_template, render_template_string
import dotenv
import time
from _models import predict_cogload, predict_focus
from lsl_read import list_available_lsl_streams, start_eeg_stream
import numpy as np
import os


# --- envs
dotenv.load_dotenv()


# --- main handling function
glob_last_inference:float = time.time()  # return seconds since epoch
glob_buffer = []
glob_cogload = 0    # between 0 and 1 (corresponds to 100% and 200% video speed)
glob_focus = 0  # between 0 and 1 (corresponds to completely drowsy vs full focus)

expected_channels = ['F7','F3','P7','O1','O2','P8','F4']
expected_sfreq = 128  

# - callibration shit
glob_focus_callibration_started = False

def handle_focus_callibration(sfreq):
    global glob_focus_callibration_started, glob_buffer
    
    buffer = glob_buffer[-sfreq*80:]
    print("\n\n--- imagine we just finetune ---\n\n") # TODO finetune 
    
    glob_focus_callibration_started = False
    
    

# - 
def softmax(x):
    exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=1, keepdims=True)


# - passed to subthread
def handle_eeg(sample, sfreq:float, real_channels:list):
    global glob_last_inference, glob_cogload, glob_focus, glob_buffer
    global glob_focus_callibration_started
    
    # --- append to buffer - limit to 180s !!!!!
    glob_buffer.append(sample)

    if len(glob_buffer) > (sfreq * 180):
        glob_buffer[:] = glob_buffer[-(int(sfreq * 180)):]


    # --- collect to buffer if
    if glob_focus_callibration_started and (len(glob_buffer) >= int(sfreq * 80)):
        handle_focus_callibration()
        
        
    # --- run inference only every half second max
    if (time.time() - glob_last_inference) < 0.5:
        return
    
    glob_last_inference = time.time()
    
    
    # -- handle shitty openbci stream
    if real_channels == ['', '', '', '', '', '', '', '']:
        real_channels = ['F7','F3','P7','O1','O2','P8','F4']
    
    # check if needed channel exist
    channel_idxs=[]
    for channel in expected_channels:
        if channel in real_channels:
            channel_idxs.append(real_channels.index(channel))
        else:
            raise Exception(f"{channel} missing in real_channels: {real_channels}")
        
    # and right sampling
    if sfreq != expected_sfreq:
        raise Exception(f"{sfreq} is not the expected sampling rate of {expected_sfreq}")
    
    # --- skipping last channel
    # 4 seconds needed for cogload
    if len(glob_buffer) >= (sfreq * 4):
        start = time.perf_counter()
        data = np.array(glob_buffer[int(-sfreq*4):]).T[channel_idxs]
        
        logits = predict_cogload(data, sfreq)
        probs = softmax(logits)
        
        # pred = np.argmax(logits, axis=1)[0] # 0 for low, 1 for high probably
        # print(logits, probs, pred)
        
        end = time.perf_counter()
        
        glob_cogload = probs[0][1]
        print(f"predicted cognitive load {probs[0][1]} (1=high) in: {(end - start) * 1000:.3f} ms")
    
    # 15 seconds needed for focus
    if len(glob_buffer) >= (sfreq * 15):
        start = time.perf_counter()

        data = np.array(glob_buffer[int(-sfreq*15):]).T[channel_idxs]
        
        prob = predict_focus(data, sfreq)
        pred = prob >= 0.5
        
        end = time.perf_counter()
        
        glob_focus = prob
        print(f"predicted focus {pred} ({prob}% of it being focused) in: {(end - start) * 1000:.3f} ms")

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
def home_route():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Simple Navigation</title>
</head>
<body>
    <h1>Main Page</h1>
    <nav>
        <a href="/focus">Focus</a>
        <a href="/cogload">Cognitive Load</a>
    </nav>
    <nav>
        <a href="/focus_callibration">Focus callibration client</a>
    </nav>
</body>
</html>              
    """)
    
@app.get("/cogload")
def cogload_route():
    return render_template("cogload.html")

@app.get("/focus")
def focus_route():
    return render_template("focus.html")

@app.get("/focus_callibration")
def focus_callibration_client_route():
    global glob_focus_callibration_started
    
    return render_template("focus_callibration.html", already_started=glob_focus_callibration_started)

@app.get("/start_focus_callibration")
def focus_callibration_route_start():
    global glob_focus_callibration_started
    
    if glob_focus_callibration_started:
        return jsonify({"msg": "callibration already started"}), 400
    
    else:
        glob_focus_callibration_started = True
        print("\n\n--- starting focus callibration recording ---\n\n")
        return jsonify({"msg": "callibration started"}), 200
    
    
@app.post("/start_focus_callibration")
def focus_callibration_route_stop():
    global glob_focus_callibration_started
    
    if not glob_focus_callibration_started:
        return jsonify({"msg": "callibration not started"}), 400
    
    else:
        glob_focus_callibration_started = False
        print("\n\n--- stopping focus callibration recording ---\n\n")
        return jsonify({"msg": "callibration ended"}), 200


# --- running
if __name__ == "__main__":
    streams = list_available_lsl_streams()
    
    if not streams:
        print("No LSL streams found. Make sure your devices are connected and streaming.")
        exit()

    stream_idx = int(input("Enter the number of the stream you want to capture: ")) - 1
    stream_info = start_eeg_stream(stream_idx, handle_eeg=handle_eeg, max_rate=128)
    print("\n\n--- info about stream ---")
    print(stream_info)
    print("-------------------------\n\n")
  
    # real_channels = stream_info["ch_names"]
    # real_sfreq = stream_info["sfreq"]
    
    # for channel in expected_channels:
    #     if channel not in real_channels:
    #         stream_info['stop_flag'].set()
    #         raise Exception(f"{channel} is missing in real channels: {str(real_channels)}")
    
    # if real_sfreq != expected_sfreq:
    #     stream_info['stop_flag'].set()
    #     raise Exception(f"{str(real_sfreq)} is not as expected")
    
    print("starting webserver")
    app.run(host="127.0.0.1", port=8080, debug=False)
    
    print("flask exited, closing stream")
    stream_info['stop_flag'].set()