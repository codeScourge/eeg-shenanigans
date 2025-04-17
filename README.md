# eeg-shenanigans

[![Open DREAMER In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_dreamer.ipynb)
[![Open STEW In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_stew.ipynb)




### dependencies (adjust based on whether you have cuda or not)
uv add numpy==1.26.4 torch==2.3.0 torchvision torchaudio
uv add torch-scatter -f https://data.pyg.org/whl/torch-2.3.0+cpu.html 
uv add torcheeg pytorch-lightning


### TODO or done
https://onnxruntime.ai/docs/get-started/with-python.html
- whitepaper onnx
- in ipynb get the last checkpoint (os.listdir and startswith) then convert to onnx (moving because we need dummy data and its stupid to not do it there)
- load onnx in some runtime and do inference

frontend
- websocket connection
- phaser.js basic stuff
- plan game design
- code, code, code

https://github.com/Emotiv
- set up connection
- do I need a license?