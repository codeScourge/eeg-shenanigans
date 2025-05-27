# eeg-shenanigans






### dependencies (adjust based on whether you have cuda or not)
uv add numpy==1.26.4 torch==2.3.0 torchvision torchaudio
uv add torch-scatter -f https://data.pyg.org/whl/torch-2.3.0+cpu.html 
uv add torcheeg pytorch-lightning

# models
emotions using DREAEMER: [![Open STEW In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_dreamer.ipynb)
- idk

---

cogload using STEW: [![Open STEW In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_stew.ipynb)
- idk
- 7ch intra-subject only: 50min, 97% train 78% val, 79% test
- 7ch extra-subject I think: 30min, 92% train, 77% val, 76% test

---

focus: [![Open STEW In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/codeScourge/eeg-shenanigans/blob/main/train_focus.ipynb)
- 80% focused, 58% whole

### setup
- add a `test.mp4` file into the `./webserver/static/videos` folder
- run `run.sh`



