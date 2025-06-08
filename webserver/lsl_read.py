import numpy as np
from pylsl import StreamInlet, resolve_streams
import time
import threading


def list_available_lsl_streams():
    """List all available LSL streams on the network"""
    streams = resolve_streams()
    print(f"Found {len(streams)} LSL streams:")
    for i, stream in enumerate(streams):
        print(f"{i+1}. Name: {stream.name()}, Type: {stream.type()}, Channels: {stream.channel_count()}, Rate: {stream.nominal_srate()} Hz")
    return streams

def start_eeg_stream(stream_index, handle_eeg=None, max_rate=128):
    
    # -- finding stream
    all_streams = resolve_streams()
    if stream_index < len(all_streams):
        streams = [all_streams[stream_index]]
    else:
        raise ValueError(f"Stream index {stream_index} out of range")
    
    if not streams:
        raise RuntimeError(f"No stream found with specified criteria")
    
    
    # -- handling
    inlet = StreamInlet(streams[0])
    info = inlet.info()
    sfreq = info.nominal_srate()
    ch_count = info.channel_count()
    ch_names = []
    ch_types = []
    ch_units = []

    ch = info.desc().child("channels").child("channel")
    for i in range(ch_count):
        ch_names.append(ch.child_value("label"))
        ch_types.append(ch.child_value("type"))
        ch_units.append(ch.child_value("unit"))
        ch = ch.next_sibling()
        
    print(f"Streaming from '{info.name()}' with {ch_count} channels at {sfreq} Hz")
    
    stop_flag = threading.Event()
    
    result = {
        'stop_flag': stop_flag,
        'ch_names': ch_names,
        'sfreq': sfreq,
    }
    

    def streaming_thread():
        # Calculate time between samples to limit to max_rate
        # min_time_between_samples = 1.0 / max_rate
        # last_sample_time = time.time()
        
        # while not stop_flag.is_set():
        #     current_time = time.time()
        #     elapsed = current_time - last_sample_time
            
        #     # only sample (from lsl) at a max freq of provided max_rate (which in theory should be the same as our headset sfreq)
        #     if elapsed >= min_time_between_samples:
        #         sample, timestamp = inlet.pull_sample(timeout=0.0)
                
        #         if sample and handle_eeg:
        #             handle_eeg(sample, sfreq, ch_names)
        #             last_sample_time = current_time
        #     else:
        #         # Sleep a bit to avoid consuming too much CPU
        #         time.sleep(0.001)
               
        while not stop_flag.is_set():
            sample, timestamp = inlet.pull_sample(timeout=0.0)
            if sample:
                handle_eeg(sample)
            time.sleep(0.001)
    
  
    thread = threading.Thread(target=streaming_thread)
    thread.daemon = True
    thread.start()
    return result

# Simple test if run directly
if __name__ == "__main__":
    streams = list_available_lsl_streams()
    
    if streams:
        def test_handler(buffer, sfreq, real_channels):
            print(f"streamed at {sfreq} for {real_channels}, Buffer size: {len(buffer)} samples")
        
        stream_idx = int(input("Enter stream number: ")) - 1
        stream_info = start_eeg_stream(stream_index=stream_idx, handle_eeg=test_handler)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stream_info['stop_flag'].set()
            print("Stopped streaming")
    else:
        print("No LSL streams found")
