#import delle librerie

## Per qualche motivo, all'inizio da sempre l'errore "No module named 'NatNet'".
## Basta per qualche run provare qualcuno di questi diversi import e poi dopo riprovare con 
## "from Acquisition import NatNet" e poi funziona 

#from Acquisition.NatNet.NatNet import NatNetClient #importo la classe NatNetClient per gestire la registrazione dell'optitrack
#import NatNet
from Acquisition import NatNet #importo la classe NatNetClient per gestire la registrazione dell'optitrack
#from NatNet import NatNet
#from NatNet.NatNet import NatNetClient


import serial 
from serial import Serial
#import pyserial as serial
#import serial.tools.list_ports #utilizzata per elencare le porte COM disponibili
#from serial.tools import list_ports
import tools
import argparse
from pythonosc import udp_client


import tkinter as tk
from tkinter import ttk
import json

import pandas as pd

import csv

import time
import datetime

import os
from threading import Thread,Event
import multiprocessing  # libreria per operare su diversi processori in parallelo
import psutil  # libreria utile per alzare la priorità dei processi d'interesse

# vispy libreria per il plottaggio in real time dei segnali, sfrutta la GPU
from vispy import gloo
from vispy import app

import numpy as np
import math

try:
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtWidgets import (QWidget, QPlainTextEdit, QLabel, QPushButton,
                                 QHBoxLayout, QVBoxLayout, QGridLayout)
except ImportError:
    from PyQt5.QtGui import (QWidget, QPlainTextEdit, QFont, QLabel,
                             QPushButton, QHBoxLayout, QVBoxLayout,QGridLayout)

################################FEATURES IMPORTING######################################
from Features.features import * # creo una reference con la subfolder Features importando lo script features.py

#importo funzioni di pre-processing
from PreProcessing.processing import butter_bandpass, butter_bandpass_filter, Implement_Notch_Filter


####################################### Roberto part ##############################################
# Argparse helps writing user-friendly commandline interfaces
parser = argparse.ArgumentParser() 
# OSC server ip
parser.add_argument("--ip", default='127.0.0.1', help="The ip of the OSC server")
# OSC server port (check on SuperCollider)
parser.add_argument("--port", type=int, default=57120, help="The port the OSC server is listening on")

# Initializing Ports
# each one will send the information of a specific channel
port1 = 57121
port2 = 57122
port3 = 57123
port4 = 57124
port5 = 57125
port6 = 57126
port7 = 57127
port8 = 57128

# Parse the arguments
#args = parser.parse_args()

args, unknown = parser.parse_known_args()

# Start the UDP Client
client = udp_client.SimpleUDPClient(args.ip, args.port) 

client1 = udp_client.SimpleUDPClient(args.ip, port1) 
client2 = udp_client.SimpleUDPClient(args.ip, port2) 
client3 = udp_client.SimpleUDPClient(args.ip, port3) 
client4 = udp_client.SimpleUDPClient(args.ip, port4) 
client5 = udp_client.SimpleUDPClient(args.ip, port5) 
client6 = udp_client.SimpleUDPClient(args.ip, port6)
client7 = udp_client.SimpleUDPClient(args.ip, port7) 
client8 = udp_client.SimpleUDPClient(args.ip, port8)

# example of how the message will be sent
#client1.send_message('/name_of_the_message', value_sent)  

def hampel(input, neighbors=3, nsigma=3):

    # I want to implement it in order that if the input is a matrix, then the function treats each column of the input as an independent channel.

    """Applies a Hampel identifier to the input vector to detect and remove outliers. 
        For each sample of the input, the function computes the median of a window composed of the sample and its 2 * "neighbors" surrounding samples, "neighbors" per side. 
        It also estimates the standard deviation of each sample about its window median using the Median Absolute Deviation. 
        If a sample differs from the median by more than "nsigma" standard deviations, it is replaced with the median. 
        
        Args:
            input: numpy vector
            neighbors (int): specifies the number of neighbors on either side of each sample
            nsigma (int): specifies a number of standard deviations by which a sample must differ from the local median for it to be replaced with the median

        Returns:
            output: copy of the input without outliers
            indices: array that contains the indices of the removed outliers
            medians: array that contains the medians of each sample
            sigmas: array that contains the standard deviations of each sample
    """

    # should put an if statement
    # checking that the input is a numpy array
    input = np.asarray(input)

    # Initializing outputs
    output = []
    indices = []
    medians = []
    sigmas = []
    n = len(input)
    temp_input = []
    K = 1.4826 # write formula 1 / (np.sqrt(2) * np.pow(erf, -1) * 0.5) ?

    for i in range(n):

        # Near the sequence endpoints, the function truncates the window used to compute median and sigma
        if i < neighbors + 1:
            for j in range(2 * neighbors + 1 - (neighbors - i)):
                temp_input.append(input[j])
            temp_array = np.asarray(temp_input)
        elif i > n - (neighbors + 1):
            for j in range(2 * neighbors - (neighbors - (n - i))):
                temp_input.append(input[i - (neighbors + 1) + j])
            temp_array = np.asarray(temp_input)

        # Far sequence endpoints (standard) behavior
        else:
            for j in range(2*neighbors+1):
                temp_input.append(input[i - neighbors + j])
            temp_array = np.asarray(temp_input)


        median = np.median(temp_array)  # Local Median
        sd = K * np.median(np.abs(temp_array - median))  # Standard Deviation, sd / K should be the MAD

        if np.abs(input[i] - median) > nsigma * sd:
            # For a given threshold "nsigma" the Hampel identifier delcares the sample an outlier and replace it with its median
            output.append(median)
            indices.append(i)
        else:
            output.append(input[i])
        medians.append(median)
        sigmas.append(sd)
        temp_input.clear()


    return np.asarray(output), np.asarray(indices), np.asarray(medians), np.asarray(sigmas)

# numero sample = ms, tempo di esecuzion di estrazione features, impacchettamento, spedizione, round robin

######################################################### end of Roberto part#############################

def continuos_optitrack(start_event,stop_event,optitrack_server,check_error):
    """controls optitrack registration

    Args:
        start_event(multiprocessing.Event): argument assigned to NatNetClient object to synchronize the registrations start (Emg and Optitrack)
        stop_event(multiprocessing.Event): variable that is used to stop the registrations at the same time, it is set to TRUE when STOP button of the main window is pressed 
        optitrack_server(string): variable containing optitrack server address (loopback=127.0.0.1)
        check_error(Bool): variable that is set to TRUE when abnormal interruption of the EMG acquisition occurs
    """

    if(check_error): #se c'è stata un'interruzione anomala
        opti_client=NatNetClient(server=f'{optitrack_server}') #nuova inizializzazione perchè non c'è piu lo scope di quella prima
        opti_client.run(start_event,check_error) 
        opti_client.stop(check_error) #stop the registration
    else:
        p=psutil.Process()
        p.nice(psutil.REALTIME_PRIORITY_CLASS) #sets the priority of the process to high
        opti_client=NatNetClient(server=f'{optitrack_server}') #initialization of communication between application and Motive
        opti_client.run(start_event,check_error) #start recording when start_event becames TRUE
        while not stop_event.is_set(): #waits until STOP button is pressed  
            pass
        opti_client.stop(check_error) #stop optitrack acquisition

def continuos_acquiring(com_number,start_event,stop_event,hide_event,delete_button_event,modalità,id_muscoli, path_directory,description,additional_data_form, check_error):
    """continuos acquisition of EMG data and plot of Real_time EMG signals
    
    Args:
        com_number (int): numer of the COM port used
        start_event (multiprocessing.Event): variable that is used to synchronize the different acquisitions 
        stop_event (multiprocessing.Event): variable that is used to stop the registrations at the same time, it is set to TRUE when STOP button of the main window is pressed
        hide_event (multiprocessing.Event): variable that is used to show/hide the realtime plot
        delete_button_event (multiprocessing.Event): variable that is used to delete show/hide button
        modalità (int): acquisition mode (frequencies)
        id_muscoli (array_like): array of muscle indeces selected on the main window
        path_directory(string): path of the directory where files will be saved 
        description(string): task's description, used to create a .txt file that describes the task
        check_error (bool): check for abnormal interruption of Emg acquisition
    """
    if(check_error):
        try:
            ser=serial.Serial(f'COM{com_number}',baudrate=3000000,xonxoff=True) #aprire la porta
            stop_msg=bytearray([160, 0, 0, 2, 0, 0, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 232]) #istruzione per stoppare la trasmissione dei dati
            ser.write(stop_msg) #scrittura messaggio di STOP
            ser.close() #chiusura seriale
        except serial.serialutil.SerialException: #eccezione se la scheda è stata scollegata
            print(f'COM{com_number} scollegata')
    else:
        p=psutil.Process()
        p.nice(psutil.REALTIME_PRIORITY_CLASS) # set the priority of the process to HIGH
       
        # How to display the EMG channels 
        nrows = 4
        ncols = 2

        # Number of EMG signals.
        m = nrows*ncols

        # Number of samples per signal to be displayed.
        n = 1000  # Roberto # e se questo parametro si facesse controllabile?
        
        #scale factor
        amplitudes=0.000007

        #initialization of the first n points 
        y=np.empty([m,n])
        y[0,:]=amplitudes*np.ones([1,n])
        y[1,:]=amplitudes*np.ones([1,n])
        y[2,:]=amplitudes*np.ones([1,n])
        y[3,:]=amplitudes*np.ones([1,n])
        y[4,:]=amplitudes*np.ones([1,n])
        y[5,:]=amplitudes*np.ones([1,n])
        y[6,:]=amplitudes*np.ones([1,n])
        y[7,:]=amplitudes*np.ones([1,n])
        y.astype(np.float32)

        #colors
        c=[[1, 0, 0],[1, 1, 0],[0.5, 1, 0],[1, 1, 1],[1, 0, 0],[1, 1, 0],[0.5, 1, 0],[1, 1, 1]]
        color = np.repeat(c,
                  n, axis=0).astype(np.float32)

        # Signal 2D index of each vertex (row and col) and x-index (sample index
        # within each signal).
        index = np.c_[np.repeat(np.repeat(np.arange(ncols), nrows), n),
                    np.repeat(np.tile(np.arange(nrows), ncols), n),
                    np.tile(np.arange(n), m)].astype(np.float32)  # ?

        VERT_SHADER = """
        #version 120

        // y coordinate of the position.
        attribute float a_position;

        // row, col, and time index.
        attribute vec3 a_index;
        varying vec3 v_index;

        // 2D scaling factor (zooming).
        uniform vec2 u_scale;

        // Size of the table.
        uniform vec2 u_size;

        // Number of samples per signal.
        uniform float u_n;

        // Color.
        attribute vec3 a_color;
        varying vec4 v_color;

        // Varying variables used for clipping in the fragment shader.
        varying vec2 v_position;
        varying vec4 v_ab;

        void main() {
            float nrows = u_size.x;
            float ncols = u_size.y;

            // Compute the x coordinate from the time index.
            float x = -1 + 2*a_index.z / (u_n-1);
            vec2 position = vec2(x - (1 - 1 / u_scale.x), a_position);

            // Find the affine transformation for the subplots.
            vec2 a = vec2(1./ncols, 1./nrows)*.9;
            vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                        -1 + 2*(a_index.y+.5) / nrows);
            // Apply the static subplot transformation + scaling.
            gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);

            v_color = vec4(a_color, 1.);
            v_index = a_index;

            // For clipping test in the fragment shader.
            v_position = gl_Position.xy;
            v_ab = vec4(a, b);
        }
        """  # Java?

        FRAG_SHADER = """
        #version 120

        varying vec4 v_color;
        varying vec3 v_index;

        varying vec2 v_position;
        varying vec4 v_ab;

        void main() {
            gl_FragColor = v_color;

            // Discard the fragments between the signals (emulate glMultiDrawArrays).
            if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
                discard;

            // Clipping test.
            vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
            if ((test.x > 1) || (test.y > 1))
                discard;
        }
        """
        #                 port; xonxoff -> enable software flow control
        ser=serial.Serial(f'COM{com_number}',baudrate=3000000,xonxoff=True) #open the serial port

        #correspondence between MODE values and bytearray to be sent to the device to start the streaming
        mode_set={
            0:bytearray([160, 0, 0, 2, 1, 0, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 233]),
            1:bytearray([160, 0, 0, 2, 1, 1, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 232]),
            2:bytearray([160, 0, 0, 2, 1, 2, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 235]),
            3:bytearray([160, 0, 0, 2, 1, 3, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 234]),
            4:bytearray([160, 0, 0, 2, 1, 4, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 237]),
            5:bytearray([160, 0, 0, 2, 1, 5, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 236]),
            6:bytearray([160, 0, 0, 2, 1, 6, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 239]),
            7:bytearray([160, 0, 0, 2, 1, 7, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 238])
        }

        #correspondence between frequencies and MODE values
        frequenze={
            0:2700,
            1:2700,
            2:2000,
            3:2000,
            4:1000,
            5:1000,
            6:500,
            7:500
        }
        
        MODE=mode_set.get(modalità) #selected bytearray to be sent to the device
        fsa=frequenze.get(modalità) #frequency of the selected mode

        #corrispondenza con i muscoli scelti nella main window prima dell'acquisizione, solo espressi in latino
        muscoli_set={
            0 : 'Pectoralis Major Dx',
            1 : 'Lower Trapezius Dx',
            2 : 'Rhomboid Major Dx',
            3 : 'Infraspinatus Dx',
            4 : 'Erector Spinae Dx',
            5 : 'Latissimus Dorsi Dx',
            6 : 'Deltoid Lateral Dx',
            7 : 'Triceps Brachii Long Head Dx',
            8 : 'Biceps Brachii Dx',
            9 : 'Brachioradialis Dx',
            10 : 'Gluteus Maximus Dx',
            11 : 'Biceps Femoris Dx',
            12 : 'Gastrocnemius Lateralis Dx',
            13 : 'Rectus Femoris Dx',
            14 : 'Vastus Lateralis Dx',
            15 : 'Sternocleidomastoid Dx',
            16 : 'Serratus Anterior Dx',
            17 : 'Rectus Abdominis Dx',
            18 : 'Upper Trapezius Dx',
            19 : 'Middle Trapezius Dx',
            20 : 'Rhomboid Minor Dx',
            21 : 'Posterior Deltoid Dx',
            22 : 'Anterior Deltoid Dx',
            23 : 'Triceps Long Head Dx',
            24 : 'Triceps Lateral Head Dx',
            25 : 'Biceps Brachii Short Head Dx',
            26 : 'Biceps Brachi Long Head Dx',
            27 : 'Palmaris Longus Dx',
            28 : 'Flexor Carpi Radialis Dx',
            29 : 'Pronator Teres Dx',
            30 : 'Extensor Carpi Ulnaris Dx',
            31 : 'Extensor Carpi Radialis Dx',
            32 : 'Abductor Digiti Minimi Dx',
            33 : 'Flexor Pollicis Brevis Dx',
            34 : 'Gluteus Medius Dx',
            35 : 'Semitendinosus Dx',
            36 : 'Gastrocnemius Medialis Dx',
            37 : 'Soleus Dx',
            38 : 'Tensor Fasciae Latae Dx',
            39 : 'Vastus Medialis Dx',
            40 : 'Tibialis Anterior Dx',
            41 : 'Peroneus Longus Dx',


            42 : 'Pectoralis Major Sx',
            43 : 'Lower Trapezius Sx',
            44 : 'Rhomboid Major Sx',
            45 : 'Infraspinatus Sx',
            46 : 'Erector Spinae Sx',
            47 : 'Latissimus Dorsi Sx',
            48 : 'Deltoid Lateral Sx',
            49 : 'Triceps Brachii Long Head Sx',
            50 : 'Biceps Brachii Sx',
            51 : 'Brachioradialis Sx',
            52 : 'Gluteus Maximus Sx',
            53 : 'Biceps Femoris Sx',
            54 : 'Gastrocnemius Lateralis Sx',
            55 : 'Rectus Femoris Sx',
            56 : 'Vastus Lateralis Sx',
            57 : 'Sternocleidomastoid Sx',
            58 : 'Serratus Anterior Sx',
            59 : 'Rectus Abdominis Sx',
            60 : 'Upper Trapezius Sx',
            61 : 'Middle Trapezius Sx',
            62 : 'Rhomboid Minor Sx',
            63 : 'Posterior Deltoid Sx',
            64 : 'Anterior Deltoid  Sx',
            65 : 'Triceps Long Head Sx',
            66 : 'Triceps Lateral Head Sx',
            67 : 'Biceps Brachii Short Head Sx',
            68 : 'Biceps Brachi Long Head Sx',
            69 : 'Palmaris Longus Sx',
            70 : 'Flexor Carpi Radialis Sx',
            71 : 'Pronator Teres Sx',
            72 : 'Extensor Carpi Ulnaris Sx',
            73 : 'Extensor Carpi Radialis Sx',
            74 : 'Abductor Digiti Minimi Sx',
            75 : 'Flexor Pollicis Brevis Sx',
            76 : 'Gluteus Medius Sx',
            77 : 'Semitendinosus Sx',
            78 : 'Gastrocnemius Medialis Sx',
            79 : 'Soleus Sx',
            80 : 'Tensor Fasciae Latae Sx',
            81 : 'Vastus Medialis Sx',
            82 : 'Tibialis Anterior Sx',
            83 : 'Peroneus Longus Sx',

            84: 'Not Connected'
        }
        
        muscoli_sorted = dict(sorted(muscoli_set.items(), key=lambda x:x[1]))
        print("muscoli ordinati: \n", muscoli_sorted)
        # Roberto -> da qui in poi ho sostituito tutti i "muscoli_set" con "muscoli_sorted"

        #nomi dei muscoli selezionati
        muscolo1=muscoli_sorted.get(id_muscoli[0]) 
        muscolo2=muscoli_sorted.get(id_muscoli[1]) 
        muscolo3=muscoli_sorted.get(id_muscoli[2]) 
        muscolo4=muscoli_sorted.get(id_muscoli[3]) 
        muscolo5=muscoli_sorted.get(id_muscoli[4]) 
        muscolo6=muscoli_sorted.get(id_muscoli[5]) 
        muscolo7=muscoli_sorted.get(id_muscoli[6]) 
        muscolo8=muscoli_sorted.get(id_muscoli[7]) 
        
        timestr = time.strftime("%Y%m%d_%H%M%S")

        description_path=os.path.abspath(os.path.join(f'{path_directory}','Description.txt'))
        #scrittuta di un file .txt che riassume la prova
        with open(description_path, "w") as text_file:
            text_file.write(f'{description}')
        
        template_path=os.path.abspath(os.path.join(f'{path_directory}','Template.txt'))
        with open(template_path, "w") as text_file:
            for muscle in range (0, len(id_muscoli)):
                text_file.write(f'{muscoli_sorted.get(id_muscoli[muscle])}\n')
        
        if(additional_data_form != ''):     # se il form di additional data del paziente è stato compilato allora posso scriverlo sul file txt
            additional_data_path=os.path.abspath(os.path.join(f'{path_directory}','Additional_Data.json'))
            with open(additional_data_path, "w") as f:
                json.dump(additional_data_form, f, indent=4, default=str)
                
        path_file=os.path.abspath(os.path.join(f'{path_directory}',f'REC_COM{com_number}_{timestr}emg.csv'))
        outfile=open(path_file, 'w+') #open a .csv file and write header
        filewriter = csv.writer(outfile, delimiter=';',
                                quotechar=' ', quoting=csv.QUOTE_MINIMAL,lineterminator = '\n')
        filewriter.writerow(['TIMESTAMP','STREAM_ID','SEQUENCE',muscolo1,muscolo2,muscolo3,muscolo4,muscolo5,muscolo6,muscolo7,muscolo8,'LAP']) #csv header
        
        #class that controls real time plot
        class Canvas(app.Canvas):
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    if key=='parent':
                        self.parent=value

                app.Canvas.__init__(self, title='Use your wheel to zoom!',
                                    keys='interactive', **kwargs)
                self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
                self.program['a_position'] = y.reshape(-1, 1).astype(np.float32)
                self.program['a_color'] = color
                self.program['a_index'] = index
                self.program['u_scale'] = (1., 1.)
                self.program['u_size'] = (nrows, ncols)
                self.program['u_n'] = n
                self.check_primo_tempo=True #variabile per controllare la stampa del timestamp ad un intervallo specifico 
                self.lap_inserted = False #variabile per inserire dei "marker" nell'acquisizione
                self.lap_count = 0
                self.dx_tot = 0 #variabile per tenere traccia dello zoom sulla finestra di plot
                self.count=0 #variabile per contare il numero di registrazioni all'interno di quell'intervallo specifico

                gloo.set_viewport(0, 0, *self.physical_size)

                self._timer = app.Timer('auto', connect=self.on_timer, start=True)

                gloo.set_state(clear_color='black', blend=True,
                            blend_func=('src_alpha', 'one_minus_src_alpha'))

            def on_resize(self, event):
                gloo.set_viewport(0, 0, *event.physical_size)

            def on_mouse_wheel(self, event):
                #when the mouse wheel is moved, a zooming on the y axis is performed
                dx = np.sign(event.delta[1]) * .05                
                if self.dx_tot+dx >= 0:             #check that the overall "wheeling" doesn't go negative, otherwise it could cause problems
                    self.dx_tot = self.dx_tot + dx
                    scale_x, scale_y = self.program['u_scale']
                    scale_x_new, scale_y_new = (scale_x * math.exp(0.0*dx),
                                                scale_y * math.exp(1.5*dx))
                    self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
                    self.update()

            def on_mouse_double_click(self, event):
                #when you doubleclick on the window, it will print a lap on the emg file
                self.lap_inserted = True
                self.lap_count = self.lap_count+1

            def on_timer(self, event):
                """Acquires and adds some data at the end of each signal (real-time signals)."""
                try:
                    #k = 20 #vecchio valore di k
                    k = 64  #number of new points to be displayed (k new points will be added and the first 20 points will be delated) the frequency of acquisition is fs/k
                    #se aumento k manda meno accquisizioni al secondo, quindi il valore sarù più smooth

                    #k_osc = 256
                    i=k
                    #lists that will contain the new points
                    g00=[]
                    g01=[]
                    g02=[]
                    g03=[]
                    g10=[]
                    g11=[]
                    g12=[]
                    g13=[]

                    readings = []
                    packings = []
                    hampels = []
                    sends = []


                    try:
                        while (i and not stop_event.is_set()):  # k acquisitions if button stop is not pressed

                            pre_reading = datetime.datetime.now()
                            print("pre-reading: ", pre_reading)
                            s=ser.read(20)

                            post_reading = datetime.datetime.now()
                            print("post-reading, pre-packing: ", post_reading)
                            reading_time = post_reading.microsecond - pre_reading.microsecond
                            print("reading time: ", reading_time)
                            readings.append(reading_time)

                            stream_id=s[-2]  # da protocollo l'informazione dello stream è nel penultimo byte
                            sequence=int.from_bytes(s[1:3], byteorder='little')
                            g0_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True)  # l'informazione del sensore è codificata su 3Byte, nella posizione indicata, dal byte meno significativo a quello più significativo, l'ultimo bit del byte rappresenta il segno (signed=True)
                            g0_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
                            g0_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
                            g0_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)
                            # ALLA SECONDA ITERAZIONE VADO A LEGGERE L'INFORMAZIONE DEGLI ALTRI 4 CANALI
                            s=ser.read(20)
                            g1_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True)  # l'informazione del sensore è codificata su 3Byte, nella posizione indicata
                            g1_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
                            g1_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
                            g1_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)
                            self.timestamp=datetime.datetime.now()  # calcolo il tempo macchina


                            if self.lap_inserted:
                                LAP = 'LAP'+str(self.lap_count)
                            else:
                                LAP = np.nan

                            if(self.check_primo_tempo):  # entra solamente quando passa un tempo specifico (inizializzata a True per stampare il tempo del primo campione)
                                self.primo_tempo=self.timestamp+datetime.timedelta(0,10)  # dopo 10 secondi controllerò il numero di campioni in questo intervallo e scriverò il timestamp
                                filewriter.writerow([self.timestamp,stream_id,sequence,g0_ch0,g0_ch1,g0_ch2,g0_ch3,g1_ch0,g1_ch1,g1_ch2,g1_ch3, LAP]) #scrivo sul file csv
                                self.check_primo_tempo=False  # variabile diventa falsa
                                self.lap_inserted = False
                            else:
                                filewriter.writerow([np.nan,stream_id,sequence,g0_ch0,g0_ch1,g0_ch2,g0_ch3,g1_ch0,g1_ch1,g1_ch2,g1_ch3, LAP])  # scrivo sul file csv, il timestamp in questo caso sarà NaN
                                self.lap_inserted = False

                            self.count=self.count+1  # conto il numero di acquisizioni
                            
                            g00.append(g0_ch0)
                            g01.append(g0_ch1)
                            g02.append(g0_ch2)
                            g03.append(g0_ch3)
                            g10.append(g1_ch0)
                            g11.append(g1_ch1)
                            g12.append(g1_ch2)
                            g13.append(g1_ch3)

                            i=i-1
                        #esco dal ciclo while quando ho effettuato 20 acquisizioni (aggiorno il grafico ogni 20 campioni)
                        
                        #casting from list to np.array and float32
                        g00=np.asarray([i * amplitudes for i in g00])
                        g00.astype(np.float32)
                        g01=np.asarray([i * amplitudes for i in g01])
                        g01.astype(np.float32)
                        g02=np.asarray([i * amplitudes for i in g02])
                        g02.astype(np.float32)
                        g03=np.asarray([i * amplitudes for i in g03])
                        g03.astype(np.float32)
                        g10=np.asarray([i * amplitudes for i in g10])
                        g10.astype(np.float32)
                        g11=np.asarray([i * amplitudes for i in g11])
                        g11.astype(np.float32)
                        g12=np.asarray([i * amplitudes for i in g12])
                        g12.astype(np.float32)
                        g13=np.asarray([i * amplitudes for i in g13])
                        g13.astype(np.float32)

                        post_packing = datetime.datetime.now()
                        print("post-packing, pre-Hampeling: ", post_packing)
                        packing_time = post_packing.microsecond - post_reading.microsecond
                        print("packing time: ", packing_time)
                        packings.append(packing_time)

                        #if np.max(g00) > last_max_00:
                            #last_max_00 = np.max(g00)
                        #if np.max(g01) > last_max_01: 
                            #last_max_01 = np.max(g01)
                        #if np.max(g02) > last_max_02: 
                            #last_max_02 = np.max(g02)
                        #if np.max(g03) > last_max_03: 
                            #last_max_03 = np.max(g03)
                        #if np.max(g10) > last_max_10: 
                            #last_max_10 = np.max(g10)
                        #if np.max(g11) > last_max_11: 
                            #last_max_11 = np.max(g11)
                        #if np.max(g12) > last_max_12: 
                            #last_max_12 = np.max(g12)
                        #if np.max(g13) > last_max_13: 
                            #last_max_13 = np.max(g13)
                         
                        #client1.send_message('/channel_0_0', hampel(g00 / last_max_00))   
                        #client2.send_message('/channel_0_1', hampel(g01 / last_max_01))   
                        #client3.send_message('/channel_0_2', hampel(g02 / last_max_02))   
                        #client4.send_message('/channel_0_3', hampel(g03 / last_max_03))   
                        #client5.send_message('/channel_1_0', hampel(g10 / last_max_10))   
                        #client6.send_message('/channel_1_1', hampel(g11 / last_max_11))   
                        #client7.send_message('/channel_1_2', hampel(g12 / last_max_12)) 
                        #client8.send_message('/channel_1_3', hampel(g13 / last_max_13)) 

                        #client1.send_message('/channel_0_0', g00 / last_max_00)   
                        #client2.send_message('/channel_0_1', g01 / last_max_01)   
                        #client3.send_message('/channel_0_2', g02 / last_max_02)   
                        #client4.send_message('/channel_0_3', g03 / last_max_03)   
                        #client5.send_message('/channel_1_0', g10 / last_max_10)   
                        #client6.send_message('/channel_1_1', g11 / last_max_11)   
                        #client7.send_message('/channel_1_2', g12 / last_max_12) 
                        #client8.send_message('/channel_1_3', g13 / last_max_13) 

                        #client1.send_message('/channel_0_0', g00 / np.max(g00))   
                        #client2.send_message('/channel_0_1', g01 / np.max(g01))   
                        #client3.send_message('/channel_0_2', g02 / np.max(g02))   
                        #client4.send_message('/channel_0_3', g03 / np.max(g03))   
                        #client5.send_message('/channel_1_0', g10 / np.max(g10))   
                        #client6.send_message('/channel_1_1', g11 / np.max(g11))   
                        #client7.send_message('/channel_1_2', g12 / np.max(g12)) 
                        #client8.send_message('/channel_1_3', g13 / np.max(g13)) 


                        g00_h, idx_00, medians_00, sd_00 = hampel(g00)
                        g01_h, idx_01, medians_01, sd_01 = hampel(g01)
                        g02_h, idx_02, medians_02, sd_02 = hampel(g02)
                        g03_h, idx_03, medians_03, sd_03 = hampel(g03)
                        g10_h, idx_10, medians_10, sd_10 = hampel(g10)
                        g11_h, idx_11, medians_11, sd_11 = hampel(g11)
                        g12_h, idx_12, medians_12, sd_12 = hampel(g12)
                        g13_h, idx_13, medians_13, sd_13 = hampel(g13)

                        post_hampeling = datetime.datetime.now()
                        print("post-Hampeling, pre-sending: ", post_hampeling)
                        hamepling_time = post_hampeling.microsecond - post_packing.microsecond
                        print("Hampeling time: ", hamepling_time)
                        hampels.append(hamepling_time)

                        #client1.send_message('/channel_0_0', g00_h)   
                        client1.send_message('/rmsValue',  RMS(g00) / np.max(g00)) #Mando l'RMS al posto che il valore puntuale
                        client2.send_message('/MAV', MAV(g00) / np.max(g00))  # g01_h client2 # forse il .microsecond potrebbe essere un problema
                        client3.send_message('/channel_0_2', g02_h)   
                        client4.send_message('/channel_0_3', g03_h)   
                        client5.send_message('/channel_1_0', g10_h)   
                        client6.send_message('/channel_1_1', g11_h)   
                        client7.send_message('/channel_1_2', g12_h) 
                        client8.send_message('/channel_1_3', g13_h) 

                        post_sent = datetime.datetime.now()
                        print("post-sent: ", post_sent)
                        sending_time = post_sent.microsecond - post_hampeling.microsecond
                        print("sending time: ", sending_time)
                        sends.append(sending_time)

                        #client1.send_message('/channel_0_0', g00)   
                        #client2.send_message('/channel_0_1', g01)   
                        #client3.send_message('/channel_0_2', g02)   
                        #client4.send_message('/channel_0_3', g03)   
                        #client5.send_message('/channel_1_0', g10)   
                        #client6.send_message('/channel_1_1', g11)   
                        #client7.send_message('/channel_1_2', g12) 
                        #client8.send_message('/channel_1_3', g13) 
                        
                        y[:, :-k] = y[:, k:] #tolgo i primi k campioni
    
                        #aggiungo alla fine k campioni
                        y[3, -k:] = g00_h #the display order starts from the bottom left corner (UPPER LEFT)
                        y[2, -k:] = g01_h
                        y[1, -k:] = g02_h
                        y[0, -k:] = g03_h #(BOTTOM LEFT)

                        y[7, -k:] = g10_h #(UPPER RIGHT)
                        y[6, -k:] = g11_h
                        y[5, -k:] = g12_h
                        y[4, -k:] = g13_h #(BOTTOM RIGHT)

                        self.program['a_position'].set_data(y.ravel().astype(np.float32))
                        self.update()
                    
                    except IndexError: #exception se la lettuta da USB risulta incompleta
                        print('Problemi di lettura da USB')
                        app.quit()

                except: 
                    #quando premo il tasto stop si verifica l'except perchè non riesce a compiere il try, 
                    #questo permette di superare l'effetto bloccante dell'applicazione di visualizzazione dei grafici real-time 
                    #(non è più necessario chiudere prima l'applicazione di plottaggio e poi premere il tasto STOP)

                    app.quit()
                    print("readings mean = ", np.mean(np.asarray(readings)))
                    print("packings mean = ", np.mean(np.asarray(packings)))
                    print("hampels mean = ", np.mean(np.asarray(hampels)))
                    print("sends mean = ", np.mean(np.asarray(sends)))

                if(self.timestamp>self.primo_tempo): #se sono passati 10 secondi
                    if(self.count<int(10*fsa)): #controllo se il numero di osservazioni è minore di quello atteso 
                        for i in range(0,int(10*fsa)-self.count): #se sono minori di quelle attese aggiungo delle righe vuote
                            filewriter.writerow([np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]) #write each acquisition to the csv file
                    self.count=0 #azzero il contatore
                    self.check_primo_tempo=True #variabile diventa vera per stampare il timestamp al campione successivo

                #quando nella gui premo il pulsante show/hide
                if (hide_event.is_set()):
                    #se era nascosto lo rendo visibile 
                    if self.parent.isHidden():
                        self.parent.show()
                        self.parent.activateWindow()
                        self.parent.raise_()
                    #se era visibile lo nascondo
                    else:
                        self.parent.hide()
                    hide_event.clear() #l'evento diventa False ritornerà True quando premo show/hide nella GUI

            def on_draw(self, event):
                gloo.clear()
                self.program.draw('line_strip')
        
        class MainWindow(QWidget):
            def __init__(self,muscolo1,muscolo2,muscolo3,muscolo4,muscolo5,muscolo6,muscolo7,muscolo8):
                QWidget.__init__(self, None)

                self.setMinimumSize(600, 400)
                self.setStyleSheet("background-color: black;")
                self.setWindowTitle(f'REAL TIME PLOT COM{com_number}')

                #Create titles
                self.channels_label= QLabel(muscolo1, self)
                self.channels_label.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label2= QLabel(muscolo2, self)
                self.channels_label2.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label3= QLabel(muscolo3, self)
                self.channels_label3.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label4= QLabel(muscolo4, self)
                self.channels_label4.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label5= QLabel(muscolo5, self)
                self.channels_label5.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label6= QLabel(muscolo6, self)
                self.channels_label6.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label7= QLabel(muscolo7, self)
                self.channels_label7.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")
                self.channels_label8= QLabel(muscolo8, self)
                self.channels_label8.setStyleSheet("QLabel { background-color : black; color : white;font: 10pt; }")

                #Create a canvas
                self.canvas = Canvas(parent=self)
                
                #Layout dell'applicazione
                grid = QGridLayout()
                grid.setSpacing(10)
                
                grid.addWidget(self.channels_label, 1, 0)
                grid.addWidget(self.channels_label2, 2, 0)
                grid.addWidget(self.channels_label3, 3, 0)
                grid.addWidget(self.channels_label4, 4, 0)
                
                grid.addWidget(self.canvas.native, 1, 1,-1,13)

                grid.addWidget(self.channels_label5, 1, 15)
                grid.addWidget(self.channels_label6, 2, 15)
                grid.addWidget(self.channels_label7, 3, 15)
                grid.addWidget(self.channels_label8, 4, 15)

                self.setLayout(grid) 
                self.show()

        app.create() #creazione app
        m=MainWindow(muscolo1,muscolo2,muscolo3,muscolo4,muscolo5,muscolo6,muscolo7,muscolo8) #inizializzazione app
        start_event.wait() #wait until the event is set to TRUE
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.flush()
        start_time1=datetime.datetime.now()
        print(f'start COM{com_number} EMG acquisition: {start_time1}')
        ser.write(MODE) #sends the acquisition mode to the device
        s=ser.read(20) #first acquisition discharged
        app.run() #real_time plot (BLOCKING FUNCTION!)
        try:
            while not stop_event.is_set(): #wait until button STOP is pressed (questa acquisizione viena effettuata solo se viene chiusa la finestra del plot real timec, che è bloccante, prima della pressione del tasto STOP)
                #questa acquisizione viene effettuata se viene chiusa la finestra di plottaggio prima che venga premuto il tasto stop
                #il timestamp non verrà più stampato ogni 10 secondi, ma verrà aggiunto il timestamp solamente dell'ultima lettura
                #nell'applicazione RawPower gli istanti di tempo nan verranno interpolati linearmente
                delete_button_event.set() #quando entro in questo ciclo significa che ho chiuso definitivamente il plot realtime per cui vado a settare a True l'evento per cancellare il pulsante show/hide 
                s=ser.read(20)
                stream_id=s[-2] #da protocollo l'informazione dello stream è nel penultimo byte
                sequence=int.from_bytes(s[1:3], byteorder='little')
                g0_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True) #l'informazione del sensore è codificata su 3Byte, nella posizione indicata, dal byte meno significativo a quello più significativo, l'ultimo bit del bit rappresenta il segno (signed=True)
                g0_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
                g0_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
                g0_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)
                #ALLA SECONDA ITERAZIONE VADO A LEGGERE L'INFORMAZIONE DEGLI ALTRI 4 CANALI
                s=ser.read(20)
                g1_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True) #l'informazione del sensore è codificata su 3Byte, nella posizione indicata
                g1_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
                g1_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
                g1_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)

                filewriter.writerow([np.nan,stream_id,sequence,g0_ch0,g0_ch1,g0_ch2,g0_ch3,g1_ch0,g1_ch1,g1_ch2,g1_ch3])

            #effettuo un'ultima acquisizione per stampare l'ultimo timestamp
            s=ser.read(20)
            stream_id=s[-2] #da protocollo l'informazione dello stream è nel penultimo byte
            sequence=int.from_bytes(s[1:3], byteorder='little')
            g0_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True) #l'informazione del sensore è codificata su 3Byte, nella posizione indicata, dal byte meno significativo a quello più significativo, l'ultimo bit del bit rappresenta il segno (signed=True)
            g0_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
            g0_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
            g0_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)
            #ALLA SECONDA ITERAZIONE VADO A LEGGERE L'INFORMAZIONE DEGLI ALTRI 4 CANALI
            s=ser.read(20)
            g1_ch0=int.from_bytes(s[5:8], byteorder='little', signed=True) #l'informazione del sensore è codificata su 3Byte, nella posizione indicata
            g1_ch1=int.from_bytes(s[8:11], byteorder='little', signed=True)
            g1_ch2=int.from_bytes(s[11:14], byteorder='little', signed=True)
            g1_ch3=int.from_bytes(s[14:17], byteorder='little', signed=True)
            timestamp=datetime.datetime.now()

            filewriter.writerow([timestamp,stream_id,sequence,g0_ch0,g0_ch1,g0_ch2,g0_ch3,g1_ch0,g1_ch1,g1_ch2,g1_ch3])

            stop_msg=bytearray([160, 0, 0, 2, 0, 0, 96, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 232]) #stop streaming message
            ser.write(stop_msg) #send the stop command
            ser.flush() #flush the buffers
            ser.close() #close the port
            
        except serial.serialutil.SerialException: #exception se l'acquisizione si è interrotta
            timestamp=datetime.datetime.now()
            filewriter.writerow([timestamp,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan])
            print('Interruzione acquisizione SerialException')

        print(f'stop COM{com_number} EMG acquisition {datetime.datetime.now()}  durata: {(datetime.datetime.now()-start_time1)}')

        outfile.close() #close csv file

        # Trasferisco la colonna lap in un singolo file txt e la elimino dall'acquisizione --> per assicurare compatibilità con la versione precedente di rawpower
        acquisition = pd.read_csv(path_file, delimiter=';')
        print(acquisition)
        lap = acquisition['LAP'].dropna()
        lap = lap.astype('string')

        laps_write=os.path.abspath(os.path.join(f'{path_directory}','LAPS.txt'))
        #scrittuta di un file .txt che riassume la prova
        with open(laps_write, "w") as text_file:
            for index, value in lap.items():
                text_file.write('At row: ' + str(index) + ' there is ' + value + '\n')
        

        acquisition.drop('LAP', axis=1, inplace=True)
        acquisition.to_csv(path_file, sep=';', index=False)
