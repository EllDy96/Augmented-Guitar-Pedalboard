#PROVA TAGLIO SEGNALE CON OPTITRACK
import tkinter as tk
from tkinter import filedialog
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import random
import matplotlib.dates as md

import os
import fileinput
from fitparse import FitFile
import datetime

#pre-processing
from scipy.signal.filter_design import butter
from scipy.signal import lfilter
from scipy.signal import iirfilter
from scipy import signal

import peakutils 
from biosppy.signals import emg
import time


def window_rms(a, window_size):
    """computes RMS along the signal through convolution 
    
    Args:
        a(array_like): original signal
        window_size (int): length of the rectangular window 
 
    Returns: 
        array_like: RMS values
    """
    a2 = np.power(a,2)
    window = np.ones(window_size)/float(window_size)
    return np.sqrt(np.convolve(a2, window, 'valid'))

#processing
def butter_bandpass(lowcut, highcut, fs, order=5):
    """returns butterworth filter coefficients
    
    Args:
        lowcut(int,float): low cutoff frequency
        highcut(int,float): high cutoff frequency
        fs(int): sampling frequency
        order(int,optional): order of the filter, default value {5}
 
    Returns: 
        ndarray: Numerator polynomials of the IIR filter
    Returns:
        ndarray: Denominator polynomials of the IIR filter
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=3):
    """returns the filtered signal after butterworth filter is applied
    
    Args:
        data (array_like): original signal
        lowcut(int,float): low cutoff frequency
        highcut(int,float): high cutoff frequency
        fs(int): sampling frequency
        order(int,optional): order of the filter, default value {3}

    Returns:
        array_like: output of the digital filter
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def Implement_Notch_Filter(fs, band, freq, ripple, order, filter_type, data):
    """implements notch filter at freq and its harmonics

    Args:
        fs (int): sampling frequency
        band(int,float): The bandwidth around the centerline freqency that you wish to filter
        freq(int,float): The centerline frequency to be filtered
        ripple(int):     The maximum passband ripple that is allowed in db
        order(int):      The filter order.  For FIR notch filters this is best set to 2 or 3,
                            IIR filters are best suited for high values of order.  This algorithm
                            is hard coded to FIR filters
        filter_type (string): 'butter', 'bessel', 'cheby1', 'cheby2', 'ellip'
        data (array_like): the data to be filtered

    Returns:
        array_like: output of the digital filter
    """
    nyq  = fs/2.0
    filtered_data=data
    for i in range(3): #3 harmonics
        low  = freq*(i+1)- band/2.0
        high = freq*(i+1) + band/2.0
        low  = low/nyq
        high = high/nyq
        b, a = iirfilter(order, [low, high], rp=ripple, btype='bandstop',
                        analog=False, ftype=filter_type)
        filtered_data = lfilter(b, a, filtered_data)
    return filtered_data

def load_data(file_directory,fs_emg):
    """opens files (emg, optitrack) from a select folder, if any
    """
    lowcut1=20.0 #frequenza di taglio bassa
    highcut1=float(float(fs_emg/2)-0.1) #frequenza di taglio pari a metà della frequenza di campionamento
    order=5 #ordine del filtro

    #lettura files
    for filename in os.listdir(file_directory):
        if(filename.endswith('emg.csv')): #se è presente un file che termina con 'emg.csv' 
            print(filename)
            with fileinput.FileInput(f'{file_directory}/{filename}') as file: #nel caso in cui il file abbia il sepratore ',' viene convertito in ';' per standardizzare il formato
                for line in file:
                    line.replace(',',';')
            emgX = pd.read_csv(f'{file_directory}/{filename}', delimiter = ';', on_bad_lines='warn') #lettura file emg

            #si presuppone che il file emg sia costituito da queste variabili, converto da stringhe a variabili numeriche tranne il time stamp che viene convertito in datetime
            emgX[emgX.columns[0]] = pd.to_datetime(emgX[emgX.columns[0]], errors='coerce') #timestamp (cast datetime)
            emgX[emgX.columns[1]] = pd.to_numeric(emgX[emgX.columns[1]], errors='coerce') #stream id
            emgX[emgX.columns[2]] = pd.to_numeric(emgX[emgX.columns[2]], errors='coerce') #sequence
            emgX[emgX.columns[3]] = pd.to_numeric(emgX[emgX.columns[3]], errors='coerce') #canale G0_CH0
            emgX[emgX.columns[4]] = pd.to_numeric(emgX[emgX.columns[4]], errors='coerce') #canale G0_CH1
            emgX[emgX.columns[5]] = pd.to_numeric(emgX[emgX.columns[5]], errors='coerce') #canale G0_CH2
            emgX[emgX.columns[6]] = pd.to_numeric(emgX[emgX.columns[6]], errors='coerce') #canale G0_CH3
            emgX[emgX.columns[7]] = pd.to_numeric(emgX[emgX.columns[7]], errors='coerce') #canale G1_CH0
            emgX[emgX.columns[8]] = pd.to_numeric(emgX[emgX.columns[8]], errors='coerce') #canale G1_CH1
            emgX[emgX.columns[9]] = pd.to_numeric(emgX[emgX.columns[9]], errors='coerce') #canale G1_CH2
            emgX[emgX.columns[10]] = pd.to_numeric(emgX[emgX.columns[10]], errors='coerce') #canale G1_CH3
            #interpolo linearmente i NaT (Not a Time), la variabile diventa cast Timestamp
            t0 = emgX[emgX.columns[0]].min()
            m = emgX[emgX.columns[0]].notnull()
            emgX.loc[m, 't_int'] = (emgX.loc[m, emgX.columns[0]] - t0).dt.total_seconds()

            emgX[emgX.columns[0]] = t0 + pd.to_timedelta(emgX.t_int.interpolate(), unit='s')
            
            #interpolo linearmente i NaN eventualmente presenti
            emgX[emgX.columns[3]]=emgX[emgX.columns[3]].interpolate(limit_direction='both') 
            emgX[emgX.columns[4]]=emgX[emgX.columns[4]].interpolate(limit_direction='both')
            emgX[emgX.columns[5]]=emgX[emgX.columns[5]].interpolate(limit_direction='both')
            emgX[emgX.columns[6]]=emgX[emgX.columns[6]].interpolate(limit_direction='both')
            emgX[emgX.columns[7]]=emgX[emgX.columns[7]].interpolate(limit_direction='both')
            emgX[emgX.columns[8]]=emgX[emgX.columns[8]].interpolate(limit_direction='both')
            emgX[emgX.columns[9]]=emgX[emgX.columns[9]].interpolate(limit_direction='both')
            emgX[emgX.columns[10]]=emgX[emgX.columns[10]].interpolate(limit_direction='both')

            print('FILE EMG LOADED')

            emgX[emgX.columns[3]] = emgX[emgX.columns[3]].astype('int64')
            emgX[emgX.columns[4]] = emgX[emgX.columns[4]].astype('int64')
            emgX[emgX.columns[5]] = emgX[emgX.columns[5]].astype('int64')
            emgX[emgX.columns[6]] = emgX[emgX.columns[6]].astype('int64')
            emgX[emgX.columns[7]] = emgX[emgX.columns[7]].astype('int64')
            emgX[emgX.columns[8]] = emgX[emgX.columns[8]].astype('int64')
            emgX[emgX.columns[9]] = emgX[emgX.columns[9]].astype('int64')
            emgX[emgX.columns[10]] = emgX[emgX.columns[10]].astype('int64')

            G0_CH0 = emgX[emgX.columns[3]]
            G0_CH1 = emgX[emgX.columns[4]]
            G0_CH2 = emgX[emgX.columns[5]]
            G0_CH3 = emgX[emgX.columns[6]]

            G1_CH0 = emgX[emgX.columns[7]]
            G1_CH1 = emgX[emgX.columns[8]]
            G1_CH2 = emgX[emgX.columns[9]]
            G1_CH3 = emgX[emgX.columns[10]]

            #filtraggio del segnale passa banda e notch
            filter_dato = butter_bandpass_filter(G0_CH0, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G0_CH0=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G0_CH1, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G0_CH1=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G0_CH2, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G0_CH2=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G0_CH3, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G0_CH3=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G1_CH0, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G1_CH0=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G1_CH1, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G1_CH1=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G1_CH2, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G1_CH2=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            filter_dato = butter_bandpass_filter(G1_CH3, lowcut1, highcut1, fs_emg, order=order) #band pass
            filter_dato_G1_CH3=Implement_Notch_Filter(fs_emg,1,50, None, 3, 'butter', filter_dato) #notch

            #print(emgX)
            #costruisco un dataframe con i segnali filtrati
            Df_Emg= pd.DataFrame(columns=emgX.columns[3:]) #colonne contenenti solo i nomi dei muscoli, non interssa stream_id e sequence
            #assegno al dataframe i valori dei segnali filtrati
            Df_Emg[Df_Emg.columns[0]]=filter_dato_G0_CH0
            Df_Emg[Df_Emg.columns[1]]=filter_dato_G0_CH1
            Df_Emg[Df_Emg.columns[2]]=filter_dato_G0_CH2
            Df_Emg[Df_Emg.columns[3]]=filter_dato_G0_CH3
            Df_Emg[Df_Emg.columns[4]]=filter_dato_G1_CH0
            Df_Emg[Df_Emg.columns[5]]=filter_dato_G1_CH1
            Df_Emg[Df_Emg.columns[6]]=filter_dato_G1_CH2
            Df_Emg[Df_Emg.columns[7]]=filter_dato_G1_CH3

            t_seconds=[date-emgX[emgX.columns[0]][0] for date in emgX[emgX.columns[0]]] #sottraggo il primo valore del timestamp per far partire l'acquisizione al tempo 0

            #ciclo per convertire t_seconds che è in formato datetime.timedelta nel formato datetime.time che ci permette la visualizzazione degli assi
            timestamp_emg=[]
            for duration in t_seconds:
                seconds = duration.total_seconds()
                #print(seconds)
                microseconds=(seconds*1000000) % 1000000
                #print(microseconds)
                hours = seconds // 3600
                #print(hours)
                minutes = (seconds % 3600) // 60
                #print(minutes)
                seconds = seconds % 60 // 1
                #print(seconds)
                timestamp_emg.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))
                #print(timestamp_emg)
            
            #assegno il timestamp determinato all'indice del dataframe dell'Emg e cambio il nome
            Df_Emg.index=timestamp_emg
            Df_Emg.index.name='Time'
            print(Df_Emg)
            '''
            h, ax_1 = plt.subplots(5,1, sharex=True)
            fig = plt.gcf()
            fig.canvas.set_window_title('FILTERED EMG E OPTITRACK')

            Df_Emg[Df_Emg.columns[0]].plot(ax=ax_1[0], legend=False,color='orangered')
            ax_1[0].set_title(f'{Df_Emg.columns[0]}',fontweight="bold")
            ax_1[0].tick_params(labelsize=10)
            plt.show()
            '''

        if(filename.endswith('opti.csv')): #se è presente un file che termina con 'opti.csv' ed è il primo
            print(filename)
            optitrack = pd.read_csv(f'{file_directory}/{filename}', delimiter = ',',header=[1,2,3,4,5], on_bad_lines='warn')
            print('FILE OPTITRACK LOADED')
            
            #variabili per caricare uno specifico corpo rigido Pier alberto primo valore 27 per gli altri 2 (il primo valore)
            rigid_body_name=optitrack.columns[2][1]
            id_opti=optitrack.columns[2][2]
            
            #seleziono solo le colonne di interesse
            optitrack["Time (Seconds)"]=optitrack.iloc[:,optitrack.columns.get_level_values(4) =='Time (Seconds)']
            optitrack[("Rigid Body",rigid_body_name,id_opti,"Position","X")] = pd.to_numeric(optitrack[('Rigid Body',rigid_body_name,id_opti,'Position','X')], errors='coerce')

            Y_optitrack = optitrack[("Rigid Body",rigid_body_name,id_opti,"Position","X")]
            secondi_optitrack=optitrack["Time (Seconds)"]

            #interpolo i NaN
            Y_optitrack=Y_optitrack.interpolate(limit_direction='both')
            secondi_optitrack=secondi_optitrack.interpolate(limit_direction='both')

            #trasformo i secondi del tempo dell'optitrack in una variabile datetime.time (IPOTESI ATTUALE: IL PRIMO CAMPIONE DEI DUE SEGNALI SONO ALLO STESSO TEMPO!!)
            timestamp_optitrack=[]
            for seconds in secondi_optitrack:
                microseconds=(seconds*1000000) % 1000000
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60 // 1
                timestamp_optitrack.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

            #in_array = np.linspace(-10*np.pi, 10*np.pi, len(Y_optitrack.values)) 
            #Y = np.sin(in_array) 
            d={'X_pos':Y_optitrack.values}
            Df_Opti=pd.DataFrame(data=d,index=timestamp_optitrack)
            Df_Opti.index.name='Time'
            print(Df_Opti)

    return Df_Emg, Df_Opti, timestamp_emg #restituisco il dataframe contenente Emg stirato e la rispettiva frequenza di campionamento e periodo di campionamento in stringa, oltre al dataframe dell'optitrack

if (__name__ == '__main__'):
    fs_emg=1000 #frequenza di campionamento del segnale emg
    fs_optitrack=120 #frequenza di campionamento del file .fit
    rms_window_size=200 #lunghezza finestra su cui effettuare la convoluzione per calcolare l'rms

    #selezione directory contenente i file da analizzare
    file_directory =  filedialog.askdirectory(title='select a folder')
    #carico i file emg e optitrack
    Df_Emg, Df_Opti, timestamp_emg=load_data(file_directory,fs_emg) #restituisce il dataframe dei segnali Emg filtrati e dell' Optitrack
  
    #PLOT 1 grafici muscoli filtrati e optitrack
    h, ax_1 = plt.subplots(5,1, sharex=True)
    fig = plt.gcf()
    fig.canvas.set_window_title('FILTERED EMG E OPTITRACK')

    Df_Emg[Df_Emg.columns[0]].plot(ax=ax_1[0], legend=False,color='orangered')
    ax_1[0].set_title(f'{Df_Emg.columns[0]}',fontweight="bold")
    ax_1[0].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[1]].plot(ax=ax_1[1], legend=False,color='skyblue')
    ax_1[1].set_title(f'{Df_Emg.columns[1]}',fontweight="bold")
    ax_1[1].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[2]].plot(ax=ax_1[2], legend=False,color='olivedrab')
    ax_1[2].set_title(f'{Df_Emg.columns[2]}',fontweight="bold")
    ax_1[2].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[3]].plot(ax=ax_1[3], legend=False,color='sienna')
    ax_1[3].set_title(f'{Df_Emg.columns[3]}',fontweight="bold")
    ax_1[3].tick_params(labelsize=10)
    
    Df_Opti[Df_Opti.columns[0]].plot(ax=ax_1[4], legend=False,color='gold')
    ax_1[4].set_title(f'{Df_Opti.columns[0]}',fontweight="bold")
    ax_1[4].tick_params(labelsize=10)

    plt.suptitle('FILTERED SIGNALS AND OPTITRACK',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)
    
    #PLOT 2 segnali filtrati e optitrack degl'altri 4 muscoli
    h, ax_2 = plt.subplots(5,1, sharex=True)
    fig = plt.gcf()
    fig.canvas.set_window_title('FILTERED EMG E OPTITRACK')

    Df_Emg[Df_Emg.columns[4]].plot(ax=ax_2[0], legend=False,color='orangered')
    ax_2[0].set_title(f'{Df_Emg.columns[4]}',fontweight="bold")
    ax_2[0].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[5]].plot(ax=ax_2[1], legend=False,color='skyblue')
    ax_2[1].set_title(f'{Df_Emg.columns[5]}',fontweight="bold")
    ax_2[1].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[6]].plot(ax=ax_2[2], legend=False,color='olivedrab')
    ax_2[2].set_title(f'{Df_Emg.columns[6]}',fontweight="bold")
    ax_2[2].tick_params(labelsize=10)

    Df_Emg[Df_Emg.columns[7]].plot(ax=ax_2[3], legend=False,color='sienna')
    ax_2[3].set_title(f'{Df_Emg.columns[7]}',fontweight="bold")
    ax_2[3].tick_params(labelsize=10)

    Df_Opti[Df_Opti.columns[0]].plot(ax=ax_2[4], legend=False,color='gold')
    ax_2[4].set_title(f'{Df_Opti.columns[0]}',fontweight="bold")
    ax_2[4].tick_params(labelsize=10)

    plt.suptitle('FILTERED SIGNALS AND OPTITRACK',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)

    #lista che conterrà tutti gli rms
    array_rms=[]

    #PLOT 3 con RMS e cinematica
    h, ax_3 = plt.subplots(5,1, sharex=True)
    fig = plt.gcf()
    fig.canvas.set_window_title('RMS E OPTITRACK')

    rect = abs(Df_Emg[Df_Emg.columns[0]].values) #rettifico il segnale
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size) #convoluzione per calcolare l'rms
    tempo_rms= timestamp_emg[int(rms_window_size/2):-int(rms_window_size/2)+1] #tempo del segnale rms è uguale a quello emg solo tagliato all'inizio e alla fine
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms) #aggiungo alla lista l'rms del canale
    rms.plot(ax=ax_3[0],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_3[0],legend=False,color='black')
    ax_3[0].set_title(f'RMS-{Df_Emg.columns[0]}',fontweight="bold")
    ax_3[0].tick_params(labelsize=10)
    
    rect = abs(Df_Emg[Df_Emg.columns[1]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_3[1],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_3[1],legend=False,color='black')
    ax_3[1].set_title(f'RMS-{Df_Emg.columns[1]}',fontweight="bold")
    ax_3[1].tick_params(labelsize=10)

    rect = abs(Df_Emg[Df_Emg.columns[2]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_3[2],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_3[2],legend=False,color='black')
    ax_3[2].set_title(f'RMS-{Df_Emg.columns[2]}',fontweight="bold")
    ax_3[2].tick_params(labelsize=10)

    rect = abs(Df_Emg[Df_Emg.columns[3]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_3[3],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_3[3],legend=False,color='black')
    ax_3[3].set_title(f'RMS-{Df_Emg.columns[3]}',fontweight="bold")
    ax_3[3].tick_params(labelsize=10)
    
    #optitrack
    Df_Opti[Df_Opti.columns[0]].plot(ax=ax_3[4], legend=False,color='gold')
    ax_3[4].set_title(f'{Df_Opti.columns[0]}',fontweight="bold")
    ax_3[4].tick_params(labelsize=10)

    plt.suptitle('RMS AND OPTITRACK',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)

    #PLOT4 con RMS e cinematica
    h, ax_4 = plt.subplots(5,1, sharex=True)
    fig = plt.gcf()
    fig.canvas.set_window_title('RMS E OPTITRACK')

    rect = abs(Df_Emg[Df_Emg.columns[4]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_4[0],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_4[0],legend=False,color='black')
    ax_4[0].set_title(f'RMS-{Df_Emg.columns[4]}',fontweight="bold")
    ax_4[0].tick_params(labelsize=10)
    
    rect = abs(Df_Emg[Df_Emg.columns[5]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)
  
    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_4[1],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_4[1],legend=False,color='black')
    ax_4[1].set_title(f'RMS-{Df_Emg.columns[5]}',fontweight="bold")
    ax_4[1].tick_params(labelsize=10)

    rect = abs(Df_Emg[Df_Emg.columns[6]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)

    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_4[2],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_4[2],legend=False,color='black')
    ax_4[2].set_title(f'RMS-{Df_Emg.columns[6]}',fontweight="bold")
    ax_4[2].tick_params(labelsize=10)

    rect = abs(Df_Emg[Df_Emg.columns[7]].values)
    # Calcolo RMS su tutto il segnale, troncando la prima parte di caricamento del filtro
    for i in range(25):
        rect[i] = int(1)
    rms_it = window_rms(rect, rms_window_size)

    rms=pd.DataFrame(data=rms_it,index=tempo_rms)
    array_rms.append(rms)
    rms.plot(ax=ax_4[3],kind='area',legend=False,color='yellow')
    rms.plot(ax=ax_4[3],legend=False,color='black')
    ax_4[3].set_title(f'RMS-{Df_Emg.columns[7]}',fontweight="bold")
    ax_4[3].tick_params(labelsize=10)

    Df_Opti[Df_Opti.columns[0]].plot(ax=ax_4[4], legend=False,color='gold')
    ax_4[4].set_title(f'{Df_Opti.columns[0]}',fontweight="bold")
    ax_4[4].tick_params(labelsize=10)

    plt.suptitle('RMS AND OPTITRACK',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)


    #individuazione dei picchi per tagliare il segnale sull'optitrack
    Indici_picchi_optitrack=peakutils.peak.indexes(Df_Opti[Df_Opti.columns[0]],min_dist=50, thres=0.5) #calcolo dell'indice dei picchi
    #plot delle linee verticali in corrispondenza dei picchi
    for picco in Indici_picchi_optitrack:
        seconds=float(picco/fs_optitrack)
        microseconds=(seconds*1000000) % 1000000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60 // 1
        linea_verticale=datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds))
        
        ax_1[0].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_1[1].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_1[2].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_1[3].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_1[4].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)

        ax_2[0].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_2[1].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_2[2].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_2[3].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_2[4].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)

        ax_3[0].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_3[1].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_3[2].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_3[3].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_3[4].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)

        ax_4[0].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_4[1].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_4[2].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_4[3].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)
        ax_4[4].axvline(linea_verticale, color='k', linewidth=1, alpha=0.1)

    
    #lista che conterrà tutti i massimi calcolati
    massimo_0=[]
    massimo_1=[]
    massimo_2=[]
    massimo_3=[]
    massimo_4=[]
    massimo_5=[]
    massimo_6=[]
    massimo_7=[]

    id_max0=[]
    id_max1=[]
    id_max2=[]
    id_max3=[]
    id_max4=[]
    id_max5=[]
    id_max6=[]
    id_max7=[]

    #lista che conterrà tutti i minimi calcolati
    minimo_0=[]
    minimo_1=[]
    minimo_2=[]
    minimo_3=[]
    minimo_4=[]
    minimo_5=[]
    minimo_6=[]
    minimo_7=[]
    
    id_min0=[]
    id_min1=[]
    id_min2=[]
    id_min3=[]
    id_min4=[]
    id_min5=[]
    id_min6=[]
    id_min7=[]

    i=len(Indici_picchi_optitrack[:-2])
    #MAX AND MIN DETECTION
    for start, end in zip(Indici_picchi_optitrack[:-2],Indici_picchi_optitrack[1:-1]):
        start=Df_Opti.iloc[:,0].index[start] #inizio e la fine dell'intervallo considerato
        end=Df_Opti.iloc[:,0].index[end]
        min_distance=len(array_rms[0].loc[start:end ,:])
        i=i-1
        print(i)

        #indice dei picchi massimi e minimi del rms all'interno della finestra
        indici_massimo=peakutils.peak.indexes(array_rms[0].loc[start:end,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi con distanza minima pari alla finestra per trovare il massimo assoluto
        indici_minimo=peakutils.peak.indexes(-array_rms[0].loc[start:end,0].values, min_dist=min_distance,thres=0.1)
        if(len(indici_massimo)>0 and len(indici_minimo)>0): #se trovo dei massimi e dei minimi
            ax_3[0].axvline(array_rms[0].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_0.append(indici_massimo/len((array_rms[0].loc[start:end, : ])))
            id_max0.append(array_rms[0].loc[start:end,:].index[indici_massimo][0])

            ax_3[0].axvline(array_rms[0].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_0.append(indici_minimo/len((array_rms[0].loc[start:end, : ])))
            id_min0.append(array_rms[0].loc[start:end,:].index[indici_minimo][0])
        
        indici_massimo=peakutils.peak.indexes(array_rms[1].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[1].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_3[1].axvline(array_rms[1].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_1.append(indici_massimo/len((array_rms[1].loc[start:end , : ])))
            id_max1.append(array_rms[1].loc[start:end,:].index[indici_massimo][0])

            ax_3[1].axvline(array_rms[1].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_1.append(indici_minimo/len((array_rms[1].loc[start:end , : ])))
            id_min1.append(array_rms[1].loc[start:end,:].index[indici_minimo][0])

        indici_massimo=peakutils.peak.indexes(array_rms[2].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[2].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_3[2].axvline(array_rms[2].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_2.append(indici_massimo/len((array_rms[2].loc[start:end , : ])))
            id_max2.append(array_rms[2].loc[start:end,:].index[indici_massimo][0])

            ax_3[2].axvline(array_rms[2].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_2.append(indici_minimo/len((array_rms[2].loc[start:end , : ])))
            id_min2.append(array_rms[2].loc[start:end,:].index[indici_minimo][0])

        indici_massimo=peakutils.peak.indexes(array_rms[3].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[3].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_3[3].axvline(array_rms[3].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_3.append(indici_massimo/len((array_rms[3].loc[start:end , : ])))
            id_max3.append(array_rms[3].loc[start:end,:].index[indici_massimo][0])

            ax_3[3].axvline(array_rms[3].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_3.append(indici_minimo/len((array_rms[3].loc[start:end , : ])))
            id_min3.append(array_rms[3].loc[start:end,:].index[indici_minimo][0])
           
        indici_massimo=peakutils.peak.indexes(array_rms[4].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[4].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_4[0].axvline(array_rms[4].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_4.append(indici_massimo/len((array_rms[4].loc[start:end , : ])))
            id_max4.append(array_rms[4].loc[start:end,:].index[indici_massimo][0])

            ax_4[0].axvline(array_rms[4].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_4.append(indici_minimo/len((array_rms[4].loc[start:end , : ])))
            id_min4.append(array_rms[4].loc[start:end,:].index[indici_minimo][0])

        indici_massimo=peakutils.peak.indexes(array_rms[5].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[5].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_4[1].axvline(array_rms[5].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_5.append(indici_massimo/len((array_rms[5].loc[start:end , : ])))
            id_max5.append(array_rms[5].loc[start:end,:].index[indici_massimo][0])

            ax_4[1].axvline(array_rms[5].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_5.append(indici_minimo/len((array_rms[5].loc[start:end , : ])))
            id_min5.append(array_rms[5].loc[start:end,:].index[indici_minimo][0])

        indici_massimo=peakutils.peak.indexes(array_rms[6].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[6].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_4[2].axvline(array_rms[5].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_6.append(indici_massimo/len((array_rms[5].loc[start:end , : ])))
            id_max6.append(array_rms[6].loc[start:end,:].index[indici_massimo][0])

            ax_4[2].axvline(array_rms[5].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_6.append(indici_minimo/len((array_rms[5].loc[start:end , : ])))
            id_min6.append(array_rms[6].loc[start:end,:].index[indici_minimo][0])

        indici_massimo=peakutils.peak.indexes(array_rms[7].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        indici_minimo=peakutils.peak.indexes(-array_rms[7].loc[start:end ,0].values, min_dist=min_distance,thres=0.1) #calcolo dell'indice dei picchi
        if (len(indici_massimo)>0 and len(indici_minimo)>0):
            ax_4[3].axvline(array_rms[6].loc[start:end,:].index[indici_massimo][0], color='r', linewidth=1,alpha=0.3)
            massimo_7.append(indici_massimo/len((array_rms[6].loc[start:end , : ])))
            id_max7.append(array_rms[7].loc[start:end,:].index[indici_massimo][0])

            ax_4[3].axvline(array_rms[6].loc[start:end,:].index[indici_minimo][0], color='g', linewidth=1,alpha=0.3)
            minimo_7.append(indici_minimo/len((array_rms[6].loc[start:end , : ])))
            id_min7.append(array_rms[7].loc[start:end,:].index[indici_minimo][0])
        
    
    #PLOT TEMPO PERCENTUALE DI OCCORRENZA DEL MASSIMO (NORMALIZZATO RISPETTO ALLA DIMENSIONE DELLA FINESTRA)
    h, ax_5 = plt.subplots(4,2, sharex=True, sharey=True)
    fig = plt.gcf()
    
    fig.canvas.set_window_title(f'MAX')
    
    Df_massimo_0=pd.DataFrame(data=massimo_0,index=id_max0)
    Df_massimo_0.plot(ax=ax_5[0,0],color='palevioletred',legend=False)
    ax_5[0,0].set_title(f'MAX-{Df_Emg.columns[0]}',fontweight="bold")
    ax_5[0,0].tick_params(labelsize=10)
    
    Df_massimo_1=pd.DataFrame(data=massimo_1,index=id_max1)
    Df_massimo_1.plot(ax=ax_5[0,1],color='orange',legend=False)
    ax_5[0,1].set_title(f'MAX-{Df_Emg.columns[1]}',fontweight="bold")
    ax_5[0,1].tick_params(labelsize=10)

    Df_massimo_2=pd.DataFrame(data=massimo_2,index=id_max2)
    Df_massimo_2.plot(ax=ax_5[2,0],color='olivedrab',legend=False)
    ax_5[2,0].set_title(f'MAX-{Df_Emg.columns[2]}',fontweight="bold")
    ax_5[2,0].tick_params(labelsize=10)

    Df_massimo_3=pd.DataFrame(data=massimo_3,index=id_max3)
    Df_massimo_3.plot(ax=ax_5[2,1],color='sienna',legend=False)
    ax_5[2,1].set_title(f'MAX-{Df_Emg.columns[3]}',fontweight="bold")
    ax_5[2,1].tick_params(labelsize=10)

    Df_massimo_4=pd.DataFrame(data=massimo_4,index=id_max4)
    Df_massimo_4.plot(ax=ax_5[1,0],color='dodgerblue',legend=False)
    ax_5[1,0].set_title(f'MAX-{Df_Emg.columns[4]}',fontweight="bold")
    ax_5[1,0].tick_params(labelsize=10)

    Df_massimo_5=pd.DataFrame(data=massimo_5,index=id_max5)
    Df_massimo_5.plot(ax=ax_5[1,1],color='g',legend=False)
    ax_5[1,1].set_title(f'MAX-{Df_Emg.columns[5]}',fontweight="bold")
    ax_5[1,1].tick_params(labelsize=10)

    Df_massimo_6=pd.DataFrame(data=massimo_6,index=id_max6)
    Df_massimo_6.plot(ax=ax_5[3,0],color='y',legend=False)
    ax_5[3,0].set_title(f'MAX-{Df_Emg.columns[6]}',fontweight="bold")
    ax_5[3,0].tick_params(labelsize=10)

    Df_massimo_7=pd.DataFrame(data=massimo_7,index=id_max7)
    Df_massimo_7.plot(ax=ax_5[3,1],color='darkred',legend=False)
    ax_5[3,1].set_title(f'MAX-{Df_Emg.columns[7]}',fontweight="bold")
    ax_5[3,1].tick_params(labelsize=10)

    plt.suptitle(f'% tempo occorrenza picco',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)
    
    #PLOT TEMPO PERCENTUALE DI OCCORRENZA DEL MINIMO (NORMALIZZATO RISPETTO ALLA DIMENSIONE DELLA FINESTRA)
    h, ax_6 = plt.subplots(4,2, sharex=True, sharey=True)
    fig = plt.gcf()
   
    fig.canvas.set_window_title(f'MIN')
    
    Df_minimo_0=pd.DataFrame(data=minimo_0,index=id_min0)
    Df_minimo_0.plot(ax=ax_6[0,0],color='palevioletred',legend=False)
    ax_6[0,0].set_title(f'MIN-{Df_Emg.columns[0]}',fontweight="bold")
    
    Df_minimo_1=pd.DataFrame(data=minimo_1,index=id_min1)
    Df_minimo_1.plot(ax=ax_6[0,1],color='orange',legend=False)
    ax_6[0,1].set_title(f'MIN-{Df_Emg.columns[1]}',fontweight="bold")

    Df_minimo_2=pd.DataFrame(data=minimo_2,index=id_min2)
    Df_minimo_2.plot(ax=ax_6[2,0],color='olivedrab',legend=False)
    ax_6[2,0].set_title(f'MIN-{Df_Emg.columns[2]}',fontweight="bold")

    Df_minimo_3=pd.DataFrame(data=minimo_3,index=id_min3)
    Df_minimo_3.plot(ax=ax_6[2,1],color='sienna',legend=False)
    ax_6[2,1].set_title(f'MIN-{Df_Emg.columns[3]}',fontweight="bold")

    Df_minimo_4=pd.DataFrame(data=minimo_4,index=id_min4)
    Df_minimo_4.plot(ax=ax_6[1,0],color='dodgerblue',legend=False)
    ax_6[1,0].set_title(f'MIN-{Df_Emg.columns[4]}',fontweight="bold")

    Df_minimo_5=pd.DataFrame(data=minimo_5,index=id_min5)
    Df_minimo_5.plot(ax=ax_6[1,1],color='g',legend=False)
    ax_6[1,1].set_title(f'MIN-{Df_Emg.columns[5]}',fontweight="bold")

    Df_minimo_6=pd.DataFrame(data=minimo_6,index=id_min6)
    Df_minimo_6.plot(ax=ax_6[3,0],color='y',legend=False)
    ax_6[3,0].set_title(f'MIN-{Df_Emg.columns[6]}',fontweight="bold")
    ax_6[3,1].tick_params(labelsize=10)

    Df_minimo_7=pd.DataFrame(data=minimo_7,index=id_min7)
    Df_minimo_7.plot(ax=ax_6[3,1],color='darkred',legend=False)
    ax_6[3,1].set_title(f'MIN-{Df_Emg.columns[7]}',fontweight="bold")
    ax_6[3,1].tick_params(labelsize=10)
    
    plt.suptitle(f'% tempo occorrenza minimo',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)


    #PLOT difference between max and min
    duration_0 = [abs(a_i - b_i) for a_i, b_i in zip(massimo_0, minimo_0)]
    duration_1 = [abs(a_i - b_i) for a_i, b_i in zip(massimo_1, minimo_1)]
    duration_2 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_2, minimo_2)]
    duration_3 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_3, minimo_3)]
    duration_4 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_4, minimo_4)]
    duration_5 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_5, minimo_5)]
    duration_6 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_6, minimo_6)]
    duration_7 = [abs(a_i - b_i)for a_i, b_i in zip(massimo_7, minimo_7)]

    h, ax_7 = plt.subplots(4,2, sharex=True, sharey=True)
    fig = plt.gcf()
   
    fig.canvas.set_window_title(f'DIFFERENCE')
    
    Df_duration_0=pd.DataFrame(data=duration_0,index=id_min0)
    Df_duration_0.plot(ax=ax_7[0,0],color='palevioletred',legend=False)
    ax_7[0,0].set_title(f'{Df_Emg.columns[0]}',fontweight="bold")

    Df_duration_1=pd.DataFrame(data=duration_1,index=id_min1)
    Df_duration_1.plot(ax=ax_7[0,1],color='orange',legend=False)
    ax_7[0,1].set_title(f'{Df_Emg.columns[1]}',fontweight="bold")

    Df_duration_2=pd.DataFrame(data=duration_2,index=id_min2)
    Df_duration_2.plot(ax=ax_7[2,0],color='olivedrab',legend=False)
    ax_7[2,0].set_title(f'{Df_Emg.columns[2]}',fontweight="bold")

    Df_duration_3=pd.DataFrame(data=duration_3,index=id_min3)
    Df_duration_3.plot(ax=ax_7[2,1],color='sienna',legend=False)
    ax_7[2,1].set_title(f'{Df_Emg.columns[3]}',fontweight="bold")

    Df_duration_4=pd.DataFrame(data=duration_4,index=id_min4)
    Df_duration_4.plot(ax=ax_7[1,0],color='dodgerblue',legend=False)
    ax_7[1,0].set_title(f'{Df_Emg.columns[4]}',fontweight="bold")

    Df_duration_5=pd.DataFrame(data=duration_5,index=id_min5)
    Df_duration_5.plot(ax=ax_7[1,1],color='g',legend=False)
    ax_7[1,1].set_title(f'{Df_Emg.columns[5]}',fontweight="bold")

    Df_duration_6=pd.DataFrame(data=duration_6,index=id_min6)
    Df_duration_6.plot(ax=ax_7[3,0],color='y',legend=False)
    ax_7[3,0].set_title(f'{Df_Emg.columns[6]}',fontweight="bold")
    ax_7[3,0].tick_params(labelsize=10)

    Df_duration_7=pd.DataFrame(data=duration_7,index=id_min7)
    Df_duration_7.plot(ax=ax_7[3,1],color='darkred',legend=False)
    ax_7[3,1].set_title(f'{Df_Emg.columns[7]}',fontweight="bold")
    ax_7[3,1].tick_params(labelsize=10)
    
    plt.suptitle(f'absolute difference between max and min occurrence',fontweight="bold")
    plt.subplots_adjust(left  = 0.06, bottom = 0.07, right = 0.94,hspace = 0.8)
    
    plt.show()