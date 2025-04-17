# --- data processing stuff
from torcheeg import transforms
from torcheeg.datasets.constants import DREAMER_CHANNEL_LOCATION_DICT


def preprocess_data(raw_data):
    """
    Process raw EEG data for ONNX inference using the same pipeline as training.
    
    Args:
        raw_data: Raw EEG data in the format expected by your transforms
        
    Returns:
        numpy.ndarray: Processed data ready for ONNX model inference
    """
    # Apply only the necessary transforms
    transform = transforms.Compose([
        transforms.BaselineRemoval(),
        transforms.Concatenate([
            transforms.Compose([
                transforms.BandDifferentialEntropy(sampling_rate=128),
                transforms.MeanStdNormalize()
            ]),
            transforms.Compose([
                transforms.Downsample(num_points=32),
                transforms.MinMaxNormalize()
            ])
        ]),
        transforms.ToInterpolatedGrid(DREAMER_CHANNEL_LOCATION_DICT),
        transforms.Resize((16, 16))
    ])
    
    # Process the data
    processed_data = transform(raw_data)
    
    # Ensure it's a numpy array
    if not isinstance(processed_data, np.ndarray):
        processed_data = np.array(processed_data)
    
    return processed_data



# --- loading model and providing calls
import onnxruntime as ort
import numpy as np

onnx_path = "models/sst_00.onnx"

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


def predict(input_data):
    onnx_outputs = session.run([output_name], {input_name: input_data})
    probabilities = onnx_outputs[0]
    predicted_classes = np.argmax(probabilities, axis=1)
    return predicted_classes