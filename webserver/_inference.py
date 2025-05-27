from torcheeg import transforms
import onnxruntime as ort
import numpy as np
from scipy.signal import windows
import joblib
import os


# --- cogload model
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


def predict_cogload(raw_data:np.ndarray, sfreq=128):
    """
    expects 4s raw array chunk with 7 channels on 128 sampling frequency - shape: (14, 512)
    """
    
    input_data = offline_transform(eeg=raw_data)["eeg"]
    input_data = np.array([input_data], dtype=np.float32) 

    onnx_outputs = session.run([output_name], {input_name: input_data})
    probs = onnx_outputs[0]
    return probs


# --- focus model
svm_path = "./svm_0.pkl"    # focus vs rest
scaler_path = "./scaler.pkl"


if not os.path.exists(svm_path):
    raise FileNotFoundError("need /webserver/svm_0.pkl file with model")

if not os.path.exists(scaler_path):
    raise FileNotFoundError("need /webserver/scaler.pkl file with model")
        
clf = joblib.load(svm_path)
scaler = joblib.load(scaler_path)

def predict_focus(raw_data: np.ndarray, sfreq=128):
    """
    expects 15s raw array chunk with 7 channels on 128 sampling frequency - shape: (14, 1920)
    """
    
    # --- CLAUDE rewrite of MNE implementation from train_focus.ipynb
    window_length = 15  # seconds
    step_size = 1  # second
    
    # Convert to samples
    window_samples = int(window_length * sfreq)
    step_samples = int(step_size * sfreq)
    
    # Create Blackman window
    blackman_window = windows.blackman(window_samples)
    
    # Calculate number of windows
    n_windows = (raw_data.shape[1] - window_samples) // step_samples + 1
    
    # Prepare for STFT
    n_channels = raw_data.shape[0]
    n_fft = 1024
    
    # Initialize spectrogram array
    spectrograms = np.zeros((n_channels, n_windows, n_fft//2 + 1))
    
    # Calculate STFT for each channel
    for ch_idx in range(n_channels):
        for win_idx in range(n_windows):
            # Extract window
            start_idx = win_idx * step_samples
            end_idx = start_idx + window_samples
            window_data = raw_data[ch_idx, start_idx:end_idx]
            
            # Apply Blackman window
            windowed_data = window_data * blackman_window
            
            # Calculate FFT
            fft_result = np.fft.rfft(windowed_data, n=n_fft)
            
            # Calculate power spectrum
            power_spectrum = np.abs(fft_result)**2
            
            # Store in spectrogram
            spectrograms[ch_idx, win_idx, :] = power_spectrum
    
    # Calculate frequency bins
    freqs = np.fft.rfftfreq(n_fft, d=1/sfreq)
    
    # Bin into 0.5 Hz bands (from 0 to 18 Hz)
    bin_size = 0.5
    max_freq = 18.0
    n_bins = int(max_freq / bin_size)
    
    binned_spectrograms = np.zeros((n_channels, n_windows, n_bins))
    
    # Fixed binning approach
    for ch_idx in range(n_channels):
        for win_idx in range(n_windows):
            for bin_idx in range(n_bins):
                freq_start = bin_idx * bin_size
                freq_end = (bin_idx + 1) * bin_size
                
                # Find indices of frequencies in this bin
                bin_indices = np.where((freqs >= freq_start) & (freqs < freq_end))[0]
                
                if len(bin_indices) > 0:
                    # Average power in this frequency bin
                    binned_spectrograms[ch_idx, win_idx, bin_idx] = np.mean(
                        spectrograms[ch_idx, win_idx, bin_indices])
    
    # Apply 15-second running average for temporal smoothing
    smooth_window = 15  # in steps (since each step is 1 second)
    smoothed_spectrograms = np.zeros_like(binned_spectrograms)
    
    # FIX: Skip smoothing if we don't have enough windows
    if n_windows < smooth_window:
        # Just copy the data without smoothing
        smoothed_spectrograms = binned_spectrograms.copy()
    else:
        # Original smoothing code
        for ch_idx in range(n_channels):
            for freq_idx in range(n_bins):
                # Use convolution for running average
                kernel = np.ones(smooth_window) / smooth_window
                smoothed_spectrograms[ch_idx, :, freq_idx] = np.convolve(
                    binned_spectrograms[ch_idx, :, freq_idx], kernel, mode='same')
    
    # Convert to decibels
    # Add small constant to avoid log(0)
    db_spectrograms = 10 * np.log10(smoothed_spectrograms + 1e-10)
    
    # Create feature vectors
    n_features = n_channels * n_bins
    features = np.zeros((n_windows, n_features))
    
    for win_idx in range(n_windows):
        # Flatten the spectrograms for this time point
        features[win_idx, :] = db_spectrograms[:, win_idx, :].flatten()
    
    # --- Prediction part
    # print(f"Raw data shape: {raw_data.shape}")
    # print(f"Features shape: {features.shape}")
    
    # Assuming scaler and clf are defined elsewhere
    scaled = scaler.transform(features)
    # print(f"Scaled features shape: {scaled.shape}")
    
    probs = clf.predict_proba(scaled)[0][1]  # 1 represents focused [:, 1]
    # print(f"Probabilities shape: {probs.shape}")
    
    return probs
