import numpy as np
import pandas as pd
from pandas_profiling import ProfileReport
from tkinter import filedialog
import fileinput
import datetime

if __name__=="__main__":
    filename =  filedialog.askopenfilename(title='select a file')
    print(filename.split('/')[-1])
    with fileinput.FileInput(f'{filename}') as file: 
        for line in file:
            line.replace(',',';')
    #lettura file emg in un dataframe
    emgX = pd.read_csv(f'{filename}', delimiter = ';', on_bad_lines='warn'e)

    #SE CAMBIA IL TEMPLATE DELL'ACQUISIZIONE DEL SEGNALE EMG, BISOGNA VARIARE QUESTE RIGHE
    #si presuppone che il file emg sia costituito da queste variabili!!! converto da stringhe a variabili numeriche
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
    t0 = emgX[emgX.columns[0]].min() #tempo iniziale
    m = emgX[emgX.columns[0]].notnull() #vettore booleano, True dove ci sono dei valori, False dove ci sono nan
    #aggiungo una colonna t_int che conterrà il tempo espresso in secondi
    emgX.loc[m, 't_int'] = (emgX.loc[m, emgX.columns[0]] - t0).dt.total_seconds()
    #interpolo i nan della colonna timestamp
    emgX[emgX.columns[0]] = t0 + pd.to_timedelta(emgX.t_int.interpolate(), unit='s')
    #sottraggo il primo valore del timestamp per far partire l'acquisizione al tempo 0
    t_seconds=[date-emgX[emgX.columns[0]][0] for date in emgX[emgX.columns[0]]] 

    #ciclo per convertire t_seconds che è in formato datetime.timedelta nel formato datetime.time
    #che ci permette la visualizzazione degli assi
    timestamp_emg=[]
    for duration in t_seconds:
        seconds = duration.total_seconds()
        microseconds=(seconds*1000000) % 1000000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60 // 1
        timestamp_emg.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

    #le prime tre colonne sono timestamp, stream_ID e sequence le altre i muscoli
    #interpolo linearmente i NaN dei canali                    
    emgX[emgX.columns[3]]=emgX[emgX.columns[3]].interpolate(limit_direction='both')
    emgX[emgX.columns[4]]=emgX[emgX.columns[4]].interpolate(limit_direction='both')
    emgX[emgX.columns[5]]=emgX[emgX.columns[5]].interpolate(limit_direction='both')
    emgX[emgX.columns[6]]=emgX[emgX.columns[6]].interpolate(limit_direction='both')
    emgX[emgX.columns[7]]=emgX[emgX.columns[7]].interpolate(limit_direction='both')
    emgX[emgX.columns[8]]=emgX[emgX.columns[8]].interpolate(limit_direction='both')
    emgX[emgX.columns[9]]=emgX[emgX.columns[9]].interpolate(limit_direction='both')
    emgX[emgX.columns[10]]=emgX[emgX.columns[10]].interpolate(limit_direction='both')
    
    emgX[emgX.columns[3]] = emgX[emgX.columns[3]].astype('int64')
    emgX[emgX.columns[4]] = emgX[emgX.columns[4]].astype('int64')
    emgX[emgX.columns[5]] = emgX[emgX.columns[5]].astype('int64')
    emgX[emgX.columns[6]] = emgX[emgX.columns[6]].astype('int64')
    emgX[emgX.columns[7]] = emgX[emgX.columns[7]].astype('int64')
    emgX[emgX.columns[8]] = emgX[emgX.columns[8]].astype('int64')
    emgX[emgX.columns[9]] = emgX[emgX.columns[9]].astype('int64')
    emgX[emgX.columns[10]] = emgX[emgX.columns[10]].astype('int64')
    
    #CREAZIONE DATAFRAME RAW
    #colonne contenenti solo i nomi dei muscoli, non interssa stream_id, sequence e timestamp 
    #(l'ultima colonna (t_int) non la considero perchè è quella che ho creato per interpolare il tempo)
    Df_Emg_Raw=emgX.iloc[:,3:-1]
    #assegno il timestamp determinato all'indice del dataframe dell'Emg Raw
    Df_Emg_Raw.index=timestamp_emg
    print('FILE EMG LOADED')
    
    profile = ProfileReport(Df_Emg_Raw, title='Pandas Profiling Report')
    profile.to_file('profile_report.html')