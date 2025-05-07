from torcheeg import transforms
import onnxruntime as ort
import numpy as np
from mne.io import Raw
import os


# --- loading model and providing calls
onnx_path = "./inference.onnx"

if not os.path.exists(onnx_path):
    raise FileNotFoundError("need /webserver/inference.onnx file with model")

session_options = ort.SessionOptions()
session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] # fallbacks to CPU if CUDA isn't available


session = ort.InferenceSession(
    onnx_path,
    sess_options=session_options,
    providers=providers
)


input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

print("input_name: ", input_name)
print("output_name: ", output_name)


# --- preprocessing and interface

# has to match the data we give into the    
offline_transform = transforms.Compose([
    transforms.CWTSpectrum(
        wavelet='morl',
        total_scale=64,
        contourf=False
    ),
    transforms.MeanStdNormalize(),
])


def predict(raw_data:np.ndarray):
    """
    takes in raw array and does inference on the last 4 seconds following preprocessing in training
    """
    
    # expects 4s chunk with 14 channels on 128 sampling frequency - shape: (14, 512)
    input_data = offline_transform(eeg=raw_data)["eeg"]
    input_data = np.array([input_data], dtype=np.float32)  # Convert to float32
    # print(input_data.shape)
        
    # expets spectogram - shape: (batch_size, 14, 64, 19200)
    
    onnx_outputs = session.run([output_name], {input_name: input_data})
    probs = onnx_outputs[0]
    return probs

