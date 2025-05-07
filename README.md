# eeg-shenanigans






### dependencies (adjust based on whether you have cuda or not)
uv add numpy==1.26.4 torch==2.3.0 torchvision torchaudio
uv add torch-scatter -f https://data.pyg.org/whl/torch-2.3.0+cpu.html 
uv add torcheeg pytorch-lightning

### setup
- optionally create a new .onnx model using the notebook [![Open STEW In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_stew.ipynb)
- add a `test.mp4` file into the `./webserver/static/videos` folder
- run `run.sh`