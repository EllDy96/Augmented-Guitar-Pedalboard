 

#from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import os

##################### OSC libraries #########################
import argparse #to properly understand incoming OSC messages 
from pythonosc import dispatcher # allow us to catch and map input from osc 
from pythonosc import osc_server # to create osc messages 
from pythonosc import osc_message_builder #to create adress-value massages 
from pythonosc import udp_client# allow us to listen from messages 
from pythonosc.osc_server import ThreadingOSCUDPServer

'''RMS Signal'''
if os.path.isfile('signal_bicep_Dx_rms_normalized.npy'):
    signal_bicep_Dx_rms_normalized= np.load('signal_bicep_Dx_rms_normalized.npy', allow_pickle=True)
    print('array already exist')
 
else:
    file_rms = "C:\\Users\david\OneDrive - Politecnico di Milano\Il_mio_mondo\Corsi Università\Magistrale\Tesi\LWT3\\firstPrototype\Abs_Test_rms.xlsx"
    sheet_rms = "Sheet1"
    sr= 1000  #Hz
    dataFrame_rms = pd.read_excel(io= file_rms, sheet_name=sheet_rms)
    npdf_rms = np.asarray(dataFrame_rms) #packing the exel sEMG rms vectors into a numpy array
    #Salviamo l'array per le future letture 

    print("npdf_rms = \n{}".format(npdf_rms[1:20, 1:10]))
    print("shape npdf_rms = {}".format(np.shape(npdf_rms)))


    signal_bicep_Dx_rms = npdf_rms.T[1, 1:] # traspose for non se lo ricorda  salto priam riga e colonna degli indici 
    s_rms_lenght = signal_bicep_Dx_rms.shape[0]
    s_rms_duration = (1/sr)*s_rms_lenght
    s_rms_instants = np.arange(0, s_rms_lenght)*1/sr
    #normalizzazione
    signal_bicep_Dx_rms_normalized = signal_bicep_Dx_rms / np.max(signal_bicep_Dx_rms)
    print("Original Duration: {} seconds".format(s_rms_duration))
    np.save('signal_bicep_Dx_rms_normalized.npy', signal_bicep_Dx_rms_normalized)
''' 
########################################################## Sengnale sEmg Raw #############################################################

file_normal = "C:\\Users\david\OneDrive - Politecnico di Milano\Il_mio_mondo\Corsi Università\Magistrale\Tesi\LWT3\\firstPrototype\Abs_Test_Corretto.xlsx"
sheet_normal = "Sheet1"
dataFrame_normal = pd.read_excel(io=file_normal, sheet_name=sheet_normal)
npdf_normal = np.asarray(dataFrame_normal) #packing the exel sEMG rms vectors into a numpy array
signal_bicep_Dx_normal = npdf_normal.T[1, 1:]

print("npdf_normal= \n{}".format(npdf_normal[1:20, 1:10]))
print("shape npdf_normal = {}".format(np.shape(npdf_normal)))

s_normal_lenght = signal_bicep_Dx_normal.shape[0]
s_normal_duration = (1/sr)*s_normal_lenght
s_normal_instants = np.arange(0, s_normal_lenght)*1/sr

print('the normal length ', s_normal_lenght, 'the rms length ',s_rms_lenght)

signal_bicep_Dx_normal_normalized = signal_bicep_Dx_normal / np.max(signal_bicep_Dx_normal)


print("Original Duration: {} seconds".format(s_normal_duration))
'''
'''
Devo capire come mai mi da un errore con i QT plugin, forse è colpa di OneDrive di merda
plt.figure(figsize=(10,6))
plt.plot(s_rms_instants, signal_bicep_Dx_rms)
#plt.plot(s_normal_instants, signal_bicep_Dx_normal)
#plt.autoscale(enable=True, axis='x', tight=True)
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.title('RMS sEMG Bicept Dx')
'''



def sEmg1_mapping(unused_addr, args, client):
    print("sEMG1 received") 
    client.send_message("/sEmg_1_received", "value")


# we need to set up the main python methods, dealing with the main python thread first 
if __name__ == "__main__":
    #if you are the python main thread then we are going to set up the catchng and sending of OSC messages
    #Set OSC port
    ip = "127.0.0.1" #specila ip to send message only into your computer loval ip adress
    sendPort = 57121 #check the port later 
    inPort= 8000 #check later 
    #sending osc messages 
    client = udp_client.SimpleUDPClient(ip,sendPort)

    #cathces OSC messages 
    dispatcher = dispatcher.Dispatcher()
    #now we create the message names
    dispatcher.map("/sEmg1", sEmg1_mapping) #message name, function to call 

    #setting up a server
    server = ThreadingOSCUDPServer((ip, inPort), dispatcher)
    print("server is on {}.".format(server.server_address))
    #server.serve_forever() #costantily listening for messages 
    #server.kill()

    #provare a mandare l'array signal_bicep_Dx
     
    for i in range(len(signal_bicep_Dx_rms_normalized)):
        
        client.send_message("/rms_BiceptDx", signal_bicep_Dx_rms_normalized[i])
        #client.send_message("/normal_BiceptDx", signal_bicep_Dx_normal_normalized[i])
        print("sending the rms value" , signal_bicep_Dx_rms_normalized[i])

        #print("sending the rms value" , signal_bicep_Dx_rms_normalized[i], "sending the normal value", signal_bicep_Dx_normal_normalized[i])
        


 