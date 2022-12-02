import csv
import streamlit as st
import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import paho.mqtt.client as mqtt
import threading as th
from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh
from csv import writer
import plotly.express as px
import librosa as lib
import librosa.display

st.title("Cloud Logger - Inês Botelho - Advanced Biomedical Instrumentations Aplications")
st.markdown(':exclamation: Development of a data logger for information extracted from sound, allowing the storage and visualization of this information collected over a period of time longer than 10 minutes :alarm_clock: :exclamation:')
st.markdown('''Clicking in the checkbox "Start Micophone Recording :microphone:" it will send a request to the computer running the PC.py file, to record an audio.
Then this page will receive the information (5s after sending the request) and will show 2 options to show 2 types of graphs (RMS Graph and Sonogram Graph)
Clicking in the button "Sava Data as CSV File :inbox_tray:" it will save a CSV in your computer with 3 columns (RMS, Time and Sonogram) in wich each line corresponds
to an adquired audio''')


## Graph with the diagram function of this program
st_autorefresh(interval=5000)  

st.graphviz_chart('''
    digraph {
        subgraph {
        Microphone -> Computer
        Computer -> MQTT_Data [color=blue, style=dotted, shape=box]
        MQTT_Data -> Gitpod [color=blue, style=dotted]
        MQTT_Request -> Computer [color=blue, style=dotted]
        Gitpod -> MQTT_Request [color=blue, style=dotted]        
        MQTT_Request  [shape=box]
        MQTT_Data  [shape=box]
        rank = same; MQTT_Request; MQTT_Data;
        }
    }
''')
st.caption('Diagram representing how this program functions')


#MQTT Thread Function
def MQTT_TH(client):   
    def on_connect(client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.        
        client.subscribe("inesbotelho/data")
 
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        #when data is received we can plot the graphs 
        st.session_state['plot'] = True
        #get the data from the msg.playload and get it the initial type
        data = json.loads(msg.payload)
        #in one dataframe we have the RMS and the corresponded Time, its set to a session_state variable
        data1 = {'RMS': data[0],'Times': data[1]}
        df = pd.DataFrame(data1)
        st.session_state['current_data1'] = df   
        #Another session_state variable has the chronogram
        st.session_state['current_data2'] = data[2]     
    
    #dataframe_final it's a pandas DataFrame that will be used to save in the CSV file, in here we create the collumns it will have and set to a session variable
    dataframe_final = pd.DataFrame(columns = ['RMS', 'Times','STFT'])
    st.session_state['dataframe_final'] = dataframe_final
    #Session_state Variable that will be used to only plot when data is receveid
    st.session_state['plot'] = False
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mqtt.eclipseprojects.io", 1883, 60)
    client.loop_forever()

if 'mqttThread' not in st.session_state:
    st.session_state.mqttClient = mqtt.Client()
    st.session_state.mqttThread = th.Thread(target=MQTT_TH, args=[st.session_state.mqttClient])
    add_script_run_ctx(st.session_state.mqttThread)
    st.session_state.mqttThread.start()

# CheckBox to Start Voice Recording (send request of data acquisition and then receive it(
if st.checkbox('Start Voice Recording :microphone:'):
    st.session_state.mqttClient.publish("inesbotelho/request", payload="start")    
    #it will only plot after receive the data
    if(st.session_state['plot']):
        # receive the last data (RMS and Times)
        df1 = st.session_state['current_data1']
        
        if st.checkbox('Show RMS Graph :sparkles:'):
            st.line_chart(data = df1, x="Times", y="RMS")  
            st.caption('RMS of the last recorded sound, along the time')

        
        # convert it again to list do add to the final dataframe
        rms = df1['RMS'].tolist()
        times = df1['Times'].tolist()
        df2 = st.session_state['current_data2']
        
        if st.checkbox('Show Sonogram Graph :sparkles:'):        
            # to plot the SFTF
            fig, ax = plt.subplots()
            fig2, ax2 = plt.subplots()
            df2 = list(df2)
            df2 = np.array(df2)
            abso = np.abs(df2)
            D = librosa.amplitude_to_db(df2)**2
            img = librosa.display.specshow(librosa.amplitude_to_db(D), y_axis='log', x_axis='time', ax=ax)
            img2 = lib.display.specshow(df2, y_axis='chroma', x_axis='time')
            fig.colorbar(img, ax=ax, format="%+2.f dB")
            fig2.colorbar(img2, ax=ax2, format="%+2.f dB")
            st.container().pyplot(fig)
            st.caption('Intensity of a slot of frequencies of the last recorded sound, along the time')
            st.container().pyplot(fig2)
            st.caption('Intensity of each pich of the last recorded sound, along the time')


        # add to the final dataframe the current RMS, Times and STFT
        dataframe_final = st.session_state['dataframe_final']
        dataframe_final = dataframe_final.append({'RMS' : rms, 'Times' : times, 'STFT': df2}, ignore_index = True)
        st.session_state['dataframe_final'] = dataframe_final

else:
     # if checkbox is no longer selected we want to set the session_state variable plot to False
     st.session_state['plot'] = False



## Convert dataframe to csv and save it when button "Download data as CSV" is pressed, it will have the name "data.csv"
dataframe_final = st.session_state['dataframe_final']
csv = dataframe_final.to_csv().encode('utf-8')
st.download_button(
    label="Download Data as CSV :inbox_tray:",
    data=csv,
    file_name='data.csv',
    mime='text/csv',
)

