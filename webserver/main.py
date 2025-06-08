from flask import Flask, jsonify, render_template, render_template_string
import dotenv
import time
from _models import predict_cogload, predict_focus
from lsl_read import list_available_lsl_streams, start_eeg_stream
import numpy as np
from scipy import signal
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

def handle_focus_callibration(buffer, channel_idxs):
    """
    expects an already downsampled buffer with at least 80 seconds filled of expected_sfreq - channel_idxs to identify what is where
    """
    global glob_focus_callibration_started, expected_sfreq
    
    focused_buffer = np.array(buffer[int(-expected_sfreq*83):int(-expected_sfreq*43)]).T[channel_idxs]
    unfocused_buffer = np.array(buffer[int(-expected_sfreq*40):]).T[channel_idxs]
    print("\n\n--- imagine we just finetune ---\n\n") # TODO finetune 
    np.save("./datasets/focused.npy", focused_buffer)
    np.save("./datasets/unfocused.npy", unfocused_buffer)
    
    glob_focus_callibration_started = False
    
    

# - 
def softmax(x):
    exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=1, keepdims=True)

minimum_displayed_freq = 0.5    # in Hz
minimum_length_for_downsampling = 10 * (1 / minimum_displayed_freq)    # 20 seconds, has to be multiplied by the frequency to get the actual time steps

def down_sample(buffer, source_sfreq:float):
    """
    takes:
    - buffer of shape (n_channels, n_samples) - n_samples has to be at least minimum_length_for_downsampling (otherwise not accurate, or might even throw error because impossible)
    - source_sfreq - lower than the target_sfeq defined in "expected_sfreq" global variable
    """
    
    target_sfreq = expected_sfreq
    
    if source_sfreq <= target_sfreq:
        raise Exception(f"source frequency {source_sfreq} must be higher than the target frequency of {target_sfreq}")
    
    if len(buffer) <= (minimum_length_for_downsampling * source_sfreq):
        raise Exception(f"input sample length must be at least {minimum_length_for_downsampling} seconds")
    
    buffer = np.array(buffer).T
    
    start = time.perf_counter()
    
    down_factor = source_sfreq / target_sfreq
    
    nyquist = source_sfreq / 2.0  # 125 Hz
    cutoff = target_sfreq / 2.0 * 0.9  # 57.6 Hz (90% of new Nyquist)
    b, a = signal.butter(8, cutoff/nyquist, 'low')

    filtered_data = signal.filtfilt(b, a, buffer, axis=1)
    new_length = int(buffer.shape[1] / down_factor)
    
    downsampled_data = signal.resample(filtered_data, new_length, axis=1)
    
    print(f"reduced length of samples from {buffer.shape[1]} to {downsampled_data.shape[1]}")
    
    output_buffer = downsampled_data.T.tolist()
    
    end = time.perf_counter()
    # print(f"downsampled in: {(end - start) * 1000:.3f} ms")
    return output_buffer

# - passed to subthread
def handle_eeg(sample, sfreq:float, real_channels:list):
    global glob_last_inference, glob_cogload, glob_focus, glob_buffer
    global glob_focus_callibration_started
    
    # --- constantly append to buffer global variable, holding up to 180s (sliding window)
    glob_buffer.append(sample)

    if len(glob_buffer) > (sfreq * 180):
        glob_buffer[:] = glob_buffer[-(int(sfreq * 180)):]

        
        
    # --- run inference only every half second max
    if (time.time() - glob_last_inference) < 0.5:
        return
    
    glob_last_inference = time.time()
    
    
    # --- EEG channels
    # handle shitty openbci stream
    if real_channels == ['', '', '', '', '', '', '', '']:
        real_channels = ['F7','F3','P7','O1','O2','P8','F4']
    
    # check if all expected channels exist (we can have more than needed, no problem)
    channel_idxs=[]
    for channel in expected_channels:
        if channel in real_channels:
            channel_idxs.append(real_channels.index(channel))
        else:
            raise Exception(f"{channel} missing in real_channels: {real_channels}")
        
        
    # --- at this point we (if needed) downsample, means that our measurements on the (not global) buffer object need to use expected_sfreq
    if sfreq < expected_sfreq:
        raise Exception(f"{sfreq} is smaller than expected sfreq of {expected_sfreq}")
    elif sfreq > expected_sfreq:
        
        # skip if not ong enough to downsample
        if len(glob_buffer) >= (minimum_length_for_downsampling * sfreq):
            buffer = down_sample(glob_buffer, sfreq)
        else:
            print(f"{len(glob_buffer) / sfreq} seconds too short for downsample, skipping...")
            return
    else:
        buffer = glob_buffer
        
        
    # --- when finetuning: and we have reached the 80s data collection time, handle the finetuning step
    if glob_focus_callibration_started and (len(buffer) >= int(expected_sfreq * 86)):
        handle_focus_callibration(buffer, channel_idxs)
    else:
        print(glob_focus_callibration_started)
        print(len(buffer), ">", int(expected_sfreq * 86))
        
    # --- skipping last channel
    # 4 seconds needed for cogload
    if len(buffer) >= (expected_sfreq * 4):
        start = time.perf_counter()
        data = np.array(buffer[int(-expected_sfreq*4):]).T[channel_idxs]
        
        logits = predict_cogload(data, expected_sfreq)
        probs = softmax(logits)
        
        glob_cogload = probs[0][1]
        
        end = time.perf_counter()
        # print(f"predicted cognitive load {probs[0][1]} (1=high) in: {(end - start) * 1000:.3f} ms")
    
    # 15 seconds needed for focus
    if len(buffer) >= (expected_sfreq * 15):
        start = time.perf_counter()

        data = np.array(buffer[int(-expected_sfreq*15):]).T[channel_idxs]
        
        prob = predict_focus(data, expected_sfreq)
        pred = prob >= 0.5
        
        glob_focus = prob
        
        end = time.perf_counter()
        # print(f"predicted focus {pred} ({prob}% of it being focused) in: {(end - start) * 1000:.3f} ms")

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
    
    
@app.get("/stop_focus_callibration")
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