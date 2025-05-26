from flask import Flask, jsonify, render_template
import dotenv
import time
from _cortex import Cortex
from _inference import predict
import threading
import numpy as np
import os


"""
Inputs to Update:
    set EMOTIV_CLIENT_ID and EMOTIV_CLIENT_SECRET inside `.env` (!! make sure file exists !!)
    (commands not implemented) - "profile_name_load": The trained profile name from EmotivBCI
"""


# --- envs
dotenv.load_dotenv()

# --- vars & consts
def update_cogload(value):
    with open('cogload.txt', 'w') as f:
        f.write(str(value))

def get_cogload():
    try:
        with open('cogload.txt', 'r') as f:
            return float(f.read().strip())
    except:
        return 0.0

last_inference:float = time.time()  # return seconds since epoch

ch_names = ['AF3', 'F7', 'F3', 'FC5', 'T7', 'P7', 'O1', 'O2', 'P8', 'T8', 'FC6', 'F4', 'F8', 'AF4']

sampling_frequency = 128
seconds_expected = 4
clips_per_chunk = sampling_frequency * seconds_expected


buffer = [] # (x, 12)

# --- constants, globals, and secrets
loaded_profile = False  # global variable to check if profile for mental commands is loaded
COMMAND_PROFILE_NAME = "test"   # the name of the profile you set inside EMOTIV (for mental commands)


# --- subscribing (was headset.py before moving here due to global variable sharing)
class Subscribe():
    """
    A class to subscribe data stream.

    Attributes
    ----------
    c : Cortex
        Cortex communicate with Emotiv Cortex Service

    Methods
    -------
    start():
        start data subscribing process.
    sub(streams):
        To subscribe to one or more data streams.
    on_new_data_labels(*args, **kwargs):
        To handle data labels of subscribed data 
        To handle mental command emitted from Cortex
    """
    
    def __init__(self, app_client_id, app_client_secret, handle_eeg_data: callable, license:str="", **kwargs):
        """
        Constructs cortex client and bind a function to handle subscribed data streams
        If you do not want to log request and response message , set debug_mode = False. The default is True
        """
        print("Subscribe __init__")
        self.c = Cortex(app_client_id, app_client_secret, license, debug_mode=False, **kwargs)

        #associate events from Cortex with handler functions in class
        self.c.bind(create_session_done=self.on_create_session_done)
        self.c.bind(new_data_labels=self.on_new_data_labels)
        self.c.bind(new_com_data=self.on_new_com_data)
        self.c.bind(new_eeg_data=self.on_new_eeg_data)
        self.c.bind(inform_error=self.on_inform_error)
        
        # pass function here
        self.handle_eeg_data = handle_eeg_data


    def start(self, streams, headsetId=''):
        """
        To start data subscribing process as below workflow
        (1)check access right -> authorize -> connect headset->create session
        (2) subscribe streams data

        'com' : Mental Command

    
        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot']
        headsetId: string , optional
             id of wanted headet which you want to work with it.
             If the headsetId is empty, the first headset in list will be set as wanted headset
        Returns
        -------
        None
        """

        self.streams = streams

        if headsetId != '':
            self.c.set_wanted_headset(headsetId)

        self.c.open()
        
        
    def stop(self):
        self.c.close()


    def sub(self, streams):
        """
        To subscribe to one or more data streams
        'eeg': EEG
        'mot' : Motion
        'dev' : Device information
        'met' : Performance metric
        'pow' : Band power
        'com' : Mental Command

        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot', 'com']

        Returns
        -------
        None
        """
        self.c.sub_request(streams)


    def unsub(self, streams):
        """
        To unsubscribe to one or more data streams
        'eeg': EEG
        'mot' : Motion
        'dev' : Device information
        'met' : Performance metric
        'pow' : Band power

        Parameters
        ----------
        streams : list, required
            list of streams. For example, ['eeg', 'mot']

        Returns
        -------
        None
        """
        self.c.unsub_request(streams)


    def on_new_data_labels(self, *args, **kwargs):
        print("on_new_data_labels")
        """
        To handle data labels of subscribed data 
        Returns
        -------
        data: list  
              array of data labels
        name: stream name
        For example:
            eeg: ["COUNTER","INTERPOLATED", "AF3", "T7", "Pz", "T8", "AF4", "RAW_CQ", "MARKER_HARDWARE"]
            motion: ['COUNTER_MEMS', 'INTERPOLATED_MEMS', 'Q0', 'Q1', 'Q2', 'Q3', 'ACCX', 'ACCY', 'ACCZ', 'MAGX', 'MAGY', 'MAGZ']
            dev: ['AF3', 'T7', 'Pz', 'T8', 'AF4', 'OVERALL']
            met : ['eng.isActive', 'eng', 'exc.isActive', 'exc', 'lex', 'str.isActive', 'str', 'rel.isActive', 'rel', 'int.isActive', 'int', 'foc.isActive', 'foc']
            pow: ['AF3/theta', 'AF3/alpha', 'AF3/betaL', 'AF3/betaH', 'AF3/gamma', 'T7/theta', 'T7/alpha', 'T7/betaL', 'T7/betaH', 'T7/gamma', 'Pz/theta', 'Pz/alpha', 'Pz/betaL', 'Pz/betaH', 'Pz/gamma', 'T8/theta', 'T8/alpha', 'T8/betaL', 'T8/betaH', 'T8/gamma', 'AF4/theta', 'AF4/alpha', 'AF4/betaL', 'AF4/betaH', 'AF4/gamma']
        """
        
        
        data = kwargs.get('data')
        print(data)
        # stream_name = data['streamName']
        # stream_labels = data['labels']
        # print('{} labels are : {}'.format(stream_name, stream_labels))


    def on_new_com_data(self, *args, **kwargs):
        global loaded_profile
        """
        To handle mental command data emitted from Cortex

        Returns
        -------
        data: dictionary
             The values in the array pow match the labels in the array labels return at on_new_com_data_labels
        """


        if loaded_profile == False:
            status_load = "load"
            profile_name_load = COMMAND_PROFILE_NAME
            self.profile_name = profile_name_load
            self.c.set_wanted_profile(profile_name_load)
            self.c.setup_profile(profile_name_load, status_load)
            loaded_profile = True
            

        #handling pushing of cube
        actions = ['push'] 
        self.c.set_mental_command_active_action(actions)
        data = kwargs.get('data')

        action = data.get('action') 
        power = data.get('power')
        time = data.get('time')

        print(f'Command Data - Action: {action}, Power: {power}, Time: {time}')

        if action == 'push' and power > 0.6: print("user thought about pushing cube with a certain strength")


    def on_new_eeg_data(self, *args, **kwargs):
        eeg_data = kwargs.get('data')
        self.handle_eeg_data(eeg_data)

    # callbacks functions
    def on_create_session_done(self, *args, **kwargs):
        print('on_create_session_done')
        self.sub(self.streams)


    def on_inform_error(self, *args, **kwargs):
        error_data = kwargs.get('error_data')
        raise Exception(error_data)
        
        
        
# --- interfaces
def run_emotiv(client_id:str, client_secret:str, handle_eeg_data:callable, license:str=""):
    s = Subscribe(client_id, client_secret, handle_eeg_data, license)
    streams = [
        'eeg',  # raw data
        # 'com'   # mental commands
    ]    
    
    thread = threading.Thread(target=s.start, args=(streams,))
    thread.daemon = True  # Will exit when main thread exits
    thread.start()
    
    return s


def stop_emotiv(s:Subscribe):
    s.stop()

    

# --- handlers
def handle_eeg_data(eeg_data):
    global last_inference
    
    if eeg_data:
        # print(f"EEG Data: {eeg_data}")
        # print(f"Timestamp: {eeg_data['time']}")
        # print(f"Values: {eeg_data['eeg']}")
        
        
        # ["COUNTER","INTERPOLATED", ..., "RAW_CQ", "MARKER_HARDWARE"]
        values = eeg_data['eeg']
        values = values[2:-2]
        
        if len(values) == len(ch_names):
            buffer.append(values)
            
            # check if we have enough data for inference AND at least half a seconds since last inference
            if (len(buffer) >= (clips_per_chunk)) and ((time.time() - last_inference) >= 0.5):
                last_inference = time.time()
                
                start = time.perf_counter()

                data = np.array(buffer[-clips_per_chunk:]).T
                probs = predict(data)
                pred = np.argmax(probs, axis=1) # 0 for low, 1 for high probably
                
                end = time.perf_counter()
                confidence = probs[0][pred[0]]
                
                update_cogload(confidence)
                print(f"predicted {pred[0]} at {confidence}% in: {(end - start) * 1000:.3f} ms")
                
        else:
            raise ValueError("channels from stream doesn't match channel expected")
                

# --- init
app = Flask(__name__)


s = run_emotiv(
    client_id = os.getenv("EMOTIV_CLIENT_ID"),
    client_secret = os.getenv("EMOTIV_CLIENT_SECRET"),
    handle_eeg_data=handle_eeg_data,
    license = os.getenv("EMOTIV_LICENSE")
) 




@app.teardown_appcontext
def cleanup_resources(exception=None):
    stop_emotiv(s)

# --- routes
@app.get("/data")
def dataRoute():
    value = get_cogload()
    return jsonify({
        "cogload": str(value)
    })
    
@app.get("/")
def mainRoute():
    return render_template("main.html")
    

# --- running
if __name__ == "__main__":
    print("starting webserver")
    app.run(port=8080, debug=True)

