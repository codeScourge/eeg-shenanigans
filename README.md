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
```old
- collect a 40s clip (32s train, 8s test) for each state (focused, unfocused)
- either record it on the backend in a separate object..
- ... OR: record a timestamp which you can pull from the buffer? (basically we just have to send an end-request to the backend which is precise in how many timebins the recorded started ago - means full synchronization frontend backnend OR include a time-string, but this would require the buffer to be saved with times as well)
- => the first one is easier, simply call a start signal at the same time the person is asked to focus, then after 40s*128Hz items, we end the collection and then finetune this shit
- the question is how to make the client... insipired by eyetracking being used for annotation: 
```
=> new is done using timestamp, because otherwise it is unprecise AF, this means we get the timestamp of the start in unix time in the frontend, and then after callibration is done there, we send it to an endpoint to get the last 86 seconds, since:
- 0-40s unfocused
- 40-43s pause
- 43-83s focused
- 83-86s pause
this means that all synchronization WITH USER happens on the frontend. the synchronization with the headset stream is done on the backend, using the timestamp (also unix time) provided by the lsl stream.
- we could map each chunck to a timestep, and then get the closest one to the one received and count from there
(not a big problem but:) if we leave tap, than the counter pauses, but I think we can expect the user to stay on this bitch for 80s, not that hard

##### matching clocks
the problem is, that the return of the LSL stream is not unix time, but a local device clock
- we can calculate an offset between the two (f.e take first timestep, or keep a moving average) and then append it -
- however the above would include the delay between when it was recorded and when it actually arrived on the backend - ideal would be "advanced clock synchronization" - f.e. send time since last timestamp sent so we can calculate out the

### downsampling
idk I just did