import paho.mqtt.client as mqtt
import threading as th
import sounddevice as sd
from scipy.io.wavfile import write
import librosa as lib

fs = 44100 #sampling frequency, will be a parameter in the function responsible for recording the audio
second = 4 #defines the duration of the recorded audio

#MQTT Thread Function

def get_data():
    record_voice = sd.rec( int( second * fs ) , samplerate = fs , channels = 2 )
    sd.wait() # wait for the recording of the audio to continue with the script
    write("som.wav", fs , record_voice )
    x, sr = lib.load("som.wav") 
    pm = lib.feature.rms(y=x) #Compute root-mean-square (RMS) value for each frame
    times = lib.times_like(pm) #Getting the array with the timesteps
    stft = lib.feature.chroma_stft(y=x, sr=fs #Chromagram
    pm2 = pm[0]   #Because it has a array inside an array
    pm2 = pm2.tolist()     #pass to a list
    times = times.tolist() #pass to a list
    stft = stft.tolist()   #pass to a list
    data = [pm2, times, stft] #pass to a variable (it will contain a list with 3 positions, each one with a list inside)
    data = str(data) #converting to string to be sent via client.publish   
    return data

def MQTT_TH(client):    
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc)) 
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("inesbotelho/request") #subscrive to the request of adquiring the data
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))   # when the message is "start" it means that came from "inesbotelho/request" and is needed to send the data
        data = get_data() # get the data from the function
        client.publish("inesbotelho/data", data)

    print('Incializing MQTT')
    client.on_connect = on_connect
    client.on_message = on_message
  
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
   
    client.loop_forever()

t = th.Thread(target=MQTT_TH, args=[mqtt.Client()])
t.start()
