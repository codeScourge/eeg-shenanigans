# --- 1. simulate board
from pylsl import StreamInfo, StreamOutlet
import numpy as np
import time

# Create stream with full metadata
info = StreamInfo(
    name='CustomEEG',                # ✅ Custom name
    type='EEG',                      # ✅ Custom type
    channel_count=8,                 # ✅ Custom channel count
    nominal_srate=128,               # ✅ Custom sampling rate
    channel_format='float32',        # ✅ Custom format
    source_id='myuid123'             # ✅ Custom ID
)

# Add detailed channel information
channels = info.desc().append_child("channels")
channel_names = ['F7', 'F3', 'P7', 'O1', 'O2', 'P8', 'F4', 'A1']    # A1 is NOT used
channel_types = ['EEG', 'EEG', 'EEG', 'EEG', 'EEG', 'EEG', 'EEG', 'Other']
channel_units = ['microvolts'] * 8

for i, (name, type, unit) in enumerate(zip(channel_names, channel_types, channel_units)):
    ch = channels.append_child("channel")
    ch.append_child_value("label", name)      # ✅ Custom channel name
    ch.append_child_value("type", type)       # ✅ Custom channel type
    ch.append_child_value("unit", unit)       # ✅ Custom channel unit
    ch.append_child_value("index", str(i))    # ✅ Custom metadata

# Add experiment metadata
info.desc().append_child("experiment").append_child_value("id", "test-01")  # ✅ Custom metadata

# Create outlet
outlet = StreamOutlet(info)

# Stream data
while True:
    # Generate random data
    sample = np.random.randn(8)
    outlet.push_sample(sample)
    time.sleep(1/128)  # 128 Hz



# --- reading real board and restreaming it
# f.e. change brainaccess to right frequency here
# or pick up on emotiv and simply restream
# or handle whole openbci connection