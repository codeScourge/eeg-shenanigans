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

### finetuning
- the client is going to run on PC (because I don't have the integration to the headset on colab)
- it will for now create a new model file, which inference will prefer over the normal one - this means you have to restart the webapp if you want to use the new one
- for now it will simply overwrite the old finetuned model each time

we need to:
- collect a 40s clip (32s train, 8s test) for each state (focused, unfocused)
- either record it on the backend in a separate object..
- ... OR: record a timestamp which you can pull from the buffer? (basically we just have to send an end-request to the backend which is precise in how many timebins the recorded started ago - means full synchronization frontend backnend OR include a time-string, but this would require the buffer to be saved with times as well)
- => the first one is easier, simply call a start signal at the same time the person is asked to focus, then after 40s*128Hz items, we end the collection and then finetune this shit
- the question is how to make the client... insipired by eyetracking being used for annotation: 
```prompt
I need an interface for building an EEG dataset. basically I try to to first make the user focus hard (by having him follow a flying circle on screen?) and then be unfocused (by showing a blurred focused?)

---

can you write me the html, css, js files for that? (filename for all should be focus_callibration)
```

