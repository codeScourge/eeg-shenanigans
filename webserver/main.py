from flask import Flask, jsonify, render_template, render_template_string, request
import dotenv
import time
from _models import predict_cogload, predict_focus
from lsl_read import list_available_lsl_streams, start_eeg_stream
import numpy as np
from _helpers import softmax, find_closest_timestamp_index
from scipy import signal
import os


# --- envs
dotenv.load_dotenv()

# --- main handling function
started = time.time()

expected_channels = ['F7','F3','P7','O1','O2','P8','F4']
expected_sfreq = 128  

glob_buffer = []
glob_timestamps = []
glob_channel_idxs = []
glob_sfreq = 128




# --- callibration shit
def handle_focus_calibration(buffer:list, timestamps:list, sfreq:float, channel_idxs:list, start_callibration_timestamp:float):
    """
    expects an already downsampled buffer with at least 86 seconds filled of expected_sfreq - channel_idxs to identify what is where
    """
    
    # 0-3s pause
    # 3-43s focused
    # 43-46s pause
    # 46-86s unfocused
    start_index = find_closest_timestamp_index(timestamps, start_callibration_timestamp)
    f_start = start_index + (3*sfreq)
    f_end = start_index + (43*sfreq)
    u_start = start_index + (46*sfreq)
    u_end = start_index + (86*sfreq)
    
    focused_buffer = np.array(buffer[f_start:f_end]).T[channel_idxs]
    unfocused_buffer = np.array(buffer[u_start:u_end]).T[channel_idxs]
    
    print("\n\n--- imagine we just finetune ---\n\n") # TODO finetune 
    np.save("./datasets/focused.npy", focused_buffer)
    np.save("./datasets/unfocused.npy", unfocused_buffer)
    print(f"saving shapes: {focused_buffer.shape}, {unfocused_buffer.shape}")
    
    



# --- downsampling shit
minimum_displayed_freq = 0.5    # in Hz
minimum_length_for_downsampling = 10 * (1 / minimum_displayed_freq)    # 20 seconds, has to be multiplied by the frequency to get the actual time steps
    
def down_sample_if_needed(input_buffer, source_sfreq, target_sfreq, timestamps=None):
    """
    needs certain length and must be higher than target sfreq
    
    """

    if source_sfreq < target_sfreq:
        raise Exception(f"{source_sfreq} is smaller than target sfreq of {target_sfreq}")
    
    
    # no need if same
    if source_sfreq == target_sfreq:
        return input_buffer, timestamps
    
    
    # check if minimum length on nyqiom theorem has been reached
    if len(input_buffer) >= (minimum_length_for_downsampling * source_sfreq):
        downsampled_buffer = down_sample(input_buffer, source_sfreq, target_sfreq)
        
        # -- downsample timestamps simply by skipping (TODO: could pool them)
        downsample_factor = source_sfreq / target_sfreq
        indices_to_keep = []
        for i in range(int(len(timestamps) / downsample_factor)):
            idx = int(i * downsample_factor)
            if idx < len(timestamps):
                indices_to_keep.append(idx)
        downsampled_timestamps = [timestamps[i] for i in indices_to_keep]
        
        return downsampled_buffer, downsampled_timestamps
    
    else:
        print(f"{len(glob_buffer) / glob_sfreq} seconds too short for downsample, skipping...")
        return None


def down_sample(buffer, source_sfreq:float, target_sfreq:float):
    """
    takes:
    - buffer of shape (n_channels, n_samples) - n_samples has to be at least minimum_length_for_downsampling (otherwise not accurate, or might even throw error because impossible)
    - source_sfreq - lower than the target_sfeq defined in "expected_sfreq" global variable
    """
    
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


# --- main handling function, passed to subthread
def handle_eeg(sample, timestamp):
    """
    only called when sample is not None
    timestamp is in unix time
    """
    
    global glob_buffer, glob_sfreq, glob_timestamps
    
    # print(timestamp)
    
    # --- constantly append to buffer global variable (sliding window)
    glob_buffer.append(sample)
    glob_timestamps.append(timestamp)

    max_buffer_length = 180 # in seconds
    if len(glob_buffer) > (glob_sfreq * max_buffer_length):
        glob_buffer[:] = glob_buffer[-(int(glob_sfreq * max_buffer_length)):]
        glob_timestamps[:] = glob_timestamps[-(int(glob_sfreq * max_buffer_length)):]


# --- init
app = Flask(__name__)


        
# --- routes
@app.get("/data")
def dataRoute():
    global glob_buffer, glob_channel_idxs, glob_sfreq
    
    if len(glob_buffer) < glob_sfreq*15:
        print("--not long enough for inference inference--")
        return jsonify({
            "cogload": str(0),
            "focus": str(0)
        })
    
    
    buffer, _ = down_sample_if_needed(glob_buffer, glob_sfreq, expected_sfreq)
    if buffer == None:
        print("--not long enough for downsampling--")
        return jsonify({
            "cogload": str(0),
            "focus": str(0)
        })
    
    # --- needs 15 seconds
    start = time.perf_counter()

    data = np.array(buffer[int(-expected_sfreq*15):]).T[glob_channel_idxs]
    
    prob = predict_focus(data, expected_sfreq)
    pred = prob >= 0.5
    
    focus = prob
    
    end = time.perf_counter()
    # print(f"predicted focus {pred} ({prob}% of it being focused) in: {(end - start) * 1000:.3f} ms")
        
    # --- needs 4 seconds
    start = time.perf_counter()
    data = np.array(buffer[int(-expected_sfreq*4):]).T[glob_channel_idxs]
    
    logits = predict_cogload(data, expected_sfreq)
    probs = softmax(logits)
    
    cogload = probs[0][1]
    
    end = time.perf_counter()
    # print(f"predicted cognitive load {probs[0][1]} (1=high) in: {(end - start) * 1000:.3f} ms")
    
    return jsonify({
        "cogload": str(cogload), # between 0 and 1 (corresponds to 100% and 200% video speed)
        "focus": str(focus) # between 0 and 1 (corresponds to completely drowsy vs full focus)
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
        <a href="/focus_calibration">Focus callibration client</a>
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

@app.route("/focus_calibration", methods=["GET", "POST"])
def focus_calibration_client_route():
    
    if request.method == "GET":
        return render_template("focus_callibration.html")
    
    
    # this is the POST endpoint to callibrate
    # we receive the timestamp of when the callibration happened on the frontend (in unix time)
    # and have to match it to the right chunk inside our buffer
    global glob_buffer, glob_timestamps, glob_sfreq, glob_channel_idxs, expected_sfreq
    print("received calibration request")
    
    data = request.get_json()
    start_callibration_timestamp = data["calibration_start"]
    time.sleep(5)
    
    if (len(glob_buffer) >= int(glob_sfreq * 86)):  
        buffer, timestamps = down_sample_if_needed(glob_buffer, glob_sfreq, expected_sfreq, glob_timestamps)
        handle_focus_calibration(buffer, timestamps, expected_sfreq, glob_channel_idxs, start_callibration_timestamp)
        return {"msg": "succesfully calibrated"}, 200

    else:
        return {"msg": "motherfucker is too short"}, 500
        
        
        



# --- running
if __name__ == "__main__":
    streams = list_available_lsl_streams()
    
    if not streams:
        print("No LSL streams found. Make sure your devices are connected and streaming.")
        exit()

    stream_idx = int(input("Enter the number of the stream you want to capture: ")) - 1
    stream_info = start_eeg_stream(stream_idx, handle_eeg=handle_eeg, max_rate=128)
    
    
    # --
    glob_sfreq = stream_info["sfreq"]
    ch_names = stream_info["ch_names"]
    
    if ch_names == ['', '', '', '', '', '', '', '']:
        ch_names = ['F7','F3','P7','O1','O2','P8','F4']
    
    # check if all expected channels exist (we can have more than needed, no problem - will be filtered out by the use of indexes)
    for channel in expected_channels:
        if channel in ch_names:
            glob_channel_idxs.append(ch_names.index(channel))
        else:
            raise Exception(f"{channel} missing in real_channels: {ch_names}")
    # --
    
    
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
    
    print("flask exited, closing stream connection")
    stream_info['stop_flag'].set()