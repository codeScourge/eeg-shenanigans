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

def start_eeg_stream(stream_name=None, stream_index=None, handle_eeg=None, max_rate=128):
    """
    Start streaming EEG data and process it with handle_eeg function
    
    Parameters:
    -----------
    stream_name : str or None
        Name of the LSL stream to capture
    stream_index : int or None
        Index of the LSL stream to capture (from list_available_lsl_streams)
    handle_eeg : function
        Function to process the EEG buffer when new data arrives
    max_rate : float
        Maximum rate to process data (Hz)
    
    Returns:
    --------
    dict : A dictionary containing:
        - 'stop_flag': threading Event to stop the streaming
        - 'ch_names': list of channel names
        - 'sfreq': sampling frequency
        - 'buffer': list to store EEG samples
    """
    # Find the stream
    if stream_name:
        print(f"Looking for stream named '{stream_name}'...")
        streams = resolve_stream('name', stream_name)
    elif stream_index is not None:
        all_streams = resolve_streams()
        if stream_index < len(all_streams):
            streams = [all_streams[stream_index]]
        else:
            raise ValueError(f"Stream index {stream_index} out of range")
    else:
        raise ValueError("Must provide either stream_name or stream_index")
    
    if not streams:
        raise RuntimeError(f"No stream found with specified criteria")
    
    # Create inlet
    inlet = StreamInlet(streams[0])
    
    # Get stream info
    info = inlet.info()
    sfreq = info.nominal_srate()
    ch_count = info.channel_count()
    
    # Try to get channel names from stream info
    try:
        ch_names = [info.desc().child("channels").child("channel", i).child_value("label") 
                    for i in range(ch_count)]
    except:
        # If channel names not available, create generic names
        ch_names = [f'Ch{i+1}' for i in range(ch_count)]
    
    print(f"Streaming from '{info.name()}' with {ch_count} channels at {sfreq} Hz")
    
    # Create a buffer to store samples
    buffer = []
    
    # Create a stop flag for the thread
    stop_flag = threading.Event()
    
    # Create a result dictionary to return
    result = {
        'stop_flag': stop_flag,
        'ch_names': ch_names,
        'sfreq': sfreq,
        'buffer': buffer
    }
    
    # Function to run in a thread
    def streaming_thread():
        # Calculate time between samples to limit to max_rate
        min_time_between_samples = 1.0 / max_rate
        last_sample_time = time.time()
        
        while not stop_flag.is_set():
            current_time = time.time()
            elapsed = current_time - last_sample_time
            
            # Limit sampling rate
            if elapsed >= min_time_between_samples:
                # Get a sample
                sample, timestamp = inlet.pull_sample(timeout=0.0)
                
                if sample:
                    # Append to buffer
                    buffer.append(sample)
                    
                    # Limit buffer size to prevent memory issues (keep last 30 seconds)
                    if len(buffer) > (sfreq * 30):
                        buffer[:] = buffer[-(int(sfreq * 30)):]
                    
                    # Call handle_eeg function if provided
                    if handle_eeg:
                        handle_eeg(buffer, sfreq)
                    
                    last_sample_time = current_time
            else:
                # Sleep a bit to avoid consuming too much CPU
                time.sleep(0.001)
    
    # Start the streaming thread
    thread = threading.Thread(target=streaming_thread)
    thread.daemon = True
    thread.start()
    
    return result

# Simple test if run directly
if __name__ == "__main__":
    streams = list_available_lsl_streams()
    
    if streams:
        def test_handler(buffer, sfreq):
            print(f"Buffer size: {len(buffer)} samples")
        
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
