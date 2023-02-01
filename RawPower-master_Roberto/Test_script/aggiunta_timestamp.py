#script per aggiungere la colonna del timestamp, ai file acquisiti senza, utilizzando l'optitrack

import pandas as pd
import numpy as np
import csv
import fileinput
from tkinter import filedialog
import os
import datetime

def load_workout():
    #lettura files, carica al massimo un file emg, lattato, fit e optitrack, 
    #per evitare possibili ambiguità all'interno della folder ci deve essere un solo file per tipo di registrazione
    file_directory =  filedialog.askdirectory(title='select a folder') #selezione della directory contetnte il workout 
    for filename in os.listdir(file_directory): #ciclo sui file presenti nella directory
        if filename.endswith('.csv'): #controllo se il file è un .csv (potrà essere un file emg, lattato o optitrack)
            f = open(f'{file_directory}/{filename}', 'r') #apro il file e leggo l'header
            reader = csv.reader(f)
            headers = next(reader, None)
            
            if(headers[0].split(';')[0]=='STREAM_ID'): 
                file_path=f'{file_directory}/{filename}'
                print(filename) 
                #nel caso in cui il file abbia il sepratore ',' viene convertito in ';' per standardizzare il formato
                with fileinput.FileInput(f'{file_directory}/{filename}') as file: 
                    for line in file:
                        line.replace(',',';')
                #lettura file emg in un dataframe
                emgX = pd.read_csv(f'{file_directory}/{filename}', delimiter = ';', on_bad_lines='warn')

            if(headers[0].split(';')[0]=='Format Version'): 
                    optitrack = pd.read_csv(f'{file_directory}/{filename}', delimiter = ',',header=[1,2,3,4,5], on_bad_lines='warn')
    return emgX,optitrack,file_path

if __name__ == "__main__":
    Df_Emg,Df_Opti,file_path=load_workout()
    Df_Emg.insert(loc=0, value=np.nan, column ='TIMESTAMP')
    Df_Emg.iloc[0,0]=datetime.time(second=0)
    seconds=Df_Opti.iloc[-1,1]
    microseconds=(seconds*1000000) % 1000000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60 // 1
    Df_Emg.iloc[-1,0]=datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds))
    filename=file_path.split('.csv')[0]
    filename=filename + '_modify.csv'
    Df_Emg.to_csv(filename,sep=';',na_rep=np.nan,index=False)