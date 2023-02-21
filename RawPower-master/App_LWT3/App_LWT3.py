#APPLICAZIONE RAW_POWER!


'''Cosa ho  SISTEMATO

    Ho commentato tutti i 'set_window_title' dei plot perchè non lo riconosceva come attributo del canvas Riiisoltooo: era deprecato bisogna usare canvas.manager.set_window_title

'''

#import library
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

import pandas as pd 
import numpy as np 
import math

import scipy as sp 
from scipy import signal

import tkinter as tk 
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing

import peakutils

import csv

import os
import inspect
import fileinput

import time
import datetime

from functools import partial
import multiprocessing #processo per mostrare le barre di progresso
import threading #thread per controllare quali figure sono visibli
import sys

#import serial 
#import pyserial as serial
import serial.tools.list_ports #utilizzata per elencare le porte COM disponibili
#from serial.tools import list_ports

#importo il CustomNotebook per avere le tab con la possibilità di essere chiuse
from Notebook.CustomNotebook import CustomNotebook

#importo le FEATURES
from Features.features import *

#importo il Menubar e la Statusbar
from Configuration.ConfigRawpower import Menubar, Statusbar

#importo funzioni di pre-processing
from PreProcessing.processing import butter_bandpass, butter_bandpass_filter, Implement_Notch_Filter

#importo funzioni per leggere file .fit
from Fit.fit import open_fit

#importo funzione per andare ad esportare i dati in un file .csv
from Export.export import export_excel, export_all_rms_excel

#importo la funzione per mostrare la barra di progresso
from ProgressBar.progress_bar import show_progress_bar

#import per effettuare una nuova acquisizione
from Acquisition.Gui import Acquisition_app

#disabilitazione warnings
#import warnings
#warnings.filterwarnings("ignore")

#libreria seaborn per gestire lo stile dei plot
import seaborn as sns
sns.set()

#funzioni utilizzate per il calcolo delle features in parallel processing
def function(func,th,x):
    return func(x,th)

def function_spectrum(func,fs_emg,x):
    f, p = signal.welch(x,fs_emg)
    return func(f,p)

#funzione per cambiare il colore di un item del menù
def change_item_color(menu,id_label):
    """
    changes color of specified menu item

    Args:
        menu (tk.Menu): menu
        id_label (int): menu item identifier
    """
    last=menu.index('end') #number of items
    for i in range(last+1):
        if i == id_label:
            menu.entryconfig(i,background='#DCDCDC',foreground='red') #change color of the specified item
        else:
            menu.entryconfig(i,background='#DCDCDC',foreground='black') #all other items become black

#funzione per convertire il tempo in hh:mm:ss
def time_convert(vect):
    """converts time expressed in seconds, in format %H:%M:%S

    Args:
        vect (array_like): time instants in seconds

    Returns: 
        list of strings: time in format %H:%M:%S
    """

    tempo=[]
    for i in vect:
        date_string=time.strftime(f'%H:%M:%S',time.gmtime(i))
        tempo.append(date_string)
    return tempo

##########################################################################################################################################
#############################             CREAZIONE DELL'APPLICAZIONE SOTTO FORMA DI CLASSE           ####################################
##########################################################################################################################################
##########################################################################################################################################
##########################################################################################################################################
#Definizione della classe che si occupa di gestire l'appilcazione e le funzioni associate ai tasti del menù


class Application:
    """controls main application 
    """
    #INIZIALIZZAZIONE
    def __init__(self,master): #il parametro master è la finestra generata con tkinter        
        #CARATTERISTICHE GEOMETRICHE E DI LAYOUT
        self.master=master #tkinter.TK()
        self.master.title("LWT3 RawPower - ROBERTO") #titolo della finestra
        #geometria finestra centrata
        w = 1280 # width for the Tk self
        h = 720 # height for the Tk self

        # get screen width and height
        ws = self.master.winfo_screenwidth() # width of the screen
        hs = self.master.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk self window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        self.master.geometry(f'{w}x{h}+{int(x)}+{int(y)}')

        #ICONA
        self.master.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')

        #OPERAZIONI ALLA CHIUSURA
        self.master.protocol("WM_DELETE_WINDOW", self.close)
        
        #INIZIO TAB home
        self.tabControl = CustomNotebook(self,self.master) # Create Tab Control
        self.tab_home = ttk.Frame(self.tabControl) # Create a tab 
        self.tabControl.add(self.tab_home, text='home') # Add the tab
        self.tabControl.pack(expand=1, fill="both")  # Pack to make visible
        
        #aggiunta immagine iniziale
        #self.img_path=os.path.abspath(os.path.join(__file__, '..','LWT3.jpg')) #path dell'immagine da caricare
        #self.img=ImageTk.PhotoImage(Image.open(self.img_path)) #immagine iniziale

        # SPOSTARE L'IMMAGINE ALL'INTERNO DELLA CARTELLA!

        self.img_path='C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\RawPower-master_Roberto\App_LWT3\LWT3.jpg'
        #self.img_path='C:\\Users\\rales\OneDrive\Desktop\LWT3\RawPower\RawPower\App_LWT3\LWT3.jpg'

        self.img=ImageTk.PhotoImage(Image.open(self.img_path)) #immagine iniziale
        self.img_display= tk.Label(self.tab_home,bg='black',image=self.img) #creo una label in cui inserisco l'immagine caricata
        self.img_display.place(x=0, y=0, relwidth=1, relheight=1)
        #FINE TAB home

        #INIZIO TAB Editor
        self.check_tab_editor=False #inizialmente la tab_editor non è presente
        #inizialmente la variabile che descrive se scrivere l'header delle features nell'editor è True
        self.first_feature=True #variabile che serve a determinare se scrivere l'header o meno nell'editor quando si calcolano le fatures
        #FINE TAB Editor

        self.title_emg="Untitled" #variabile che mostra sulla status bar il nome del file emg
        self.title_optitrack="None" #variabile che mostra sulla status bar il nome del file optitrack se è stato aperto
        self.muscle_name="None"  #variabile che conterrà il nome del muscolo under investigation

        #INIZIALIZZAZIONE FREQUENZE DI CAMPIONAMENTO
        self.fs_emg = 1000.0 #frequenza di campionamento EMG (verrà comunque detrminata automaticamente all'apertura del file EMG)
        self.fs_optitrack=120.0 #frequenza di campionamento optitrack
        self.fs_fit=1 #frequenza di campionamento segnali .Fit

        #INIZIALIZZAZIONE PARAMETRI FILTRO
        self.lowcut = 30.0 #inizializzazione frequenza taglia basso
        self.highcut = 499.9 #inizializzazione frequenza taglia alto (verrà comunque detrminata automaticamente all'apertura del file EMG)
        self.order=5 #ordine del filtro di butterworth

        self.default_low = 30.0 #inizializzazione frequenza taglia basso utilizzata per ripristinare i valori di default
        self.default_high = 499.9 #inizializzazione frequenza taglia alto utilizzata per ripristinare i valori di default
        self.default_order = 5 #ordine del filtro di butterworth utilizzata per ripristinare i valori di default

        #variabili utilizzate per testare nuovi parametri del filtro
        self.test_lowcut = 30.0 #inizializzazione frequenza taglia basso di test
        self.test_highcut = 499.9 #inizializzazione frequenza taglia alto di test
        self.test_order=5 #ordine del filtro di butterworth di test

        #INIZIALIZZAZIONE PARAMETRI PER IL CALCOLO DELLE FEATURES
        self.rms_window_size=200 #numero di campioni su cui effettuare la convoluzione per il calcolo del RMS
        self.window_size=0.500 #inizializzazione lunghezza finestra per il calcolo delle features (espresso in secondi)
        self.overlap=0.125 #inizializzazione overlapping tra finestre per il calcolo delle features (espresso in secondi)
        self.th=0.1 # threshold per il calcolo di alcune features, SARA' DA IMPOSTARE IN BASE AL RANGE MASSIMALE DEL SOGGETTO
        self.TMNF=30 #periodo di campionamento della MNF in sec (un valore di MNF ogni self.TMNF)
        self.Tfinestra=30 #intorno del punto considerato, in secondi e centrato, per il calcolo della MNF (la MNF verrà calcolata su un segmento pari a self.Tfinestra secondi)
        
        #INIZIALIZZAZIONE MENUBAR E STATUSBAR
        self.statusbar=Statusbar(self) #creazione statusbar
        self.menubar=Menubar(self) #creazione menù
        self.array_nome_muscoli=[] #lista che verrà popolata con i nomi dei muscoli della prova che sarà caricata

        #INIZIALIZZAZIONI TOP LEVEL 
        self.help_window=None #finestra dell'help inizialmente non è presente, si aprirà alla pressione del tasto help->about
        self.frequency_setting=None #finestra per confermare il settaggio dei parametri del filtro, si aprirà alla pressione del tasto apply della finestra self.window_filter
        self.window_filter=None #finestra per il settaggio dei parametri del filtro, si aprirà alla pressione del tasto filter settings
        self.acquisition_window=None #finestra che serve per acquisire una nuova registrazione
        self.features_settings_gui=None #finestra per settare le caratteristiche per il calcolo delle features

        #INIZIALIZZAZIONE FIGURA PER IL PLOT DEL SEGNALE FILTRATO SU CUI CALCOLARE LE FEATURES E MOSTRARLE NELL'EDITOR
        self.fig_compute=None #variabile che conterrà la figura in cui verrà mostrato il segnale su cui calcolare le features
        self.text_content='' #variabile che conterrà ciò che verrà scritto nell'editor (inizialmente è vuota)
        self.textarea=None #editor in cui andare a scrivere le features calcolate (inizialmente è chiuso)

        #INIZIALIZZAZIONE VARIABILI PER PLOT SINGLE CHANNEL
        self.number_of_channels=8
        self.check_tab_channel=[False]*self.number_of_channels #lista che conterrà le eventuali tab per mostrare i plot generati alla pressione dei tasti contenuti nel menù 'muscles' (8 possibili tab diverse)
        self.tab_channel=[None]*self.number_of_channels #lista che conterrà le eventiali tab per mostrare i plot single channel
        self.id_single_channel=np.zeros(self.number_of_channels,dtype=int) #lista che contiene l'id della figura da mostrare per i diversi canali (all'apertura di una delle tab contenute in self.tab_channel, verrà mostrata la figura con id=0, all'interno della lista self.ar_fig)
        self.canvas_single_channel=[None]*self.number_of_channels #lista che conterrà le eventuali canvas per mostrare i grafici generati alla pressione dei tasti del menù 'muscles'
        self.toolbar_single_channel=[None]*self.number_of_channels #lista che conterrà le eventuali toolbar dei grafici generati alla pressione dei tasti del menù 'muscles'
        self.single_channel_plot_selection=[None]*self.number_of_channels #lista che conterrà i combobox per la selezione del plot da mostrare all'interno di una delle tab presenti in sel.tab_channel
        self.single_channel_available_plot=['SMOOTHED','SPECTROGRAM','PSD','FEATURES'] #all'interno delle tab presenti in self.tab_channel ci saranno almeno questi grafici
        self.change_features_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per cambiare la feature mostrata nel grafico 'FEATURES' all'interno delle tab presenti in self.tab_channel
        self.change_BLE_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per selezionare gli eventuali BLE nel grafico 'BLE' all'interno delle tab presenti in self.tab_channel (se sono presenti dispositivi BLE)
        self.change_opti_feature_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per selezionare le features dell' optitrack in self.tab_channel 
        self.list_available_features=['MAV','RMS','IEMG','VAR','WL','SSC','WAMP','ZC','MNF','MDF'] #lista contenente tutte le features disponibili
        self.list_Df_features=[None]*self.number_of_channels #lista che conterrà i dataframe delle features di tutti i canali
        self.fig_coerence=[None]*self.number_of_channels #lista che conterrà le eventuali figure di coerenza tra i segnali (grafico 'RAW')
        self.fig_PSD=[None]*self.number_of_channels #lista che conterrà le eventuali figure dei PSD (grafico 'PSD')
        self.fig_spectrogram=[None]*self.number_of_channels #lista che conterrà le eventuali figure degli spettrogrammi (grafico 'SPECTROGRAM')
        self.fig_features=[None]*self.number_of_channels #lista che conterrà le eventuali figure delle features (grafico 'FEATURES')

        #INIZIALIZZAZIONI VARIABILI PER PLOT ALL CHANNELS
        self.check_tab_all_channels=False #tab per mostrare i plot geneari alla pressione del tasto 'all_channels'
        self.ar_fig_all=[] #lista che conterrà tutte le figure da mostrare, generate alla pressione del tasto 'all_channels'
        self.available_all_channels_plot=["FILTERED EMG","RMS","SPECTROGRAM","PSD","MNF"] #lista contenente tutti i plot disponibili all_channels

        #INIZIALIZZAZIONI VARIABILI PER PLOT FATIGUE
        self.check_tab_fatigue=False #tab per mostrare i plot geneari alla pressione del tasto 'fatigue analysis'
        self.ar_fig_fatigue=[] #lista che conterrà tutte le figure da mostrare, generate alla pressione del tasto 'fatigue analysis' (saranno self.number_of_channels figure, una per ogni canale)
        self.axfatigue =[[None]*3]*self.number_of_channels #lista che contiene delle liste di assi (3 assi per self.number_of_channels canali)

        #INIZIALIZZAZIONE VARIABILI BOOLEANE PER DESCRIVERE LA PRESENZA DEI FILE
        self.check_emg=False #variabile che diventerà vera quando e se si caricherà il file .emg
        self.check_fit=False #variabile che diventerà vera quando e se si caricherà il file .fit
        self.check_lattato=False #variabile che diventerà vera quando e se si caricherà il file lattato
        self.check_opti=False #variabile che diventerà vera quando e se si caricherà il file optitrack
        self.check_BLE=False #variabile che diventerà vera quando e se si caricherà almeno un file .csv di un dispositivo BLE
        self.list_DF_BLE=[] #lista che conterrà i dataframe dei singoli BLE
        self.Df_BLE=pd.DataFrame() #empty dataframe al quale verranno aggiunte le informazioni in base al numero di dati provenienti dai dispositivi BLE

        #INIZIALIZZAZIONI VARIABILI PER CSV EXPORT
        self.Df_export = None #variabile che conterrà i dati da esportare in .csv (MNF e eventualmente .fit)
        
        #INIZIALIZZAZIONE VARIABILI PER MOSTRARE LA BARRA DI PROGRESSO
        self.progressbar_process=None #process che verrà attivato quando verranno mostrate le barre di progresso
        self.start_stop_event=multiprocessing.Event() #variabile per gestire il sincronismo tra i processi

        #INIZIALIZZAZIONE VARIABILI PER SALVARE IL REPORT GENERATO CON PANDAS PROFILING
        self.report_process=None #process che verrà attivato quando verrà salvato il report
        self.finish_report=multiprocessing.Event() #variabile per gestire il sincronismo tra i processi
    #FINE INIZIALIZZAZIONE

    def new_acquisition(self):
        """
        starts recording a new acquisition
        """
        ports = list(serial.tools.list_ports.comports()) #lista delle porte COM <- se non è attaccato nulla non va
        #seleziono solamente le COM collegate ad un dispositivo seriale
        porte_com=[]
        for p in ports:
            if(str(p).split('-')[-1].split('(')[0] in [' USB Serial Device ',' Dispositivo seriale USB ']): #se le com sono collegate ad un dispositivo seriale
                porte_com.append(str(p).split(' ')[0])

        if len(porte_com)>0: #controllo se è collegata almeno una porta COM seriale
            #quando effettuo una nuova acquisizione disabilito il menù dell'applicazione, per impedire altre esecuzioni
            self.menubar.menubar.entryconfigure("File",state="disabled")
            self.menubar.menubar.entryconfigure("Muscles",state="disabled")
            self.menubar.menubar.entryconfigure("Plot",state="disabled")
            self.menubar.menubar.entryconfigure("Settings",state="disabled")
            self.menubar.menubar.entryconfigure("Help",state="disabled")
            self.master.protocol("WM_DELETE_WINDOW", lambda: None) #quando è aperta la GUI di registrazione non è possibile chiudere la main window
            
            #apro l'applicazione per registrare e finchè non viene chiusa blocca l'applicazione principale
            self.acquisition_window=tk.Toplevel(master=self.master) 
            Acquisition_app(self.acquisition_window)
            #blocca l'applicazione principale finchè non viene chiusa
            self.acquisition_window.transient(self.master)
            self.acquisition_window.grab_set()
            self.master.wait_window(self.acquisition_window)

            #quando l'applicazione di registrazione viene chiusa abilito nuovamente il menù
            self.master.protocol("WM_DELETE_WINDOW", self.close) #quando chiudo la GUI di registrazione è possibile chiudere anche la main window
            self.menubar.menubar.entryconfigure("File",state="normal")
            self.menubar.menubar.entryconfigure("Help",state="normal")
            if self.check_emg: #se era stato caricato un workout abilito anche i menù Muscles, Plot e Settings
                self.menubar.menubar.entryconfigure("Muscles",state="normal")
                self.menubar.menubar.entryconfigure("Plot",state="normal")
                self.menubar.menubar.entryconfigure("Settings",state="normal")
            else: #se non era stato caricato un workout, vado a disabilitare la possibilità di esportare il file csv
                self.menubar.file_dropdown.entryconfigure('Export .xlsx',state='disabled')
                self.menubar.file_dropdown.entryconfigure("Export rms", state="disabled")
        else:
        #     #se non ci sono delle porte aperte mostro un popup
            tk.messagebox.showerror(title='DEVICE ERROR',message='No device available')

    def create_dataframes(self,only_DF_MNF):
        """creates a dataframe containing filtered Emg signals (Df_Emg_Filtered), a dataframe containing smoothed signals (Df_Savitzky) a dataframe containing RMS signals (Df_RMS) and a datafreme containing MNF signals (Df_MNF)
        
        Args:
            only_DF_MNF(bool): if True only Df_MNF will be compute otherwise Df_Emg_Filtered, Df_RMS, Df_Savitzky and Df_MNF will be computed 
        """
        self.Df_export = None #ogni volta che viene chiamata la funzione create dataframes self.Df_export (variabile per esportare i dati in .csv) diventa None perchè deve essere aggiornata

        if not only_DF_MNF: #se devo aggiornare tutti i dataframes
            #CALCOLO DF SEGNALI FILTRATI
            #applicazione filtro passa panda e di notch su ogni colonna (canale) del dataframe Raw
            self.Df_Emg_Filtered=self.Df_Emg_Raw.apply(lambda x: Implement_Notch_Filter(self.fs_emg,1,50, None, 3, 'butter', 
                                                butter_bandpass_filter(x,self.lowcut,self.highcut, self.fs_emg, order=self.order)))

            #CALCOLO DF SAVITZKY
            def df_Sav(vect):
                rect = abs(vect.values)
                # FIltro di Savitzky-Golay per test smoothing
                return np.absolute(sp.signal.savgol_filter(rect,161,4))
            
            self.Df_Savitzky=self.Df_Emg_Filtered.apply(lambda x: df_Sav(x))

            #CALCOLO DF SEGNALI RMS
            def df_rms(vect):
                rect=abs(vect.values)
                for i in range(25):
                    rect[i]=int(1)
                return window_rms(rect,self.rms_window_size)

            #applicazione della funzione df_rms su ogni colonna (canale) del dataframe contente i segnali filtrati
            self.Df_RMS=self.Df_Emg_Filtered.apply(lambda x: df_rms(x))
            
            #tempo del segnale rms è uguale a quello emg solo tagliato all'inizio e alla fine per via della convoluzione 'valid'
            #il primo campione del RMS è stato assegnato a metà della prima finestra
            tempo_rms= self.timestamp_emg[int(self.rms_window_size/2):-int(self.rms_window_size/2)+1] 

            for i in range(len(self.Df_RMS.columns)):
               self.Df_RMS.rename(columns = {f'{self.Df_RMS.columns[i]}' : f'RMS_{self.Df_RMS.columns[i]}'}, inplace = True)
            #assegno il timestamp all'indice del dataframe RMS
            self.Df_RMS.index=tempo_rms
            print("self.Df_RMS = \n", self.Df_RMS)
            print("\nself.Df_Emg_Filtered = \n", self.Df_Emg_Filtered)


        def compute_MNF(filter_dato):
            """
                computes MNF

                Args:
                    filter_dato (array_like): Emg filter data

                Returns: 
                    np.array: MNF values
                    list of datetime.time: MNF sampling time
                    list of int: MNF sampling time in seconds
            """
            #plot MNF
            rect = abs(filter_dato)
            MNF_it,seconds_MNF = window_MNF(rect,self.TMNF,self.Tfinestra,self.fs_emg)
            tempo_MNF=[]
            #converto la variabile seconds_MNF in una lista di datetime.time
            for seconds in seconds_MNF:
                microseconds=(seconds*1000000) % 1000000
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60 // 1
                tempo_MNF.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))
            
            return MNF_it, tempo_MNF, seconds_MNF

        #calcolo MNF di ogni canale
        MNF_it=[]
        for i in range(len(self.Df_Emg_Filtered.columns)):
            MNFi_it, tempo_MNF, self.seconds_MNF = compute_MNF(self.Df_Emg_Filtered.iloc[:,i])
            MNF_it.append(MNFi_it)

        #creazione dataframe MNF
        MNFs={}
        for mnf,i in zip(MNF_it,range(len(MNF_it))):
            MNFs[f'MNF_{self.array_nome_muscoli[i]}']=mnf

        #MNF dataframe
        self.Df_MNF = pd.DataFrame(data=MNFs, index=tempo_MNF)
    #FINE METODO create_dataframes

    def load_pca_file(self):
        """
        open files .csv from a select folder, which first column is TIME and compute PCA analiysis. It plots 2d and 3d both for Score Plots and Biplots
        """

        csv_found = False   #se non viene trovato nessun file .csv nella directory selezionata
        TIME_as_first_column=False  #se viene trovato un file .csv nella directory MA la prima colonna NON è 'TIME'
        file_encoded = False    #se il file .csv ha come prima colonna 'ï»¿TIME', il che significa che è salvato con encoding UTF-8

        in_dir=os.path.expanduser('~\\OneDrive - Politecnico di Milano\Documenti\Recordings')
        if not (os.path.isdir(in_dir)):
            os.mkdir(in_dir)
        #file_directory=askopendirname(title='select folder',initialdir=f'{in_dir}')
        file_directory=filedialog.askdirectory(title='select folder',initialdir=f'{in_dir}')

        if len(file_directory)>0: #se è stata selezionata una directory
            #ciclo per controllare se all'interno della cartella è presente un file EMG
            for filename in os.listdir(file_directory): #ciclo sui file presenti nella directory
                if filename.endswith('.csv'): #controllo se il file è un .csv (potrà essere un file emg, lattato, optitrack o BLE)
                    csv_found = True
                    f = open(f'{file_directory}/{filename}', 'r') #apro il file e leggo l'header
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    print('ENTERED HEADER:  ', headers)
                    #se è presente un file il cui il primo valore dell'header è 'TIME' (caratteristico dell'export MNF)
                    if(headers[0].split(';')[0]=='TIME'): #si può rendere più univoco
                        TIME_as_first_column=True
                        with fileinput.FileInput(f'{file_directory}/{filename}') as file: 
                            for line in file:
                                line.replace(',',';')

                        #lettura file emg in un dataframe
                        df_PCA = pd.read_csv(f'{file_directory}/{filename}', delimiter = ',', on_bad_lines='warn')      #ATTENZIONE: , OPPURE ; ????

                        df_PCA.drop(columns=['TIME'], inplace=True)
                        df_PCA = df_PCA.rename(columns=str.upper)
                        target_variable=False  #specifica se è una PCA con o senza target variable

                        for column in df_PCA.columns:
                            if(column == 'TARGET'):
                                target_variable = True
                                target_class = df_PCA['TARGET'].to_numpy()

                        features = df_PCA.loc[:, df_PCA.columns != 'TARGET']    #df without any other column, just muscles data
                        df_transf = StandardScaler().fit_transform(features)
                        pca = PCA()
                        pca_out = pca.fit(df_transf)
                        loadings = pca_out.components_
                        num_pc = pca_out.n_features_
                        pc_list = ['PC' + str(x) for x in range(1, num_pc+1)]

                        loadings_df = pd.DataFrame.from_dict(dict(zip(pc_list, loadings)))
                        loadings_df['variable'] = features.columns.values
                        loadings_df = loadings_df.set_index('variable')

                        pca_out.explained_variance_
                        # get scree plot (for scree or elbow test)
                        from bioinfokit.visuz import cluster
                        #cluster.screeplot(obj=[pc_list, pca_out.explained_variance_ratio_])

                        #PCA con target variable
                        if(target_variable):
                            pca_scores=PCA().fit_transform((features))
                            cluster.biplot(cscore=pca_scores, loadings=loadings, labels=df_PCA.columns.values, show=True, var1=round(pca_out.explained_variance_ratio_[0]*100, 2),
                                var2=round(pca_out.explained_variance_ratio_[1]*100, 2), colorlist=target_class)
                        #PCA senza target variable
                        else:
                            #PCAPLOT 3d
                            cluster.pcaplot(x=loadings[0], y=loadings[1], z=loadings[2], labels=df_PCA.columns.values, show=True,
                                var1=round(pca_out.explained_variance_ratio_[0]*100, 2),
                                var2=round(pca_out.explained_variance_ratio_[1]*100, 2),
                                var3=round(pca_out.explained_variance_ratio_[2]*100, 2))

                            #PCAPLOT 2d
                            cluster.pcaplot(x=loadings[0], y=loadings[1], labels=df_PCA.columns.values, show=True,
                                var1=round(pca_out.explained_variance_ratio_[0]*100, 2),
                                var2=round(pca_out.explained_variance_ratio_[1]*100, 2))

                            #BIPLOT 3d
                            pca_scores = PCA().fit_transform(df_transf) #get pca scores
                            cluster.biplot(cscore=pca_scores, loadings=loadings, labels=df_PCA.columns.values, show=True,
                                var1=round(pca_out.explained_variance_ratio_[0]*100, 2),
                                var2=round(pca_out.explained_variance_ratio_[1]*100, 2),
                                var3=round(pca_out.explained_variance_ratio_[2]*100, 2))

                            #BIPLOT 2d
                            pca_scores = PCA().fit_transform(df_transf) #get pca scores
                            cluster.biplot(cscore=pca_scores, loadings=loadings, labels=df_PCA.columns.values, show=True,
                                var1=round(pca_out.explained_variance_ratio_[0]*100, 2),
                                var2=round(pca_out.explained_variance_ratio_[1]*100, 2))
                    elif(headers[0].split(';')[0]=='ï»¿TIME'):
                        file_encoded=True
            if(not csv_found):
                tk.messagebox.showerror(title='LOAD ERROR',message='Did not found any .csv file')
            elif(file_encoded):
                tk.messagebox.showerror(title='LOAD ERROR',message='The file is saved as .csv but encoded with UTF-8. Save it without encoding please.')
            elif(not TIME_as_first_column):
                tk.messagebox.showerror(title='LOAD ERROR',message='Among all the .csv files, there is not a file which the first column is TIME. That is needed to do PCA.')


    def load_workout(self,*args):
        """
        opens files (emg, .fit, optitrack, lattato and BLE) from a select folder, if any
        """
        self.start_loading=False #start loading inizialmente è False, diventerà True se nella directory sarà presente un file con le caratteristiche del file EMG
        self.check_all_channels_disconnected=False #variabile che indica che tutti i canali erano disconnessi
        in_dir=os.path.expanduser('~\\OneDrive - Politecnico di Milano\Documenti\Recordings')
        if not (os.path.isdir(in_dir)):
            os.mkdir(in_dir)
        #file_directory=askopendirname(title='select folder',initialdir=f'{in_dir}')
        file_directory=filedialog.askdirectory(title='select folder',initialdir=f'{in_dir}')

        if len(file_directory)>0: #se è stata selezionata una directory
            #ciclo per controllare se all'interno della cartella è presente un file EMG
            for filename in os.listdir(file_directory): #ciclo sui file presenti nella directory
                if filename.endswith('.csv'): #controllo se il file è un .csv (potrà essere un file emg, lattato, optitrack o BLE)
                    f = open(f'{file_directory}/{filename}', 'r') #apro il file e leggo l'header
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    #se è presente un file il cui il primo valore dell'header è 'TIMESTAMP' (caratteristico della registrazione emg)
                    if(headers[0].split(';')[0]=='TIMESTAMP'): #si può rendere più univoco
                        use_columns=list(filter(lambda a: a != 'Unspecified',headers[0].split(';')))
                        use_columns=list(filter(lambda a: a != ' Not  Connected ',use_columns))         # !attenzione al doppio spazio in Not  Connected!
                        use_columns=list(filter(lambda a: a != ' Not  used ',use_columns))
                        use_columns=list(filter(lambda a: a != 'LAP', use_columns))
                        if len(use_columns)==3: #timestamp,stream_id,sequence
                            self.start_loading=False #la variabile diventa False, tutti i canali erano scollegati
                            self.check_all_channels_disconnected=True #variabile che indica che tutti i canali erano disconnessi
                        else:
                            self.start_loading=True #la variabile diventa True, ovvero posso incominciare a caricare i file
                            self.number_of_channels=len(use_columns)-3 #numero di canali utilizzati
                            #self.number_of_channels=8

            if self.start_loading: #se è presente almeno il file EMG incomincio  a caricare i file
                self.file_directory=file_directory #variabile contenente il path della directory
                
                #chiudo tutte le tab aperte
                try:
                    self.tabControl.forget(self.tab_editor) #chiudo la tab se è presente
                    self.check_tab_editor=False #metto a false la variabile che indica la presenza della tab
                except Exception as e: #la tab non era presente
                    self.check_tab_editor=False #metto comunque a false che indica la presenza della tab
                
                try:   
                    self.tabControl.forget(self.tab_all_channels) #chiudo la tab se è presente
                    self.check_tab_all_channels=False
                    
                    #cerco di liberare il più possibile la memoria
                    for i in range(len(self.ar_fig_all)):
                        plt.figure(self.ar_fig_all[i].number).clear()
                        plt.close(self.ar_fig_all[i]) #chiudo le figure

                    self.ar_fig_all=[] #reinizializzo l'array
                    self.canvas_all_channels.get_tk_widget().pack_forget()
                    self.canvas_all_channels.get_tk_widget().destroy()
                    self.toolbar_all_channels.pack_forget()
                    self.toolbar_all_channels.destroy()
                    self.all_channels_plot_selection.destroy()              

                    self.all_channels_plot_selection=None
                    self.tab_all_channels = None #reinizializzo a None la tab
                
                    self.check_tab_all_channels=False
                    self.canvas_all_channels=None
                    self.toolbar_all_channels=None
                except Exception as e:
                    self.check_tab_all_channels=False

                try:
                    self.tabControl.forget(self.tab_fatigue) #chiudo la tab se è presente
                    self.check_tab_fatigue=False
                    #cerco di risparmiare memoria
                    for i in range(len(self.ar_fig_fatigue)):
                        plt.figure(self.ar_fig_fatigue[i].number).clear()
                        plt.close(self.ar_fig_fatigue[i])
                    
                    self.ar_fig_fatigue=[] #reinizializzo l'array
                    self.canvas_fatigue.get_tk_widget().pack_forget()
                    self.canvas_fatigue.get_tk_widget().destroy()
                    self.toolbar_fatigue.pack_forget()
                    self.toolbar_fatigue.destroy()
                    self.muscle_selection.destroy()

                    self.muscle_selection=None
                    self.tab_fatigue = None #reinizializzo a None la tab
                    self.check_tab_fatigue=False
                    self.canvas_fatigue=None
                    self.toolbar_fatigue=None
                except Exception as e:
                    self.check_tab_fatigue=False

                try:
                    #ciclo su tutte le tab single channel
                    for tab,id in zip(self.tab_channel,range(len(self.tab_channel))):
                        try:
                            self.tabControl.forget(tab) #provo a chiudere la tab se è presente (altrimenti entra nell'except)
                            self.check_tab_channel[id]=False

                            #cerco di risparmiare memoria
                            for i in range(np.shape(self.ar_fig)[1]):
                                if not self.ar_fig[id][i]==None:
                                    plt.figure(self.ar_fig[id][i].number).clear()
                                    plt.close(self.ar_fig[id][i])
                                    self.ar_fig[id][i]=None
                            
                            #cerco di risparmiare memoria elinando tutti i widget presenti
                            if not self.canvas_single_channel[id]==None:
                                self.canvas_single_channel[id].get_tk_widget().pack_forget()
                                self.canvas_single_channel[id].get_tk_widget().destroy()
                                self.canvas_single_channel[id]=None
                            
                            if not self.toolbar_single_channel[id]==None:
                                self.toolbar_single_channel[id].pack_forget()
                                self.toolbar_single_channel[id].destroy()
                                self.toolbar_single_channel[id]=None
                            
                            if not self.single_channel_plot_selection[id]==None:
                                self.single_channel_plot_selection[id].destroy()
                                self.single_channel_plot_selection[id]=None

                            if not self.change_features_single_channel[id]==None:
                                self.change_features_single_channel[id].destroy()
                                self.change_features_single_channel[id]=None

                            if not self.change_BLE_single_channel[id]==None:
                                self.change_BLE_single_channel[id].destroy()
                                self.change_BLE_single_channel[id]=None

                            if not self.change_opti_feature_single_channel[id]==None:
                                self.change_opti_feature_single_channel[id].destroy()
                                self.change_opti_feature_single_channel[id]=None

                            self.tab_channel[id] = None #reinizializzo a None la tab

                        except Exception as e:
                            self.check_tab_channel[id]=False
                except Exception as e:
                    #print(e)
                    pass
                
                #chiudo la finestra window_filter se è aperta 
                if not self.window_filter == None:
                    self.window_filter.destroy()
                    self.window_filter=None

                #chiudo la finestra frequency_setting se è aperta 
                if not self.frequency_setting == None:
                    self.frequency_setting.destroy()
                    self.frequency_setting=None
                
                #reinizializzazione delle variabili ogni volta che carico un nuovo workout
                self.title_optitrack="None"
                
                #INIZIALIZZAZIONE FIGURA PER IL PLOT DEL SEGNALE FILTRATO SU CUI CALCOLARE LE FEATURES E MOSTRARLE NELL'EDITOR
                self.fig_compute=None #variabile che conterrà la figura in cui verrà mostrato il segnale su cui calcolare le features
                self.text_content='' #variabile che conterrà ciò che verrà scritto nell'editor (inizialmente è vuota)
                self.textarea=None #editor in cui andare a scrivere le features calcolate (inizialmente è chiuso)

                #INIZIALIZZAZIONE VARIABILI PER PLOT SINGLE CHANNEL
                self.check_tab_channel=[False]*self.number_of_channels #lista che conterrà le eventuali tab per mostrare i plot generati alla pressione dei tasti contenuti nel menù 'muscles' (self.number_of_channels possibili tab diverse)
                self.tab_channel=[None]*self.number_of_channels #lista che conterrà le eventuali tab single_channel
                self.id_single_channel=np.zeros(self.number_of_channels,dtype=int) #lista che contiene l'id della figura da mostrare per i diversi canali (all'apertura di una delle tab contenute in self.tab_channel, verrà mostrata la figura con id=0, all'interno della lista self.ar_fig)
                self.canvas_single_channel=[None]*self.number_of_channels #lista che conterrà le eventuali canvas per mostrare i grafici generati alla pressione dei tasti del menù 'muscles'
                self.toolbar_single_channel=[None]*self.number_of_channels #lista che conterrà le eventuali toolbar dei grafici generati alla pressione dei tasti del menù 'muscles'
                self.single_channel_plot_selection=[None]*self.number_of_channels #lista che conterrà i combobox per la selezione del plot da mostrare all'interno di una delle tab presenti in sel.tab_channel
                self.single_channel_available_plot=['SMOOTHED','SPECTROGRAM','PSD','FEATURES'] #all'interno delle tab presenti in self.tab_channel ci saranno almeno questi grafici
                self.change_features_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per cambiare la feature mostrata nel grafico 'FEATURES' all'interno delle tab presenti in self.tab_channel
                self.change_BLE_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per selezionare gli eventuali BLE nel grafico 'BLE' all'interno delle tab presenti in self.tab_channel (se sono presenti dispositivi BLE)
                self.change_opti_feature_single_channel=[None]*self.number_of_channels #lista che conterrà i combobox per selezionare le features dell' optitrack in self.tab_channel 
                self.list_available_features=['MAV','RMS','IEMG','VAR','WL','SSC','WAMP','ZC','MNF','MDF'] #lista contenente tutte le features disponibili
                self.list_Df_features=[None]*self.number_of_channels #lista che conterrà i dataframe delle features di tutti i canali
                self.fig_coerence=[None]*self.number_of_channels #lista che conterrà le eventuali figure di coerenza tra i segnali (grafico 'RAW')
                self.fig_PSD=[None]*self.number_of_channels #lista che conterrà le eventuali figure dei PSD (grafico 'PSD')
                self.fig_spectrogram=[None]*self.number_of_channels #lista che conterrà le eventuali figure degli spettrogrammi (grafico 'SPECTROGRAM')
                self.fig_features=[None]*self.number_of_channels #lista che conterrà le eventuali figure delle features (grafico 'FEATURES')

                #INIZIALIZZAZIONI VARIABILI PER PLOT ALL CHANNELS
                self.check_tab_all_channels=False #tab per mostrare i plot geneari alla pressione del tasto 'all_channels'
                self.ar_fig_all=[] #lista che conterrà tutte le figure da mostrare, generate alla pressione del tasto 'all_channels'
                self.available_all_channels_plot=["FILTERED EMG","RMS","SPECTROGRAM","PSD","MNF"] #lista contenente tutti i plot disponibili all_channels

                #INIZIALIZZAZIONI VARIABILI PER PLOT FATIGUE
                self.check_tab_fatigue=False #tab per mostrare i plot geneari alla pressione del tasto 'fatigue analysis'
                self.ar_fig_fatigue=[] #lista che conterrà tutte le figure da mostrare, generate alla pressione del tasto 'fatigue analysis' (saranno self.number_of_channels figure, una per ogni canale)
                self.axfatigue =[[None]*3]*self.number_of_channels #lista che contiene delle liste di assi (3 assi per self.number_of_channels canali)

                #INIZIALIZZAZIONE VARIABILI BOOLEANE PER DESCRIVERE LA PRESENZA DEI FILE
                self.check_emg=False #variabile che diventerà vera quando e se si caricherà il file .emg
                self.check_fit=False #variabile che diventerà vera quando e se si caricherà il file .fit
                self.check_lattato=False #variabile che diventerà vera quando e se si caricherà il file lattato
                self.check_opti=False #variabile che diventerà vera quando e se si caricherà il file optitrack
                self.check_BLE=False #variabile che diventerà vera quando e se si caricherà almeno un file .csv di un dispositivo BLE
                self.list_DF_BLE=[] #lista che conterrà i dataframe dei singoli BLE
                self.Df_BLE=pd.DataFrame() #empty dataframe al quale verranno aggiunte le informazioni in base al numero di dati provenienti dai dispositivi BLE

                #INIZIALIZZAZIONI VARIABILI PER CSV EXPORT
                self.Df_export = None #variabile che conterrà i dati da esportare in .csv (MNF e eventualmente .fit)
                
                #MOSTRO LA BARRA DI PROGRESSO DURANTE IL CARICAMENTO
                self.start_stop_event.set() #setto la varibile di partenza a True (start)
                self.progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(self.start_stop_event,'Loading files...',))
                self.progressbar_process.start() #parte la barra di progresso
                
                #lettura file EMG (è il primo che deve essere letto perchè viene utilizzato come riferimento di inizio registrazione)
                #per evitare possibili ambiguità all'interno della folder ci deve essere un solo file per tipo di registrazione 
                for filename in os.listdir(self.file_directory): #ciclo sui file presenti nella directory
                    if filename.endswith('.csv'): #controllo se il file è un .csv (potrà essere un file emg, lattato, optitrack o BLE)
                        f = open(f'{self.file_directory}/{filename}', 'r') #apro il file e leggo l'header
                        reader = csv.reader(f)
                        headers = next(reader, None)
                        
                        #se è presente un file il cui il primo valore dell'header è 'TIMESTAMP' (caratteristico della registrazione emg), 
                        #ed è il primo file di questa tipologia
                        if(headers[0].split(';')[0]=='TIMESTAMP' and not self.check_emg): 
                            self.title_emg=filename #titolo file emg
                            #variabile che descrive la presenza del file emg diventa vera
                            #(se dovesse esserci un altro file emg non verrebbe aperto)
                            self.check_emg=True 
                            #nel caso in cui il file abbia il sepratore ',' viene convertito in ';' per standardizzare il formato
                            with fileinput.FileInput(f'{self.file_directory}/{filename}') as file: 
                                for line in file:
                                    line.replace(',',';')

                            #lettura file emg in un dataframe
                            self.emgX = pd.read_csv(f'{self.file_directory}/{filename}',usecols=use_columns, delimiter = ';', on_bad_lines='warn')
                            #SE CAMBIA IL TEMPLATE DELL'ACQUISIZIONE DEL SEGNALE EMG, BISOGNA VARIARE QUESTE RIGHE
                            #si presuppone che il file emg sia costituito da queste variabili!!! converto da stringhe a variabili numeriche
                            self.emgX[self.emgX.columns[0]] = pd.to_datetime(self.emgX[self.emgX.columns[0]], errors='coerce') #timestamp (cast datetime)
                            for i in range(1,len(self.emgX.columns)):
                                self.emgX[self.emgX.columns[i]] = pd.to_numeric(self.emgX[self.emgX.columns[i]], errors='coerce')
  
                            #interpolo linearmente i NaT (Not a Time), la variabile diventa cast Timestamp
                            t0 = self.emgX[self.emgX.columns[0]][0] #tempo iniziale
                            m = self.emgX[self.emgX.columns[0]].notnull() #vettore booleano, True dove ci sono dei valori, False dove ci sono nan
                            #aggiungo una colonna t_int che conterrà il tempo espresso in secondi
                            self.emgX.loc[m, 't_int'] = (self.emgX.loc[m, self.emgX.columns[0]] - t0).dt.total_seconds()
                            t_seconds=self.emgX.loc[:,'t_int'].interpolate()

                            #ciclo per convertire t_seconds nel formato datetime.time
                            #che ci permette la visualizzazione degli assi
                            self.timestamp_emg=[]
                            for seconds in t_seconds:
                                microseconds=(seconds*1000000) % 1000000
                                hours = seconds // 3600
                                minutes = (seconds % 3600) // 60
                                seconds = seconds % 60 // 1
                                self.timestamp_emg.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

                            #le prime tre colonne sono timestamp, stream_ID e sequence le altre i muscoli
                            #interpolo linearmente i NaN dei canali                    
                            for i in range(3,len(self.emgX.columns[:-1])):
                                self.emgX[self.emgX.columns[i]]=self.emgX[self.emgX.columns[i]].interpolate(limit_direction='both')

                            #lista contenente i nomi dei muscoli
                            self.array_nome_muscoli=[]
                            for i in range(3,len(self.emgX.columns[:-1])):
                                self.array_nome_muscoli.append(self.emgX.columns[i])
 
                            #update del menù canali con i nomi dei muscoli
                            self.menubar.uptade_channel_labels(self.array_nome_muscoli)

                            #cast int64
                            for i in range(3,len(self.emgX.columns[:-1])):
                                self.emgX[self.emgX.columns[i]] = self.emgX[self.emgX.columns[i]].astype('int64')
                            
                            #CREAZIONE DATAFRAME RAW
                            #colonne contenenti solo i nomi dei muscoli, non interssa stream_id, sequence e timestamp 
                            #(l'ultima colonna (t_int) non la considero perchè è quella che ho creato per interpolare il tempo)
                            self.Df_Emg_Raw=self.emgX.iloc[:,3:-1]
                            #assegno il timestamp determinato all'indice del dataframe dell'Emg Raw
                            self.Df_Emg_Raw.index=self.timestamp_emg

                            #DETERMINO LA FREQUENZA DI CAMPIONAMENTO AUTOMATICAMENTE IN BASE AL TIMESTAMP E AL NUMERO DI CAMPIONI
                            msec_ini=self.Df_Emg_Raw.index[0].hour * 3600 + self.Df_Emg_Raw.index[0].minute * 60 + self.Df_Emg_Raw.index[0].second + self.Df_Emg_Raw.index[0].microsecond/1000000
                            msec_fin=self.Df_Emg_Raw.index[-1].hour * 3600 + self.Df_Emg_Raw.index[-1].minute * 60 + self.Df_Emg_Raw.index[-1].second + self.Df_Emg_Raw.index[-1].microsecond/1000000
                            fs=len(self.Df_Emg_Raw)/(msec_fin-msec_ini) #numero di campioni/tempo registrazione
                            
                            #riduco la risoluzione dei punti nei plot in base al numero dei campioni, e setto il tempo di campionamento della MNF
                            if len(self.Df_Emg_Raw) < 300000:
                                self.num_ele=1
                                self.TMNF=1
                                self.Tfinestra=1
                            elif 300000 <len(self.Df_Emg_Raw) < 1200000:
                                self.num_ele=3
                                self.TMNF=30
                                self.Tfinestra=30
                            else:
                                self.TMNF=30
                                self.Tfinestra=30
                                self.num_ele=5

                            list_available_freq=[500,1000,2000,3000] #la frequenza di campionamento potrà essere uno di questi valori
                            best_diff=1000 #inizializzazione variabile che conterrà la differenza più piccola tra le frequenze di campionamento disponibili e quella calcolata
                            for f in list_available_freq:
                                diff = abs(fs-f)
                                if diff < best_diff:
                                    best_diff=diff
                                    self.fs_emg=float(f) #assegno a self.fs_emg la frequenza di campionamento che più si avvicina a quella calcolata
                            
                            self.highcut = self.fs_emg/2 - 0.1 #in base alla frequenza di campionamento calcolo la frequenza alta del filtro passa-banda
                            self.default_high = self.fs_emg/2 - 0.1
                            self.test_highcut = self.fs_emg/2 - 0.1

                            #CREAZIONE DATAFRAME EMG FILTRATI E RMS
                            #creazione della variabile self.Df_Emg_Filtered contente i segnali emg filtrati 
                            #del dataframe Df_Savitzky che conterrà i segnali smussati
                            #del Dataframe self.Df_RMS contente i segnali RMS
                            #e del Dataframe self.Df_MNF contente i segnali MNF
                            self.create_dataframes(False) #update di tutti i dataframe (Filtered, RMS Savitzky e MNF)
            
                            #SELEZIONE DI UN CANALE DI INTERESSE
                            #id del canale selezionato (all'inizio viene selezionato il primo canale)
                            self.ID_channel_under_investigation = 0 
                            #canale preso in esame se si vorrà analizzare un segnale specifico
                            self.channel_under_investigation = self.Df_Emg_Raw.iloc[:,self.ID_channel_under_investigation]
                            #canale filtrato preso in esame se si vorrà analizzare un segnale specifico 
                            self.filter_dato1 = self.Df_Emg_Filtered.iloc[:,self.ID_channel_under_investigation] 
                            #evidenzio in rosso il canale selezionato
                            change_item_color(self.menubar.channel_dropdown,self.ID_channel_under_investigation) 
                            #stringa per la visualizzazione grafica del canale (titolo) corrispondente al nome del muscolo
                            self.muscle_name=self.array_nome_muscoli[self.ID_channel_under_investigation]
                            #RMS del canale selezionato 
                            self.RMS=self.Df_RMS.iloc[:,self.ID_channel_under_investigation] 
                            continue

                #lettura degli altri file eventualmenti presenti (BLE, optitrack, fit, lattato)
                for filename in os.listdir(self.file_directory): #ciclo sui file presenti nella directory
                    if filename.endswith('.csv'): #controllo se il file è un .csv       
                        f = open(f'{self.file_directory}/{filename}', 'r') #apro il file e leggo l'header
                        reader = csv.reader(f)
                        headers = next(reader, None)

                        if self.check_emg: #prima di leggere gli altri .csv verifico che sia stato caricato il file emg, perchè è il file di riferimento per il timestamp 
                            #se è presente un file in cui il primo valore dell'header e 'Format Version' (caratteristico della registrazione optitrack) 
                            #ed è il primo di questa tipologia
                            if(headers[0].split(';')[0]=='Format Version' and not self.check_opti): 
                                self.check_opti=True #variabile che descrive la presenza del file OPTITRACK diventa vera
                                self.available_movements=[]#lista che conterrà i diversi corpi rigidi disponibili
                                #lettura file optitrack
                                optitrack = pd.read_csv(f'{self.file_directory}/{filename}', delimiter = ',',header=[1,2,3,4,5], on_bad_lines='warn')
                                self.title_optitrack = filename #titolo optitrack
                                
                                time_optitrack= optitrack.iloc[:,optitrack.columns.get_level_values(4) =='Time (Seconds)'].values
                                Rigid_Bodies={}
                                #popolo un dizionario con le caratteristiche dei corpi rigidi
                                for column in optitrack.columns:
                                    if column[0] == 'Rigid Body' and not column[3] == 'Mean Marker Error':
                                        data=pd.to_numeric(optitrack[(f'{column[0]}',f'{column[1]}',f'{column[2]}',f'{column[3]}',f'{column[4]}')], errors='coerce')
                                        data=data.interpolate(limit_direction='both')
                                        Rigid_Bodies[f'{column[1]} {column[3]} {column[4]}']=data.values
                                        self.available_movements.append(f'{column[1]} {column[3]}') #aggiungo il tipo di movimento (es RigidBody_name Rotation o RigidBody_name Position )
                                        self.available_movements=list(set(self.available_movements)) #prendo solamente i movimenti univoci (es Rotation X, Rotation Y, Rotation Z diventano solo Rotation perchè le tre rotazioni verranno mostrate insieme)
                                
                                #creo il tempo dell'optitrack nel formato datetime.time
                                timestamp_optitrack=[]
                                for seconds in time_optitrack:
                                    microseconds=(seconds*1000000) % 1000000
                                    hours = seconds // 3600
                                    minutes = (seconds % 3600) // 60
                                    seconds = seconds % 60 // 1
                                    timestamp_optitrack.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

                                #creao il dataframe contente i dati dell'optitrack
                                self.Df_Opti=pd.DataFrame(data=Rigid_Bodies,index=timestamp_optitrack)                
                                continue

                            #LETTURA FILE BLE FASCIA CARDIO
                            if int(len(headers[0].split(';')) > 1): # serve perchè anche l'export dell'MNF inizia con 'TIME', ma è un .csv che usa come delimitatore ',' quindi creerebbe problemi con il file BLE che inizia con 'TIME ma è delimitato con ';''
                                if (headers[0].split(';')[0]=='TIME' and ((headers[0].split(';')[1]==' Heart  Rate  Measurement ') or (headers[0].split(';')[1]==' HR'))): #template header della fascia cardio (prima colonna TIME, seconda colonna HR)
                                    Df_HR_Strip=pd.read_csv(f'{self.file_directory}/{filename}', delimiter = ';', on_bad_lines='warn')
                                    self.check_BLE=True
                                    self.Df_HR_Strip=pd.DataFrame(columns=['HR'])
                                    self.Df_HR_Strip['HR']=Df_HR_Strip[' Heart  Rate  Measurement ']
                                    #ciclo per convertire t_seconds che è in formato datetime.timedelta nel formato datetime.time
                                    #che ci permette la visualizzazione degli assi
                                    self.timestamp_HR_Strip=[]
                                    #IMPORTANTE! SOTTRAGGO AL TIMESTAMP IL VALORE DEL PRIMO CAMPIONE DEL .CSV EMG
                                    first_time=self.emgX[self.emgX.columns[0]][0]
                                    #ciclo per convertire gli istanti di tempo (string) in variabili datetime.time
                                    for duration in Df_HR_Strip['TIME']:
                                        date_time_obj = datetime.datetime.strptime(duration, ' %Y-%m-%d %H:%M:%S.%f ')
                                        timedelta=date_time_obj - first_time
                                        seconds = timedelta.total_seconds()
                                        microseconds=(seconds*1000000) % 1000000
                                        hours = seconds // 3600
                                        minutes = (seconds % 3600) // 60
                                        seconds = seconds % 60 // 1
                                        self.timestamp_HR_Strip.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

                                    self.Df_HR_Strip.index=self.timestamp_HR_Strip
                                    #aggiungo alla lista contenente i dataframe BLE, quello appena calcolato
                                    self.list_DF_BLE.append(self.Df_HR_Strip)

                    if(filename.endswith('.fit') and not self.check_fit): #se è presente un file .fit ed è il primo che trovo
                        self.Df_fit=open_fit(f'{self.file_directory}/{filename}',self.fs_fit) #apertura del file.fit e creazione dei dataframe
                        #variabile che descrive la presenza del file fit diventa vera (se ce ne dovesse essere un altro non verrebbe aperto)
                        self.check_fit=True 
                        for filename in os.listdir(self.file_directory): #il file lattato è presente solo se è presente il file .fit
                            if(filename.startswith('lattato') and not self.check_lattato): #se è presente un file del lattato
                                #variabile che descrive la presenza del file lattato diventa vera (se ce ne dovesse essere un altro non verrebbe aperto)
                                self.check_lattato=True 
                                dati_lattato = pd.read_csv(f'{self.file_directory}/{filename}', delimiter = ',', on_bad_lines='warn')
                                #il file lattato è costruito con le colonne lattato power e time(s)
                                lattato = pd.to_numeric(dati_lattato['lattato'], errors='coerce', downcast='float')
                                power = pd.to_numeric(dati_lattato['power'], errors='coerce')
                                tempo_lattato = pd.to_numeric(dati_lattato['time(s)'], errors='coerce') #tempo espresso in secondi
                                #creo un array di NaN di lunghezza pari alla lunghezaz del file .fit che è campionato a 1s
                                a = np.empty(len(self.Df_fit.index))
                                a[:] = np.nan
                                #il dataframe del lattato avrà lo stesso indice temporale del file .Fit (che è campionato ogni secondo)
                                self.Df_lattato=pd.DataFrame(data=a,index=self.Df_fit.index)
                                self.Df_lattato.columns=['lactate'] #cambio il nome della colonna
                                #sostituisco agli istanti di tempo in cui ho calcolato il lattato, i valori del lattato
                                self.Df_lattato['lactate'].iloc[tempo_lattato.values]=lattato.values 
                                #creo una curva di regressione polinomiale di terzo ordine del lattato
                                fit=np.polyfit(tempo_lattato.values,lattato.values,3) 
                                #valuto la curva di regressione tra il primo e l'ultimo tempo in cui si è calcolato il lattato 
                                lattato_regression=np.polyval(fit,np.linspace(tempo_lattato.values[0],tempo_lattato.values[-1],tempo_lattato.values[-1]-tempo_lattato.values[0]))
                                #creo un dataframe contetnte i valori della curva di regressione
                                self.Df_lattato_regression=pd.DataFrame(data=lattato_regression,index=self.Df_fit.iloc[tempo_lattato.values[0]:tempo_lattato.values[-1]].index)
                                self.Df_lattato_regression.columns=['lactate regression']
                                continue
                        continue
                
                #TERMINO DI MOSTRARE LA BARRA DI PROGRESSO
                self.start_stop_event.clear() #la vraibile diventa False (stop)
                self.progressbar_process=None #il processo non è più presente                   

                if self.check_BLE: #se è stato caricato almeno un dispositivo BLE
                    #creo un unico dataframe concatenando i singoli dataframe BLE
                    for Df_ble in self.list_DF_BLE:
                        self.Df_BLE= pd.concat([self.Df_BLE, Df_ble], axis=1, sort=True) #concateno i Dataframe di dispositivi BLE
                        self.Df_BLE=self.Df_BLE.interpolate(limit_direction='both') #interpolo i NaN
                        self.fig_BLE=[None]*self.number_of_channels #inizializzo le figure che conterranno le informazioni dei dispositivi BLE
                        self.single_channel_available_plot.append('BLE') #aggiungo alla lista dei possibili plot, quello dei BLE
                    
                    self.list_available_BLE_Data=list(self.Df_BLE) #lista che verrà utilizzata all'interno di un combobox per poter selezionare quale dato proveninete dai dispositivi BLE mostrare sul plot
                
                if self.check_fit: #se è presente il file.fit
                    self.Df_fit=self.Df_fit.iloc[:int((len(self.Df_Emg_Raw)*self.fs_fit/self.fs_emg))] #taglio la registrazione del file .fit quando è terminata la registrazione emg
                    self.fig_fit=[None]*self.number_of_channels #lista che conterrà le eventuali figure in cui mostrare il file.fit
                    self.single_channel_available_plot.append('FIT') #aggiungo alla lista dei possibili plot, quello dei FIT
                    if self.check_lattato: #se è presente il lattato
                        #taglio la registrazione del lattato quando è terminata la registrazione emg
                        self.Df_lattato=self.Df_lattato.iloc[:int(len(self.Df_Emg_Raw) * self.fs_fit / self.fs_emg), :]
                        self.Df_lattato_regression=self.Df_lattato_regression.iloc[:int(len(self.Df_Emg_Raw) * self.fs_fit / self.fs_emg), :]
                
                if self.check_opti: #se è presente il file optitrack
                    self.fig_optitrack=[None]*self.number_of_channels #lista che conterrà le eventuali figure in cui mostrare l'analisi cinematica
                    self.single_channel_available_plot.append('CINEMATIC') #aggiungo alla lista dei possibili plot, quello dell'analisi cinematica

                number_ar_fig=4 #alla pressione di un tasto del menù 'muscles' si aprirà la relativa tab, che mostrerà minimo 4 plot
                for n in [self.check_opti,self.check_fit,self.check_BLE]: #ciclo per controllare se sono stati caricati i file optitrack, fit e BLE
                    if n: #se è presente il file
                        number_ar_fig=number_ar_fig+1 #aumento di 1 il numero di plot che verranno mostrati alla pressione di un tasto del menù 'muscles'

                self.ar_fig=[[None]*number_ar_fig]*self.number_of_channels #inizializzo la lista che conterrà i plot da mostrare, per ogni canale
                
                #aggiornamento della barra di stato dell'editor
                self.statusbar.update_status(
                    f'EMG {self.title_emg}\tMUSCLE {self.muscle_name}\t\tFs {self.fs_emg}Hz\t'      
                    f'WINDOW SIZE {round(self.window_size*1000,0)}ms\tOVERLAPPING TIME {round(self.overlap*1000,0)}ms\t'       
                    f'\tOPTITRACK {self.title_optitrack}',
                    True)
                
                #attivazione degli altri pulsanti del menù all'aperture del file
                self.menubar.file_dropdown.entryconfigure("Export .xlsx", state="normal")
                self.menubar.file_dropdown.entryconfigure("Export rms", state="normal")
                self.menubar.menubar.entryconfigure("Muscles",state="normal")
                self.menubar.menubar.entryconfigure("Plot",state="normal")
                self.menubar.menubar.entryconfigure("Settings",state="normal")

                #quando carico un nuovo atleta le features precedenti vengono cancellate 
                self.amav=[]
                self.arms=[]                                                             
                self.aiemg=[]
                self.avar=[]
                self.awl=[]
                self.assc=[]
                self.awamp=[]
                self.azero_crossings=[]                                                       
                self.amnf=[]                                                                                                       
                self.amdf=[]
                
                #variabile che è True quando le features sono già calcolate
                self.features=False

                #emgX conteneva anche le iformazioni relative alla sequence ecc, per cui alla fine lo elimino e tengo solo le informazioni dei canali (Df_Emg_Raw)
                self.emgX=None 

                try:
                    self.tabControl.add(self.tab_home, text='home') #Insert the tab
                except Exception as e:
                    #print(e)
                    pass

            else:
                if self.check_all_channels_disconnected: #variabile che indica che tutti i canali erano disconnessi
                    tk.messagebox.showerror(title='LOAD ERROR',message='All channels were diconnected')
                else:
                    #se nella directory che avevo selezionato non era presente un file EMG mostro un messaggio a schermo
                    tk.messagebox.showerror(title='LOAD ERROR',message='File EMG not available')

    def display_PSD(self,filter_dato,name,ax,xlabel=False):
        """
        displays PSD on a chart (Power spectral density)

        Args:
            filter_dato (array_like): Emg filter data
            name (string): Name of the analyzed muscle
            ax (pyplot.ax): Subplot axes
            xlabel (bool): True if label is present on axis {False}
        """
        #4 secondi di finestra sull'intero segnale 
        #di default la funzione userebbe 256 campioni pari a 256 millisecondi alla frequenza di campionamento di 100Hz
        win = 4 * self.fs_emg  
        self.low, self.high = 0.25, 4 #frequenze di interesse
        
        #calcolo della densità spettrale
        freqs, psd = signal.welch(filter_dato, self.fs_emg, nperseg=win)
        self.idx_delta = np.logical_and(freqs >= self.low, freqs <= self.high)
        self.idx_delta2 = np.logical_and(freqs >= self.high, freqs <= self.fs_emg/2)
        ax.plot(freqs, psd, lw=2, color='k')
        ax.fill_between(freqs, psd, where=self.idx_delta, color='skyblue')
        ax.fill_between(freqs, psd, where=self.idx_delta2, color='orange')
        ax.set_title(f'{name}',fontweight="bold")
        ax.tick_params(axis='both',labelsize=10)
        if xlabel:
            ax.set_xlabel('Hz',fontsize=12)
            ax.tick_params(labelbottom=True,labelsize=10)

    def display_spettrogramma(self,filter_dato,name,ax,xlabel=False):
        """
        displays spectrograms on a chart

        Args:
            filter_dato (array_like): Emg filter data
            name (string): Name of the analyzed muscle
            ax (pyplot.ax): Subplot axes
            xlabel (bool): True if label is present on axis {False}
        """
        f, t, Sxx = signal.spectrogram(filter_dato, self.fs_emg, mode = 'magnitude')
        time_spectro=time_convert(t)
        ax.xaxis.set_major_locator(plt.MaxNLocator(5)) #massimo 5 xticks per una buona visualizzazione
        #come valore massimo si è impostato 0.3 del max per aumentare il contrasto in questo range e saturare i valori più elevati,
        #questo permete di limitare l'effetto di picchi sporadici molto elevati
        ax.pcolormesh(time_spectro, f, Sxx,vmin=0,vmax=0.3*Sxx.max()) 
        #ax.set_ylabel('Hz', rotation=0,fontsize=12)
        ax.tick_params(axis='both',labelsize=10)
        ax.set_title(f'{name}',fontweight="bold")
        if xlabel:
            ax.set_xlabel('hh:mm:ss',fontsize=12)
            ax.tick_params(labelbottom=True,labelsize=10)


    def display_MNF(self,MNF_it,name,ax,xlabel=False):
        """
        displays MNF on a chart

        Args:
            MNF_it (pd.Series): MNF to display
            name (string): Name of the analyzed muscle
            ax (pyplot.ax): Subplot axes
            xlabel (bool): True if label is present on axis {False}
        """
        #plot MNF
        MNF_it.plot(ax=ax,legend=False,style='-xb')
        ax.set_title(f'{name}',fontweight="bold")
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.tick_params(axis='both',labelsize=10)
        if xlabel:
            ax.set_xlabel('hh:mm:ss',fontsize=12)
            ax.tick_params(axis='x',labelbottom=True,labelsize=10)

    def clear_editor(self, *args):
        """clear editor window
        """
        self.tabControl.select(self.tab_editor) #focus alla tab con l'editor
        self.textarea.configure(state='normal')
        self.first_feature=True #ogni volta che si pulisce l'editor la variabile diventa vera per andare a riscivere l'header
        self.textarea.delete(1.0,tk.END) #cancello l'editor
        self.textarea.configure(state='disabled') #l'editor viene utilizzato solo per stampare i valori ma non può essere modificato
        self.statusbar.update_status(
            f'EMG {self.title_emg}\tMUSCLE {self.muscle_name}\tFs {self.fs_emg}Hz\t'      
            f'WINDOW SIZE {round(self.window_size*1000,0)}ms\tOVERLAPPING TIME {round(self.overlap*1000,0)}ms\t'       
            f'\tOPTITRACK {self.title_optitrack}',
            True)

    def change_channel(self,id):
        """sets muscle to analyze
        
        Args:
            id (int): channel_menù index, representing the selected muscle
        """
        self.features=False #quando cambio canale la variabile che mi dice se ho già calcolato le features diventa falsa
        self.ID_channel_under_investigation=id #id del canale selezionato
        self.channel_under_investigation = self.Df_Emg_Raw.iloc[:,self.ID_channel_under_investigation] #cambio il canale under investigation (segnale EMG)
        self.filter_dato1 = self.Df_Emg_Filtered.iloc[:,self.ID_channel_under_investigation] #segnale filtrato under investigation
        self.RMS=self.Df_RMS.iloc[:,self.ID_channel_under_investigation] #RMS del segnale under investigation
        self.muscle_name=self.array_nome_muscoli[self.ID_channel_under_investigation] #cambio la variabile per la stampa (nome muscolo)
        change_item_color(self.menubar.channel_dropdown,self.ID_channel_under_investigation) #cambio il colore della label selezionata
        self.statusbar.update_status(
            f'EMG {self.title_emg}\tMUSCLE {self.muscle_name}\tFs {self.fs_emg}Hz\t'      
            f'WINDOW SIZE {round(self.window_size*1000,0)}ms\tOVERLAPPING TIME {round(self.overlap*1000,0)}ms\t'       
            f'\tOPTITRACK {self.title_optitrack}',
            True) 

        if self.check_tab_editor: #se la tab editor è stata creata
            if str(self.tab_editor) == self.tabControl.select(): #se sono focolazzito sulla tab editor
                self.compute_features() #vado a cambiare il muscolo su cui calcolare le features
            else:
                self.compute_features() #se non è focus sulla tab editor cambio il canale sulla tab editor e poi creo la tab specifica per il muscolo
                self.single_channel()

        else: #se la tab editor non è presente
            self.single_channel() #vado a creare la tab contente i grafici per il muscolo selezionato, oppure, se esiste già, gli do il focus
        
    def features_settings(self):
        """
        shows a gui where it could be set MNF_SAMPLING_TIME, WINDOW_SIZE, OVERALAPPING_TIME and POINT RESOLUTION
        """
        def close():
            self.features_settings_gui.destroy()
            self.features_settings_gui = None

        def ok_command():
            self.features_settings_gui.destroy()
            self.features_settings_gui = None

            #variabili che indicano quali tab andare ad aggiornare
            update_tab_all_channels=False 
            update_tab_fatigue=False
            update_tab_single_channel=[False]*self.number_of_channels

            overlap=int(self.OVERLAP[self.v_overlap.get()][0].split(' ')[0]) #prendo solo la parte numerica, trascurando l'unità di misura
            window_size=int(self.WINDOW_TIME[self.v_window_time.get()][0].split(' ')[0])
            #controllo se ci sono stati dei cambiamenti rispetto ai parametri già selezionati
            if not (float(float(overlap/1000)) == self.overlap and float(float(window_size/1000)) == self.window_size):    
                self.overlap=float(float(overlap)/1000) #converto il valore da stringa a float e poi divido per mille, per ottenere il valore espresso in secondi e non in millisecondi
                self.window_size=float(float(window_size)/1000)
                self.features=False #quando cambio l'overlap la variabile che mi dice se ho già calcolato le features diventa falsa
                self.statusbar.update_status(
                    f'EMG {self.title_emg}\tMUSCLE {self.muscle_name}\tFs {self.fs_emg}Hz\t'      
                    f'WINDOW SIZE {round(self.window_size*1000,0)}ms\tOVERLAPPING TIME {round(self.overlap*1000,0)}ms\t'       
                    f'\tOPTITRACK {self.title_optitrack}',
                    True)
                #MOSTRO LA BARRA DI PROGRESSO DURANTE IL CARICAMENTO
                self.start_stop_event.set() #setto la varibile di partenza a True (start)
                self.progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(self.start_stop_event,'Updating features...',))
                self.progressbar_process.start() #parte la barra di progresso
                #ciclo su tutte le possibili tab dei single channel aperte 
                for tab_id in range(self.number_of_channels):
                    #if not self.tab_channel[tab_id] == None: #se è stata creata la tab per il muscolo i-esimo
                    if self.check_tab_channel[tab_id]:
                        self.tab_channel[tab_id].update()
                        self.toolbar_single_channel[tab_id].children['!button'].invoke() #setto i limiti originali
                        self.window_features(id=tab_id) #vado ad aggiornare le features per il canale selezionato
                        update_tab_single_channel[tab_id]=True #andrò in seguito ad aggiornare questa tab

                self.start_stop_event.clear()
                self.progressbar_process=None

            TMNF=float(self.WINDOW_MNF_TIME[self.v_MNF_window_time.get()][0].split(' ')[0])
            #controllo se c'è stato un cambiamento nel periodo di campionamento della MNF
            if not TMNF == self.TMNF:
                self.TMNF = TMNF
                self.Tfinestra=int(val)
        
                self.create_dataframes(True) #in questo caso vado ad aggiornare solamente Df_MNF perchè la modifica non influisce su Df_Emg_Filtered e Df_RMS
    
                update_tab_all_channels=True
                update_tab_fatigue=True

            #point resolution change
            num_ele=int(self.POINT[self.v_point.get()][0])
            #controllo se c'è stato un cambiamento nella point resolution
            if not num_ele == self.num_ele:
                #se devo aggiorante tutte le tab è inutile mostrare il popup message
                if not (update_tab_all_channels and update_tab_fatigue and any(update_tab_single_channel)):
                    response=tk.messagebox.askyesnocancel(title='POINT RESOLUTION',message='Are you sure to change plot resolution? \n      All open tabs will be updated')
                else:
                    response=1

                if response:
                    self.num_ele=num_ele #aggiorno la risoluzione dei plot
                    update_tab_all_channels=True
                    update_tab_fatigue=True

                    for tab_id in range(self.number_of_channels):
                        if self.check_tab_channel[tab_id]:
                            update_tab_single_channel[tab_id]=True
                    
            #aggiorno le tab cercando di risparmiare memoria
            if update_tab_all_channels:
                try:   
                    self.tabControl.forget(self.tab_all_channels)
                    for i in range(len(self.ar_fig_all)):
                        plt.figure(self.ar_fig_all[i].number).clear()
                        plt.close(self.ar_fig_all[i]) #chiudo le figure

                    self.ar_fig_all=[] #reinizializzo l'array
                    self.canvas_all_channels.get_tk_widget().pack_forget()
                    self.canvas_all_channels.get_tk_widget().destroy()
                    self.toolbar_all_channels.pack_forget()
                    self.toolbar_all_channels.destroy()
                    self.all_channels_plot_selection.destroy()              

                    self.all_channels_plot_selection=None
                    self.tab_all_channels = None #reinizializzo a None la tab
                
                    self.check_tab_all_channels=False
                    self.canvas_all_channels=None
                    self.toolbar_all_channels=None
                    self.tab_home.update()
                    self.tabControl.select(self.tab_home)
                    self.all_channels()
                except Exception as e:
                    self.check_tab_all_channels=False

            if update_tab_fatigue:
                try:
                    self.tabControl.forget(self.tab_fatigue)
                    for i in range(len(self.ar_fig_fatigue)):
                        plt.figure(self.ar_fig_fatigue[i].number).clear()
                        plt.close(self.ar_fig_fatigue[i])
                    
                    self.ar_fig_fatigue=[] #reinizializzo l'array
                    self.canvas_fatigue.get_tk_widget().pack_forget()
                    self.canvas_fatigue.get_tk_widget().destroy()
                    self.toolbar_fatigue.pack_forget()
                    self.toolbar_fatigue.destroy()
                    self.muscle_selection.destroy()

                    self.muscle_selection=None
                    self.tab_fatigue = None #reinizializzo a None la tab
                    self.check_tab_fatigue=False
                    self.canvas_fatigue=None
                    self.toolbar_fatigue=None
                    self.tab_home.update()
                    self.tabControl.select(self.tab_home)
                    self.fatigue()
                except Exception as e:
                    self.check_tab_fatigue=False

            for tab_id in range(self.number_of_channels):
                if update_tab_single_channel[tab_id] == True:
                    self.tabControl.forget(self.tab_channel[tab_id])
                    for i in range(np.shape(self.ar_fig)[1]):
                        if not self.ar_fig[tab_id][i]==None:
                            plt.figure(self.ar_fig[tab_id][i].number).clear()
                            plt.close(self.ar_fig[tab_id][i])
                            self.ar_fig[tab_id][i]=None
            
                    if not self.canvas_single_channel[tab_id]==None:
                        self.canvas_single_channel[tab_id].get_tk_widget().pack_forget()
                        self.canvas_single_channel[tab_id].get_tk_widget().destroy()
                        self.canvas_single_channel[tab_id]=None
                    
                    if not self.toolbar_single_channel[tab_id]==None:
                        self.toolbar_single_channel[tab_id].pack_forget()
                        self.toolbar_single_channel[tab_id].destroy()
                        self.toolbar_single_channel[tab_id]=None
                    
                    if not self.single_channel_plot_selection[tab_id]==None:
                        self.single_channel_plot_selection[tab_id].destroy()
                        self.single_channel_plot_selection[tab_id]=None

                    if not self.change_features_single_channel[tab_id]==None:
                        self.change_features_single_channel[tab_id].destroy()
                        self.change_features_single_channel[tab_id]=None

                    if not self.change_BLE_single_channel[tab_id]==None:
                        self.change_BLE_single_channel[tab_id].destroy()
                        self.change_BLE_single_channel[tab_id]=None

                    if not self.change_opti_feature_single_channel[tab_id]==None:
                        self.change_opti_feature_single_channel[tab_id].destroy()
                        self.change_opti_feature_single_channel[tab_id]=None

                    self.tab_channel[tab_id] = None #reinizializzo a None la tab
                    self.check_tab_channel[tab_id]=False
                    self.tab_home.update()
                    self.tabControl.select(self.tab_home)
                    self.single_channel(tab_id=tab_id)

        if self.features_settings_gui == None: #se non è presente la finestra per i test dei parametri
            #inizializzazione e apertura nuova finestra per il settaggio delle frequenze
            self.features_settings_gui=tk.Toplevel(master=self.master)
            self.features_settings_gui.title("Features Settings")
            self.features_settings_gui.protocol("WM_DELETE_WINDOW",close)
            #geometria finestra centrata
            w = 600 # width for the Tk self
            h = 220 # height for the Tk self

            # get screen width and height
            ws = self.features_settings_gui.winfo_screenwidth() # width of the screen
            hs = self.features_settings_gui.winfo_screenheight() # height of the screen

            # calculate x and y coordinates for the Tk self window
            x = (ws/2) - (w/2) + 30
            y = (hs/2) - (h/2) + 30

            # set the dimensions of the screen 
            # and where it is placed
            self.features_settings_gui.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        
            self.features_settings_gui.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')

            self.features_settings_gui.configure(background='black')
            self.features_settings_gui.resizable(False,False)
            
            #OVERLAPPING TIME SELECTION
            self.v_overlap=tk.IntVar() 
            self.OVERLAP=[
                ("62 ms",0),
                ("125 ms",1),
                ("250 ms",2)
            ]

            #seleziono il check_button corrispondente al valore di OVERLAP in uso
            for val in self.OVERLAP:
                if int(self.overlap*1000) == int(val[0].split(' ')[0]):
                    self.v_overlap.set(val[1])

            tk.Label(self.features_settings_gui,text="OVERLAPPING TIME",justify=tk.LEFT,bg='black',fg='white').place(x=20,y=5) #posizionamento label setting
            
            for val,OVERLAPS in enumerate(self.OVERLAP): #creo i bottoni relativi alla modalità da scegliere
                tk.Radiobutton(self.features_settings_gui,text=OVERLAPS[0],variable=self.v_overlap,value=val,bg='black',fg='white',selectcolor='black').place(x=20,y=5+(val+1)*20)

            #WINDOW TIME SELECTION
            self.v_window_time=tk.IntVar() 
            self.v_window_time.set(2)
            self.WINDOW_TIME=[
                ("2 ms", 3),
                ("125 ms",0),
                ("250 ms",1),
                ("500 ms",2)
            ]

            #seleziono il check_button corrispondente al valore di WINDOW_TIME in uso
            for val in self.WINDOW_TIME:
                if int(self.window_size*1000) == int(val[0].split(' ')[0]):
                    self.v_window_time.set(val[1])

            tk.Label(self.features_settings_gui,text="WINDOW TIME",justify=tk.LEFT,bg='black',fg='white').place(x=160,y=5) #posizionamento label setting
            
            for val,WINDOW_TIMES in enumerate(self.WINDOW_TIME): #creo i bottoni relativi alla modalità da scegliere
                tk.Radiobutton(self.features_settings_gui,text=WINDOW_TIMES[0],variable=self.v_window_time,value=val,bg='black',fg='white',selectcolor='black').place(x=160,y=5+(val+1)*20)
        
            #WINDOW MNF TIME SELECTION
            self.v_MNF_window_time=tk.IntVar() 
            self.v_MNF_window_time.set(5)
            self.WINDOW_MNF_TIME=[
                ("1 s",0),
                ("2 s",1),
                ("5 s",2),
                ("10 s",3),
                ("20 s",4),
                ("30 s",5),
                ("60 s",6),
                ("0.0084 s",7)
            ]

            # #seleziono il check_button corrispondente al valore di TMNF in uso
            # for val in self.WINDOW_MNF_TIME:
            #     if int(self.TMNF) == int(val[0].split(' ')[0]):
            #         self.v_MNF_window_time.set(val[1])

            #seleziono il check_button corrispondente al valore di TMNF in uso
            for val in self.WINDOW_MNF_TIME:
                if float(self.TMNF) == float(val[0].split(' ')[0]):
                    self.v_MNF_window_time.set(val[1])


            tk.Label(self.features_settings_gui,text="MNF TIME SAMPLING",justify=tk.LEFT,bg='black',fg='white').place(x=300,y=5) #posizionamento label setting
            
            for val,WINDOW_MNF_TIMES in enumerate(self.WINDOW_MNF_TIME): #creo i bottoni relativi alla modalità da scegliere
                tk.Radiobutton(self.features_settings_gui,text=WINDOW_MNF_TIMES[0],variable=self.v_MNF_window_time,value=val,bg='black',fg='white',selectcolor='black').place(x=300,y=5+(val+1)*20)
        
            #POINT REDUCTION SELECTION
            self.v_point=tk.IntVar() 
            self.POINT=[
                ("1",0),
                ("3",1),
                ("5",2)
            ]

            #seleziono il check_button corrispondente al valore in uso
            for val in self.POINT:
                if int(self.num_ele) == int(val[0]):
                    self.v_point.set(val[1])

            tk.Label(self.features_settings_gui,text="POINT RESOLUTION",justify=tk.LEFT,bg='black',fg='white').place(x=440,y=5) #posizionamento label setting
            
            for val,POINT in enumerate(self.POINT): #creo i bottoni relativi alla modalità da scegliere
                tk.Radiobutton(self.features_settings_gui,text=POINT[0],variable=self.v_point,value=val,bg='black',fg='white',selectcolor='black').place(x=440,y=5+(val+1)*20)
            
            ok_button=tk.Button(master=self.features_settings_gui, width=10, bg='white',fg='black',text="Ok", command=ok_command)
            ok_button.place(x=280,y=185)

            #blocca l'esecuzione dell'applicazione fino a quando non viene chiusa
            self.features_settings_gui.transient(self.master)
            self.features_settings_gui.grab_set()
            self.master.wait_window(self.features_settings_gui)

    def compute_features(self):
        """computes features of a selected region and writes on the editor
        """
        if not self.check_tab_editor: #se la tab editor non è presente
            self.check_tab_editor=True
            self.tab_editor = ttk.Frame(self.tabControl) # Create a tab 
            self.tabControl.add(self.tab_editor, text='features') # Add the tab

            #self.ID_current_channel_displayed = self.ID_channel_under_investigation
            self.font_spec=("ubuntu",9) #specifiche font
            #specifiche editor
            self.textarea=tk.Text(self.tab_editor,bg='black',fg='white',font=self.font_spec,width=1,height=1) #editor black
            self.textarea.insert(tk.END, f'{self.text_content}') #apro l'editor scrivendo il contenuto della variabile (self.text_content) 
            self.scroll=tk.Scrollbar(self.textarea,command=self.textarea.yview) #aggiunta della scroll bar
            self.textarea.configure(yscrollcommand=self.scroll.set,state='disabled') #non è possibile scrivere nell'editor ma solo visualizzare
            self.textarea.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=True) #l'editor occupa tutta la dimensione della finestra
            self.scroll.pack(side=tk.RIGHT,fill=tk.Y) #posizionamento della scrollbar a destra
            
            self.fig_compute = plt.figure() #figura contente il plot del segnale su cui si vuole calcolare le features
            self.fig_compute = plt.gcf()
            ax=plt.gca()

            #PLOT SEGNALE FILTRATO
            self.filter_dato1.plot(ax=ax,legend=False,color='red')
            #tolgo lo spazio bianco prima dell'inizio del segnale
            ax.margins(x=0)
            ax.set_title( f'{self.muscle_name}',fontweight="bold")
            ax.set_xlabel('hh:mm:ss',fontsize=12)
            ax.tick_params(labelsize=10)
            plt.subplots_adjust(left  = 0.07, bottom = 0.18, top=0.90, right = 0.93,hspace = 0.8)

            def write_features():
                xlim=ax.get_xlim() #considero i limiti del segnale
                self.xin=int(xlim[0])
                self.xfin=int(xlim[1])
                self.campione_iniziale=int(xlim[0]*self.fs_emg) #converto i secondi in campioni
                self.campione_finale=int(xlim[1]*self.fs_emg) #converto i secondi in campioni
                self.time_display=time_convert([self.xin,self.xfin]) #converto il tempo in una stringa nel formato %H:%M:%S 
                
                #calcolo le feature sul segnale filtrato nell'intervallo selezionato
                self.mav=MAV(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.rms=RMS(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.iemg = IEMG(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.var = VAR(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.wl = WL(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.ssc = SSC(self.filter_dato1[self.campione_iniziale:self.campione_finale].values,self.th)
                self.wamp = WAMP(self.filter_dato1[self.campione_iniziale:self.campione_finale].values,self.th)
                self.zero_crossings = ZC(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.sample_on_sec = len(self.filter_dato1[self.campione_iniziale:self.campione_finale])/self.fs_emg
                self.zcr = self.zero_crossings/self.sample_on_sec
                self.freqs, self.psd = signal.welch(self.filter_dato1[self.campione_iniziale:self.campione_finale].values, self.fs_emg)
                self.fmean=MNF(self.freqs,self.psd)
                self.fmedian=MDF(self.freqs,self.psd)
                
                #stampo le features nell'editor
                self.textarea.configure(state='normal')
                if(self.first_feature): #se era la prima volta che calcolavo le features, stampo un header
                    self.textarea.insert(tk.END, f"\n\t\t\t\t\t\tMAV\t  RMS\t  IEMG\t\tVAR\t\tWL\t\tSSC\tWAMP\t ZC\tMNF\tMDF")
                    self.first_feature=False
                self.textarea.insert(tk.END, f"\n\n  {self.muscle_name}\t  {self.time_display[0]} - {self.time_display[1]}\t\t\t")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.mav,2))}")
                self.textarea.insert(tk.END, f"\t  {str(round(self.rms,2))}")
                self.textarea.insert(tk.END, f"\t  {str(round(self.iemg,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.var,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.wl,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.ssc,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.wamp,2))}")
                self.textarea.insert(tk.END, f"\t {str(round(self.zero_crossings,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.fmean,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.fmedian,2))}\n")

                #una volta terminata la scrittura, disabilito l'editor
                self.textarea.configure(state='disabled')
            
            def Add2ClipBoard():
                """
                adds features to clipboard
                """
                import pyperclip
                text=self.textarea.get(1.0,tk.END)
                pyperclip.copy(f'{text}')

            self.canvas_compute = FigureCanvasTkAgg(self.fig_compute, master=self.tab_editor)  # A tk.DrawingArea.
            self.canvas_compute.draw()
            self.canvas_compute.get_tk_widget().configure(width=1,height=1)
            self.canvas_compute.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH,expand=True)
            self.toolbar_compute = NavigationToolbar2Tk(self.canvas_compute, self.tab_editor)
            #aggiungo sulla toolbar i pulsanti compute features e clear editor
            self.compute_button = tk.Button(master=self.toolbar_compute, bg='white',text="COMPUTE FEATURES", command=write_features)
            self.compute_button.place(relx=0.25)
            self.clear_button = tk.Button(master=self.toolbar_compute, bg='white',text="CLEAR FEATURES", command= lambda: self.clear_editor())
            self.clear_button.place(relx=0.45)
            self.copy_button = tk.Button(master=self.toolbar_compute, bg='white',text="ADD TO CLIPBOARD", command=Add2ClipBoard)
            self.copy_button.place(relx=0.65)
            self.toolbar_compute.update()
            self.canvas_compute.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            #una volta creata la seleziono
            self.tab_editor.update()
            self.tabControl.select(self.tab_editor)
        else:
            self.tab_editor.update()
 
            #PLOT SEGNALE FILTRATO
            ax=self.fig_compute.axes[0]
            ax.clear()
            self.filter_dato1.plot(ax=ax,legend=False,color='red')
            #tolgo lo spazio bianco prima dell'inizio del segnale
            ax.margins(x=0)
            ax.set_title( f'{self.muscle_name}',fontweight="bold")
            ax.set_xlabel('hh:mm:ss',fontsize=12)
            ax.tick_params(labelsize=10)
            plt.subplots_adjust(left  = 0.07, bottom = 0.18, top=0.90, right = 0.93,hspace = 0.8)

            def write_features():
                xlim=ax.get_xlim() #considero i limiti del segnale
                self.xin=int(xlim[0])
                self.xfin=int(xlim[1])
                self.campione_iniziale=int(xlim[0]*self.fs_emg) #converto i secondi in campioni
                self.campione_finale=int(xlim[1]*self.fs_emg) #converto i secondi in campioni
                self.time_display=time_convert([self.xin,self.xfin]) #converto il tempo in una stringa nel formato %H:%M:%S 
                
                #calcolo le feature sul segnale filtrato nell'intervallo selezionato
                self.mav=MAV(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.rms=RMS(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.iemg = IEMG(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.var = VAR(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.wl = WL(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.ssc = SSC(self.filter_dato1[self.campione_iniziale:self.campione_finale].values,self.th)
                self.wamp = WAMP(self.filter_dato1[self.campione_iniziale:self.campione_finale].values,self.th)
                self.zero_crossings = ZC(self.filter_dato1[self.campione_iniziale:self.campione_finale].values)
                self.sample_on_sec = len(self.filter_dato1[self.campione_iniziale:self.campione_finale])/self.fs_emg
                self.zcr = self.zero_crossings/self.sample_on_sec
                self.freqs, self.psd = signal.welch(self.filter_dato1[self.campione_iniziale:self.campione_finale].values, self.fs_emg)
                self.fmean=MNF(self.freqs,self.psd)
                self.fmedian=MDF(self.freqs,self.psd)
                
                #stampo le features nell'editor
                self.textarea.configure(state='normal')
                if(self.first_feature): #se era la prima volta che calcolavo le features, stampo un header
                    self.textarea.insert(tk.END, f"\n\t\t\t\t\t\tMAV\t  RMS\t  IEMG\t\tVAR\t\tWL\t\tSSC\tWAMP\t ZC\tMNF\tMDF")
                    self.first_feature=False
                self.textarea.insert(tk.END, f"\n\n  {self.muscle_name}\t  {self.time_display[0]} - {self.time_display[1]}\t\t\t")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.mav,2))}")
                self.textarea.insert(tk.END, f"\t  {str(round(self.rms,2))}")
                self.textarea.insert(tk.END, f"\t  {str(round(self.iemg,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.var,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.wl,2))}")
                self.textarea.insert(tk.END, f"\t\t{str(round(self.ssc,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.wamp,2))}")
                self.textarea.insert(tk.END, f"\t {str(round(self.zero_crossings,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.fmean,2))}")
                self.textarea.insert(tk.END, f"\t{str(round(self.fmedian,2))}\n")

                #una volta terminata la scrittura, disabilito l'editor
                self.textarea.configure(state='disabled')
            
            def Add2ClipBoard():
                """
                adds features to clipboard
                """
                import pyperclip
                text=self.textarea.get(1.0,tk.END)
                pyperclip.copy(f'{text}')
            
            self.compute_button.destroy()
            self.clear_button.destroy()
            self.copy_button.destroy()

            self.toolbar_compute.pack_forget()
            self.toolbar_compute=None

            self.canvas_compute.get_tk_widget().pack_forget()
            self.canvas_compute=None

            self.canvas_compute = FigureCanvasTkAgg(self.fig_compute, master=self.tab_editor)  # A tk.DrawingArea.
            self.canvas_compute.draw()
            self.canvas_compute.get_tk_widget().configure(width=1,height=1)
            self.canvas_compute.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH,expand=True)
            #self.toolbar_compute.pack_forget()
            self.toolbar_compute = NavigationToolbar2Tk(self.canvas_compute, self.tab_editor)
            self.compute_button = tk.Button(master=self.toolbar_compute, bg='white',text="COMPUTE FEATURES", command=write_features)
            self.compute_button.place(relx=0.25)
            self.clear_button = tk.Button(master=self.toolbar_compute, bg='white',text="CLEAR FEATURES", command= lambda: self.clear_editor())
            self.clear_button.place(relx=0.45)
            self.copy_button = tk.Button(master=self.toolbar_compute, bg='white',text="ADD TO CLIPBOARD", command=Add2ClipBoard)
            self.copy_button.place(relx=0.65)
            self.toolbar_compute.update()
            self.canvas_compute.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            
            self.tab_editor.update()
            self.tabControl.select(self.tab_editor)
    
    #funzione per calcolare le features su finestre del segnale e stamparle nell'editor come media +/- std su tutte le finestre, alla pressione dell'apposito bottone del menù    
    def window_features(self,id=''):
        """computes features on consecutive window_size lenght segments. Segments are spaced by overlapping time.
        """
        if id=='': #di default le features sono calcolate per il muscolo sotto investigazione
            id=self.ID_channel_under_investigation
        #se le features non sono state ancora calcolate
        if not self.features:
            #inizializzazione array che conterrano le features 
            self.arms=[]
            self.amav=[]                                                           
            self.aiemg=[]
            self.avar=[]
            self.awl=[]
            self.assc=[]
            self.awamp=[]
            self.azero_crossings=[]                                                       
            self.amnf=[]                                                                                                       
            self.amdf=[]

            win2 = self.window_size * self.fs_emg  #utilizzo questo numero di campioni per la stima dello spettro con welch
            self.window_data=[]
            for i in range(0,len(self.Df_Emg_Filtered.iloc[:,id]),round(self.overlap*self.fs_emg)):#parte da zero e si sposta di un periodo pari a overlap
                if((i+round(self.window_size*self.fs_emg))>len(self.Df_Emg_Filtered.iloc[:,id])): #controlla se esce dal segnale
                    #aggiunta agli array dei valori delle features
                    self.window_data.append(self.Df_Emg_Filtered.iloc[:,id][i:].values)
                else:
                    #aggiunta agli array dei valori delle features
                    self.window_data.append(self.Df_Emg_Filtered.iloc[:,id][i:i+round(self.window_size*self.fs_emg)].values)

            start=datetime.datetime.now()
            agents = 4
            with multiprocessing.Pool(processes=agents) as pool:
                self.amav = pool.map(MAV,self.window_data)
                self.arms = pool.map(RMS,self.window_data)
                self.aiemg = pool.map(IEMG,self.window_data)
                self.avar = pool.map(VAR,self.window_data)
                self.awl = pool.map(WL,self.window_data)
                f_SSC = partial(function, SSC, self.th)
                self.assc = pool.map(f_SSC,self.window_data)
                f_WAMP = partial(function, WAMP, self.th)
                self.awamp = pool.map(f_WAMP,self.window_data)
                self.azero_crossings = pool.map(ZC,self.window_data)
                f_MNF = partial(function_spectrum, MNF,self.fs_emg)
                self.amnf = pool.map(f_MNF,self.window_data)
                f_MDF = partial(function_spectrum, MDF,self.fs_emg)
                self.amdf = pool.map(f_MDF,self.window_data)
    
            #trasformo le liste in np.array
            self.amav=np.array(self.amav)
            self.arms=np.array(self.arms)
            self.aiemg=np.array(self.aiemg)
            self.avar=np.array(self.avar)
            self.awl=np.array(self.awl)
            self.assc=np.array(self.assc)
            self.awamp=np.array(self.awamp)
            self.azero_crossings=np.array(self.azero_crossings)
            self.amnf=np.array(self.amnf)
            self.amdf=np.array(self.amdf)

            self.features=True #variabile booleana che diventa vera quando vengono calcolate le features
            #istanti temporali features
            tempo_features=[]
            for microseconds in range(int(self.window_size*1000000/2),int(self.overlap*1000000*len(self.aiemg)),int(self.overlap*1000000)):
                seconds = microseconds // 1000000
                microseconds=microseconds % 1000000
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60
                tempo_features.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))
            
            d=None
            #creo un dataframe contenente tutte le features
            d={'MAV': self.amav[:len(tempo_features)], 
                'RMS': self.arms[:len(tempo_features)], 
                'IEMG':self.aiemg[:len(tempo_features)],
                'VAR': self.avar[:len(tempo_features)], 
                'WL': self.awl[:len(tempo_features)], 
                'SSC': self.assc[:len(tempo_features)],
                'WAMP': self.awamp[:len(tempo_features)], 
                'ZC': self.azero_crossings[:len(tempo_features)], 
                'MNF': self.amnf[:len(tempo_features)], 
                'MDF': self.amdf[:len(tempo_features)]
                }

            self.list_Df_features[id]=None
            self.list_Df_features[id]=pd.DataFrame(data=d,index=tempo_features) #aggiungo alla lista dei dataframe conteneti le features, quello appena calcolato
            d=None

    def set_filter(self):
        """allows user to set properties of the band pass filter
        """
        self.ID_filter_muscle=self.ID_channel_under_investigation 
        self.id_filter=self.ID_channel_under_investigation #il muscolo che verrà mostrato inizialmente è pari a quello con id self.ID_channel_under_investigation
        self.Df_Test_Filtered=self.Df_Emg_Filtered.copy() #datafrme per il test dei parametri del filtro
        
        def close():
            plt.figure(self.fig_filter.number).clear()
            plt.close(self.fig_filter)
            
            self.next_channel_filter.destroy()
            self.next_channel_filter=None

            self.toolbar_filter.pack_forget()
            self.toolbar_filter=None
                
            self.canvas_settings.get_tk_widget().pack_forget()
            self.canvas_settings=None

            self.settings_frame.destroy()
            self.welcome_label.destroy()
            self.low_label.destroy()
            self.low_lim_label.destroy()
            self.high_label.destroy()
            self.high_lim_label.destroy()
            self.order_label.destroy()
            self.order_lim_label.destroy()
            self.low_input.destroy()
            self.high_input.destroy()
            self.order_input.destroy()
            self.default_button.destroy()
            self.draw_button.destroy()
            self.apply_button.destroy()
            
            self.apply_button=None
            self.settings_frame=None
            self.welcome_label=None
            self.low_label=None
            self.low_lim_label=None
            self.high_label=None
            self.high_lim_label=None
            self.order_label=None
            self.order_lim_label=None
            self.low_input=None
            self.high_input=None
            self.order_input=None
            self.default_button=None
            self.draw_button=None

            self.plot_frame.destroy()
            self.plot_frame=None

            self.Df_Test_Filtered=None

            try:
                self.frequency_setting.destroy()   
                self.frequency_setting=None
            except:
                pass

            self.window_filter.destroy()
            self.window_filter=None
            
        def default():
            #mostro i parametri di default
            self.high_input.delete(0,'end')
            self.high_input.insert(0,self.default_high)
            self.low_input.delete(0,'end')
            self.low_input.insert(0,self.default_low)
            self.order_input.delete(0,'end')
            self.order_input.insert(0,self.default_order)

        #show plot mostra il risultato dell'applicazione del nuovo filtro
        def show_plot():
            #se i parametri rispettano le limitazioni aggiorno il dataframe di test e plotto il segnale raw e il segnale filtrato
            if self.low_input.get() and self.high_input.get() and self.order_input.get(): #se sono presenti entrambi i valori di frequenze e l'ordine del filtro
                if(5<=float(self.low_input.get())<=30 and float(self.low_input.get())<=float(self.high_input.get())<(self.fs_emg/2) and (int(self.order_input.get()) in [3,5,7])): #se i valori inseriti rispettono alcuni criteri

                    self.low_lim_label.configure(text='min 5 Hz  max 30 Hz',fg='black')
                    self.high_lim_label.configure(text=f'max {(self.fs_emg/2)-0.1} Hz',fg='black')
                    self.order_lim_label.configure(text='3-5-7',fg='black')

                    self.test_lowcut=self.low_input.get() #valore della frequenza passa alto
                    self.test_lowcut=float(self.test_lowcut)
                    self.test_highcut=self.high_input.get() #valore della frequenza passo basso
                    self.test_highcut=float(self.test_highcut)
                    self.test_order=self.order_input.get() #ordine del filtro
                    self.test_order=int(self.test_order)
                    #plot segnale raw e filtrato con i nuovi parametri
                    self.Df_Test_Filtered=self.Df_Emg_Raw.apply(lambda x: Implement_Notch_Filter(self.fs_emg,1,50, None, 3, 'butter', 
                                            butter_bandpass_filter(x,self.test_lowcut,self.test_highcut, self.fs_emg, order=self.test_order)))
      
                    self.ax_fig_filter[0].clear()
                    self.Df_Emg_Raw.iloc[:,self.id_filter].plot(ax=self.ax_fig_filter[0],legend=False)
                    self.ax_fig_filter[0].set_title( f'RAW - {self.array_nome_muscoli[self.id_filter]}',fontweight="bold")
                    
                    self.ax_fig_filter[1].clear()
                    self.ax_fig_filter[1].set_title(f'Filtered [Butterworth {self.test_order}°Order, lowcut:  {str(self.test_lowcut)}, highcut: {str(self.test_highcut)}]',fontweight="bold")
                    self.Df_Test_Filtered.iloc[:,self.id_filter].plot(ax=self.ax_fig_filter[1],legend=False,color='red')   

                    self.canvas_settings.get_tk_widget().pack_forget()
                    self.canvas_settings=None
                    self.canvas_settings = FigureCanvasTkAgg(self.fig_filter, master=self.plot_frame)  # A tk.DrawingArea.
                    self.canvas_settings.draw()
                    self.canvas_settings.get_tk_widget().place(relx=0,rely=0,width=w,height=int(3*h/4))
                
                else: #se non rispettano le limitazioni cambio la label rispettiva
                    if not (5<=float(self.low_input.get())<=30):
                        self.low_lim_label.configure(text='min 5 Hz  max 30 Hz, value out of interval',fg='#AD2305')
                    if not (float(self.low_input.get())<=float(self.high_input.get())<(self.fs_emg/2)):
                        if (float(self.high_input.get())<=float(self.low_input.get())):
                            self.high_lim_label.configure(text=f'High frequency must be higher than low frequency',fg='#AD2305')
                        else:
                            self.high_lim_label.configure(text=f'max {(self.fs_emg/2)-0.1} Hz, value out of interval',fg='#AD2305')
                    if not (int(self.order_input.get()) in [3,5,7]):
                        self.order_lim_label.configure(text='3-5-7, value not valid',fg='#AD2305')
        
        #apply mostra una finestra interattiva in cui si può confermare o meno le nuove frequenze per il filtro
        def apply():
            def close_apply():
                self.frequency_setting.destroy()
                self.frequency_setting=None

            def setta_frequenze():
                #setto le frequenze e l'ordine del filtro
                self.lowcut=lowcut1 
                self.highcut=highcut1
                self.order=order
                #filtro i segnali e sostituisco gli RMS
                self.create_dataframes(False)
                self.filter_dato1 = self.Df_Emg_Filtered.iloc[:,self.ID_channel_under_investigation] #canale filtrato preso in esame se si vorrà analizzare un segnale specifico
                self.RMS=self.Df_RMS.iloc[:,self.ID_channel_under_investigation] #RMS del canale selezionato (l'ID del canale è lo stesso ma è cambiato il valore del corrispondente RMS causa filtraggio)

                #SE CAMBIO LE CARATTERISTICHE DEL FILTRO CHIUDO TUTTE LE TAB APERTE
                #tab features
                try:
                    self.tabControl.forget(self.tab_editor) #chiudo la tab se è presente
                    plt.figure(self.fig_compute.number).clear()
                    plt.close(self.fig_compute)
                    self.canvas_compute.get_tk_widget().pack_forget()
                    self.canvas_compute.get_tk_widget().destroy()
                    self.canvas_compute=None
                    self.toolbar_compute.pack_forget()
                    self.toolbar_compute.destroy()
                    self.toolbar_compute=None
            
                    if not self.copy_button.destroy()==None:
                        self.copy_button.destroy()
                        self.copy_button=None

                    if not self.clear_button.destroy()==None:
                        self.clear_button.destroy()
                        self.clear_button=None

                    if not self.compute_button.destroy()==None:
                        self.compute_button.destroy()
                        self.compute_button=None

                    self.check_tab_editor = False #reinizializzo a None la tab
                    
                    if not self.textarea == None: #se c'erano scritte delle features nel'editor quando l'ho chiuso
                        #salvo il contenuto dell'editor in una variabile
                        #(alla prossima pressione del tasto compute, l'editor verrà inizializzato con questo contenuto)
                        self.text_content=self.textarea.get(1.0,tk.END)
                except Exception as e: #la tab non era presente
                    self.check_tab_editor=False #metto comunque a false che indica la presenza della tab
                
                #all channels
                try:   
                    self.tabControl.forget(self.tab_all_channels) #chiudo la tab se è presente
                    self.check_tab_all_channels=False
                    
                    #cerco di liberare il più possibile la memoria
                    for i in range(len(self.ar_fig_all)):
                        plt.figure(self.ar_fig_all[i].number).clear()
                        plt.close(self.ar_fig_all[i]) #chiudo le figure

                    self.ar_fig_all=[] #reinizializzo l'array
                    self.canvas_all_channels.get_tk_widget().pack_forget()
                    self.canvas_all_channels.get_tk_widget().destroy()
                    self.toolbar_all_channels.pack_forget()
                    self.toolbar_all_channels.destroy()
                    self.all_channels_plot_selection.destroy()              

                    self.all_channels_plot_selection=None
                    self.tab_all_channels = None #reinizializzo a None la tab
                
                    self.check_tab_all_channels=False
                    self.canvas_all_channels=None
                    self.toolbar_all_channels=None
                except Exception as e:
                    self.check_tab_all_channels=False

                #fatigue
                try:
                    self.tabControl.forget(self.tab_fatigue) #chiudo la tab se è presente
                    self.check_tab_fatigue=False
                    #cerco di risparmiare memoria
                    for i in range(len(self.ar_fig_fatigue)):
                        plt.figure(self.ar_fig_fatigue[i].number).clear()
                        plt.close(self.ar_fig_fatigue[i])
                    
                    self.ar_fig_fatigue=[] #reinizializzo l'array
                    self.canvas_fatigue.get_tk_widget().pack_forget()
                    self.canvas_fatigue.get_tk_widget().destroy()
                    self.toolbar_fatigue.pack_forget()
                    self.toolbar_fatigue.destroy()
                    self.muscle_selection.destroy()

                    self.muscle_selection=None
                    self.tab_fatigue = None #reinizializzo a None la tab
                    self.check_tab_fatigue=False
                    self.canvas_fatigue=None
                    self.toolbar_fatigue=None
                except Exception as e:
                    self.check_tab_fatigue=False

                #single channel
                try:
                    #ciclo su tutte le tab single channel
                    for tab,id in zip(self.tab_channel,range(len(self.tab_channel))):
                        try:
                            self.tabControl.forget(tab) #provo a chiudere la tab se è presente (altrimenti entra nell'except)

                            #cerco di risparmiare memoria
                            for i in range(np.shape(self.ar_fig)[1]):
                                if not self.ar_fig[id][i]==None:
                                    plt.figure(self.ar_fig[id][i].number).clear()
                                    plt.close(self.ar_fig[id][i])
                                    self.ar_fig[id][i]=None
                            
                            #cerco di risparmiare memoria elinando tutti i widget presenti
                            if not self.canvas_single_channel[id]==None:
                                self.canvas_single_channel[id].get_tk_widget().pack_forget()
                                self.canvas_single_channel[id].get_tk_widget().destroy()
                                self.canvas_single_channel[id]=None
                            
                            if not self.toolbar_single_channel[id]==None:
                                self.toolbar_single_channel[id].pack_forget()
                                self.toolbar_single_channel[id].destroy()
                                self.toolbar_single_channel[id]=None
                            
                            if not self.single_channel_plot_selection[id]==None:
                                self.single_channel_plot_selection[id].destroy()
                                self.single_channel_plot_selection[id]=None

                            if not self.change_features_single_channel[id]==None:
                                self.change_features_single_channel[id].destroy()
                                self.change_features_single_channel[id]=None

                            if not self.change_BLE_single_channel[id]==None:
                                self.change_BLE_single_channel[id].destroy()
                                self.change_BLE_single_channel[id]=None

                            if not self.change_opti_feature_single_channel[id]==None:
                                self.change_opti_feature_single_channel[id].destroy()
                                self.change_opti_feature_single_channel[id]=None

                            self.tab_channel[id] = None #reinizializzo a None la tab
                            self.check_tab_channel[id]=False

                        except Exception as e:
                            self.check_tab_channel[id]=False
                except Exception as e:
                    #print(e)
                    pass

                plt.figure(self.fig_filter.number).clear()
                plt.close(self.fig_filter)
                
                self.next_channel_filter.destroy()
                self.next_channel_filter=None

                self.toolbar_filter.pack_forget()
                self.toolbar_filter=None
                    
                self.canvas_settings.get_tk_widget().pack_forget()
                self.canvas_settings=None

                self.settings_frame.destroy()
                self.welcome_label.destroy()
                self.low_label.destroy()
                self.low_lim_label.destroy()
                self.high_label.destroy()
                self.high_lim_label.destroy()
                self.order_label.destroy()
                self.order_lim_label.destroy()
                self.low_input.destroy()
                self.high_input.destroy()
                self.order_input.destroy()
                self.default_button.destroy()
                self.draw_button.destroy()
                self.apply_button.destroy()
                
                self.apply_button=None
                self.settings_frame=None
                self.welcome_label=None
                self.low_label=None
                self.low_lim_label=None
                self.high_label=None
                self.high_lim_label=None
                self.order_label=None
                self.order_lim_label=None
                self.low_input=None
                self.high_input=None
                self.order_input=None
                self.default_button=None
                self.draw_button=None

                self.plot_frame.destroy()
                self.plot_frame=None

                #chiudo le finestre
                self.frequency_setting.destroy()   
                self.window_filter.destroy()
                self.window_filter=None
                self.frequency_setting=None
                self.Df_Test_Filtered=None

            def annulla_cambiamento():
                #annullo il cambiamento delle frequenze
                self.frequency_setting.destroy()
                self.frequency_setting=None
            
            if self.frequency_setting == None:
                #quando premo 'apply' se i valori rispettano i requisiti mostro una seconda finestra in cui è possibile confermare la scelta 
                if self.low_input.get() and self.high_input.get() and self.order_input.get():
                    if(5<=float(self.low_input.get())<=30 and float(self.low_input.get())<=float(self.high_input.get())<(self.fs_emg/2) and (int(self.order_input.get()) in [3,5,7])):
                        self.low_lim_label.configure(text='min 5 Hz  max 30 Hz',fg='black')
                        self.high_lim_label.configure(text=f'max {(self.fs_emg/2)-0.1} Hz',fg='black')
                        self.order_lim_label.configure(text='3-5-7',fg='black')
                        
                        lowcut1=self.low_input.get()
                        lowcut1=float(lowcut1)
                        highcut1=self.high_input.get()
                        highcut1=float(highcut1)  
                        order=self.order_input.get()
                        order=int(order)
                        
                        self.frequency_setting=tk.Toplevel()
                        self.frequency_setting.title("Set Frequencies")
                        self.frequency_setting.geometry("400x100")
                        self.frequency_setting.protocol("WM_DELETE_WINDOW",close_apply)
                        #geometria finestra centrata
                        w = 400 # width for the Tk self
                        h = 100 # height for the Tk self

                        # get screen width and height
                        ws = self.frequency_setting.winfo_screenwidth() # width of the screen
                        hs = self.frequency_setting.winfo_screenheight() # height of the screen

                        # calculate x and y coordinates for the Tk self window
                        x = (ws/2) - (w/2)
                        y = (hs/2) - (h/2)

                        # set the dimensions of the screen 
                        # and where it is placed
                        self.frequency_setting.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
                        
                        self.frequency_setting.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')
                        self.frequency_setting.configure(background='#C0C0C0')
                        self.frequency_setting.resizable(False,False)
                        description_label=tk.Label(self.frequency_setting, text="Do you want to set these frequencies?",font=('Ubuntu','14'),fg='black',bg='#C0C0C0')
                        description_label.place(x=25,y=20)
                        ok_button= tk.Button(self.frequency_setting, text="Yes", command=lambda: setta_frequenze(),background='black',foreground='white',activebackground='white',activeforeground='black') #se premo OK richiama la funzione setta_frequenze per cui cambia le frequenze e filtra il dato
                        ok_button.place(x=100,y=50,width=75,heigh=40)
                        annulla_button= tk.Button(self.frequency_setting, text="No", command=lambda: annulla_cambiamento(),background='black',foreground='white',activebackground='white',activeforeground='black') #se premo annulla le frequenze non cambiano
                        annulla_button.place(x=225,y=50,width=75,heigh=40)
                        
                        def enter(button):
                            button['background'] = 'white'
                            button['foreground'] = 'black' 
                        def leave(button):
                            button['background'] = 'black'
                            button['foreground'] = 'white'

                        ok_button.bind("<Enter>", lambda event,button=ok_button: enter(button))
                        ok_button.bind("<Leave>", lambda event,button=ok_button: leave(button))
                        annulla_button.bind("<Enter>", lambda event,button=annulla_button: enter(button))
                        annulla_button.bind("<Leave>", lambda event,button=annulla_button: leave(button))

                    else: #se non rispettano i requisiti cambio le label
                        if not (5<=float(self.low_input.get())<=30):
                            self.low_lim_label.configure(text='min 5 Hz  max 30 Hz, value out of interval',fg='#AD2305')
                        if not (float(self.low_input.get())<=float(self.high_input.get())<(self.fs_emg/2)):
                            if (float(self.high_input.get())<=float(self.low_input.get())):
                                self.high_lim_label.configure(text=f'High frequency must be higher than low frequency',fg='#AD2305')
                            else:
                                self.high_lim_label.configure(text=f'max {(self.fs_emg/2)-0.1} Hz, value out of interval',fg='#AD2305')
                        if not (int(self.order_input.get()) in [3,5,7]):
                            self.order_lim_label.configure(text='3-5-7, value not valid',fg='#AD2305')
                else: #se era già presente una finestra per confermare le nuove frequenze la porto in primo piano
                    self.frequency_setting.lift()

        if self.window_filter == None: #se non è presente la finestra per i test dei parametri
            #inizializzazione e apertura nuova finestra per il settaggio delle frequenze
            self.window_filter=tk.Toplevel(master=self.master)
            self.window_filter.title("Filter Settings")
            self.window_filter.protocol("WM_DELETE_WINDOW",close)
            #geometria finestra centrata
            w = 1280 # width for the Tk self
            h = 720 # height for the Tk self

            # get screen width and height
            ws = self.window_filter.winfo_screenwidth() # width of the screen
            hs = self.window_filter.winfo_screenheight() # height of the screen

            # calculate x and y coordinates for the Tk self window
            x = (ws/2) - (w/2) + 30
            y = (hs/2) - (h/2) + 30

            # set the dimensions of the screen 
            # and where it is placed
            self.window_filter.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        
            self.window_filter.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')

            self.window_filter.configure(background='black')
            self.window_filter.resizable(False,False)

            self.settings_frame=tk.Frame(self.window_filter,width=w,height=int(h/4))
            self.settings_frame.place(relx=0,rely=0)
            self.settings_frame['bg']='#C0C0C0'
            self.welcome_label=tk.Label(self.settings_frame, text="Butterworth filter",font=('Ubuntu','14'),fg='black',bg='#C0C0C0')
            self.welcome_label.place(x=10,y=10)
            self.low_label=tk.Label(self.settings_frame, text="LowCut Frequency",font=('Ubuntu','10'),fg='black',bg='#C0C0C0')
            self.low_label.place(relx=0.15,rely=0.20)
            self.low_lim_label=tk.Label(self.settings_frame, text=f'min 5 Hz  max 30 Hz',font=('Ubuntu','8'),fg='black',bg='#C0C0C0')
            self.low_lim_label.place(relx=0.35,rely=0.21)
            self.high_label=tk.Label(self.settings_frame, text="HighCut Frequency",font=('Ubuntu','10'),fg='black',bg='#C0C0C0')
            self.high_label.place(relx=0.15,rely=0.50)
            self.high_lim_label=tk.Label(self.settings_frame, text=f'max {(self.fs_emg/2)-0.1} Hz',font=('Ubuntu','8'),fg='black',bg='#C0C0C0')
            self.high_lim_label.place(relx=0.35,rely=0.51)
            self.order_label=tk.Label(self.settings_frame, text="Filter Order",font=('Ubuntu','10'),fg='black',bg='#C0C0C0')
            self.order_label.place(relx=0.15,rely=0.8)
            self.order_lim_label=tk.Label(self.settings_frame, text='3-5-7',font=('Ubuntu','8'),fg='black',bg='#C0C0C0')
            self.order_lim_label.place(relx=0.35,rely=0.81)
            self.low_input=tk.Entry(self.settings_frame,width=10,justify='right')
            self.low_input.insert(0,self.lowcut)
            self.low_input.place(relx=0.3,rely=0.2)
            self.high_input=tk.Entry(self.settings_frame,width=10,justify='right')
            self.high_input.insert(0,self.highcut)
            self.high_input.place(relx=0.3,rely=0.5)
            self.order_input=tk.Entry(self.settings_frame,width=10,justify='right')
            self.order_input.insert(0,self.order)
            self.order_input.place(relx=0.3,rely=0.8)
            self.default_button= tk.Button(self.settings_frame, text="Default", command=lambda: default() ,background='black',foreground='white',activebackground='white',activeforeground='black')
            self.default_button.place(relx=0.01,rely=0.4,heigh=50,width=125)
            self.draw_button= tk.Button(self.settings_frame, text="Show results", command=lambda: show_plot() ,background='black',foreground='white',activebackground='white',activeforeground='black')
            self.draw_button.place(relx=0.58,rely=0.4,heigh=50,width=125)
            self.apply_button= tk.Button(self.settings_frame, text="Apply", command=lambda: apply(),background='black',foreground='white',activebackground='white',activeforeground='black')
            self.apply_button.place(relx=0.72,rely=0.4,heigh=50,width=125)

            def enter(button):
                button['background'] = 'white'
                button['foreground'] = 'black' 
            def on_leave(button):
                button['background'] = 'black'
                button['foreground'] = 'white'

            self.draw_button.bind("<Enter>", lambda event,button=self.draw_button: enter(button))
            self.draw_button.bind("<Leave>", lambda event,button=self.draw_button: on_leave(button))
            self.apply_button.bind("<Enter>", lambda event,button=self.apply_button: enter(button))
            self.apply_button.bind("<Leave>", lambda event,button=self.apply_button: on_leave(button))
            self.default_button.bind("<Enter>", lambda event,button=self.default_button: enter(button))
            self.default_button.bind("<Leave>", lambda event,button=self.default_button: on_leave(button))

            #creazione del frame per mostrare il plot 
            self.plot_frame=tk.Frame(self.window_filter,width=w,height=int(3*h/4))
            self.plot_frame.place(relx=0,rely=0.25)

            self.fig_filter, self.ax_fig_filter = plt.subplots(2, sharex=True)
            self.channel_under_investigation.plot(ax=self.ax_fig_filter[0],legend=False)
            self.ax_fig_filter[0].set_title( f'RAW - {self.muscle_name}',fontweight="bold")
            self.ax_fig_filter[0].tick_params(labelsize=10)
            
            self.filter_dato1.plot(ax=self.ax_fig_filter[1],legend=False,color='red')
            self.ax_fig_filter[1].set_title(f'Filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)}, highcut: {str(self.highcut)}]',fontweight="bold")
            self.ax_fig_filter[1].set_xlabel('hh:mm:ss',fontsize=12)
            self.ax_fig_filter[1].tick_params(labelsize=10)
            plt.subplots_adjust(left  = 0.07, bottom = 0.16, top=0.93, right = 0.98,hspace = 0.8)
            
            def next_muscle():
                self.ID_filter_muscle=self.ID_filter_muscle+1 #la variabile che identifica il muscolo da mostrare aumenta di 1
                self.id_filter=self.ID_filter_muscle % len(self.Df_Emg_Filtered.columns) #calcolo il modulo per ripartire dall'inizio quando termino tutti i muscoli
                
                self.ax_fig_filter[0].clear()
                self.Df_Emg_Raw.iloc[:,self.id_filter].plot(ax=self.ax_fig_filter[0],legend=False)
                self.ax_fig_filter[0].set_title( f'RAW - {self.array_nome_muscoli[self.id_filter]}',fontweight="bold")
            
                self.ax_fig_filter[1].clear()
                self.Df_Test_Filtered.iloc[:,self.id_filter].plot(ax=self.ax_fig_filter[1],legend=False,color='red')
                self.ax_fig_filter[1].set_title(f'Filtered [Butterworth {self.test_order}°Order, lowcut:  {str(self.test_lowcut)}, highcut: {str(self.test_highcut)}]',fontweight="bold")
                
                self.canvas_settings.get_tk_widget().pack_forget()
                self.canvas_settings=None

                self.toolbar_filter.pack_forget()
                self.toolbar_filter=None

                self.canvas_settings = FigureCanvasTkAgg(self.fig_filter, master=self.plot_frame)  # A tk.DrawingArea.
                self.canvas_settings.draw()

                self.toolbar_filter = NavigationToolbar2Tk(self.canvas_settings, self.window_filter)
                
                self.next_channel_filter.destroy()
                self.next_channel_filter=None
                self.next_channel_filter= tk.Button(master=self.toolbar_filter, bg='white',text="Next Muscle", command=lambda: next_muscle())
                self.next_channel_filter.place(relx=0.5)
                
                self.toolbar_filter.update()
                self.canvas_settings.get_tk_widget().place(relx=0,rely=0,width=w,height=int(3*h/4))

            self.canvas_settings = FigureCanvasTkAgg(self.fig_filter, master=self.plot_frame)  # A tk.DrawingArea.
            self.canvas_settings.draw()
            self.toolbar_filter = NavigationToolbar2Tk(self.canvas_settings, self.window_filter)
            self.next_channel_filter= tk.Button(master=self.toolbar_filter, bg='white',text="Next Muscle", command=lambda: next_muscle())
            self.next_channel_filter.place(relx=0.5)
            self.toolbar_filter.update()
            self.canvas_settings.get_tk_widget().place(relx=0,rely=0,width=w,height=int(3*h/4))
        else:
            self.window_filter.lift()

    def single_channel(self,tab_id=''): #funzione che viene chiamata alla pressione di un tasto del menù 'muscles' (se la tab_editor non ha il focus)
        """shows spectrogram, PSD, signals' consistency, features, fit cinematics and BLE if any
        """  
        if tab_id=='': #di default plotta il muscolo sotto investigazione
            ID_channel=self.ID_channel_under_investigation
        else: 
            ID_channel=tab_id

        #viene chiamata quando viene cambiato id del muscolo, se la tab del muscolo non è presente viene creata, altrimenti viene selezionata
        if not self.check_tab_channel[ID_channel]: #se non è stata ancora creata la tab per il muscolo con identificativo 'self.ID_channel_under_investigation'
            self.check_tab_channel[ID_channel]=True
            #creazione della tab specifica per il muscolo con id 'self.ID_channel_under_investigation'
            
            self.tab_channel[ID_channel]=ttk.Frame(self.tabControl)
            self.tabControl.add(self.tab_channel[ID_channel], text=f'{self.array_nome_muscoli[ID_channel]}') # Add the tab

            self.start_stop_event.set()
            self.progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(self.start_stop_event,f'Creating {self.array_nome_muscoli[ID_channel]} plot...',))
            self.progressbar_process.start()

            #CALCOLO FFT
            #xfft,yfft = data_fft(self.channel_under_investigation, self.fs_emg)

            ##PLOT SPETTROGRAMMA
            self.fig_spectrogram[ID_channel],self.ax_spectro = plt.subplots(2, sharex=True)
            self.fig_spectrogram[ID_channel] = plt.gcf()

            self.ax_spectro[0].set_title( f'Filtered [Butterworth {self.order}°Order, lowcut: {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
            self.idx = np.round(np.linspace(0, len(self.Df_Emg_Filtered.iloc[:,ID_channel]) - 1, int(len(self.Df_Emg_Filtered.iloc[:,ID_channel])/self.num_ele))).astype(int)
            self.Df_Emg_Filtered.iloc[:,ID_channel][self.idx].plot(ax=self.ax_spectro[0],color='red',legend=False)
            self.ax_spectro[0].set_xlabel('hh:mm:ss',fontsize=12)
            self.ax_spectro[0].tick_params(labelsize=10)
            
            fr, t, Sxx = signal.spectrogram(self.Df_Emg_Filtered.iloc[:,ID_channel], self.fs_emg, mode = 'magnitude')
   
            self.ax_spectro[1].xaxis.set_major_locator(plt.MaxNLocator(5)) #massimo 5 xticks per una buona visualizzazione
            self.ax_spectro[1].pcolormesh(t, fr, Sxx,vmin=0,vmax=0.3*Sxx.max())
            self.ax_spectro[1].set_title(f'Spectrogram filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
            self.ax_spectro[1].set_ylabel('Hz',fontsize=12)
            self.ax_spectro[1].set_xlabel('hh:mm:ss',fontsize=12)
            self.ax_spectro[1].set_facecolor('black')
            self.ax_spectro[1].tick_params(labelsize=10)
            
            plt.suptitle(f'Spectrogram {self.title_emg}',ha='center',fontweight="bold", fontsize = "15")
            plt.subplots_adjust(left  = 0.07, bottom = 0.09, right = 0.93,hspace = 0.44)
            #FINE PLOT SPECTROGRAM

            ##PLOT PSD
            self.fig_PSD[ID_channel],self.ax=plt.subplots(3, sharex=False)
            self.fig_PSD[ID_channel] = plt.gcf()
            
            win = 4 * self.fs_emg  ## 4 secondi di finestra sull'intero segnale
            #calcolo spettro segnale RAW
            self.Fre, self.Psd = signal.welch(self.Df_Emg_Raw.iloc[:,ID_channel], self.fs_emg, nperseg=win)
            #calcolo spettro segnale filtrato
            self.Fre_w, self.Psd_w = signal.welch(self.Df_Emg_Filtered.iloc[:,ID_channel], self.fs_emg, nperseg=win)

            self.low, self.high = 0.25, 4
            ## genero un array di booleani per individuare la banda di frequenze che ci interessano
            self.idx_delta = np.logical_and(self.Fre >= self.low, self.Fre <= self.high)
            self.idx_delta2 = np.logical_and(self.Fre >= self.high, self.Fre <= self.fs_emg/2)

            #plot del segnale Filtered
            self.ax[0].set_title( f'Filtered [Butterworth {self.order}°Order, lowcut: {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
            self.Df_Emg_Filtered.iloc[:,ID_channel][self.idx].plot(ax=self.ax[0],color='red',legend=False)
            self.ax[0].set_xlabel('hh:mm:ss',fontsize=12)
            self.ax[0].tick_params(labelsize=10) 

            #plot spettro segnale RAW
            self.ax[1].plot(self.Fre, self.Psd, lw=2, color='k')
            self.ax[1].set_title('PSD RAW',fontweight="bold")
            self.ax[1].fill_between(self.Fre, self.Psd, where=self.idx_delta, color='skyblue')
            self.ax[1].fill_between(self.Fre, self.Psd, where=self.idx_delta2, color='orange')
            self.ax[1].set_xlabel('Hz',fontsize=12)
            self.ax[1].set_ylim([0, self.Psd.max() * 1.1])
            self.ax[1].tick_params(labelsize=10) 

            #plot spettro segnale Filtered
            self.ax[2].plot(self.Fre_w, self.Psd_w, lw=2, color='k')
            self.ax[2].set_title(f'PSD [Butterworth {self.order}°Order, lowcut: {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
            self.ax[2].fill_between(self.Fre_w, self.Psd_w, where=self.idx_delta, color='skyblue')
            self.ax[2].fill_between(self.Fre_w, self.Psd_w, where=self.idx_delta2, color='orange')
            self.ax[2].set_xlabel('Hz',fontsize=12)
            self.ax[2].set_ylim([0, self.Psd_w.max() * 1.1]) 
            self.ax[2].tick_params(labelsize=10)       
            self.ax[1].get_shared_x_axes().join(self.ax[1], self.ax[2])

            plt.suptitle(f'PSD {self.title_emg}',ha='center',fontweight="bold", fontsize = "15")
            plt.subplots_adjust(left  = 0.07, bottom = 0.08, right = 0.93,hspace = 0.9)
            #FINE PLOT PSD

            #PLOT COERENZA DEI SEGNALI
            self.fig_coerence[ID_channel], self.axarr = plt.subplots(2, sharex=True)
            self.fig_coerence[ID_channel] = plt.gcf()
            self.fig_coerence[ID_channel].canvas.manager.set_window_title('COERENZA SEGNALI')

            #plot segnale filtrato
            self.axarr[0].set_title(f'Filtered Signal [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} , highcut: {str(self.highcut)}]',fontweight="bold")
            self.Df_Emg_Filtered.iloc[:,ID_channel][self.idx].plot(ax=self.axarr[0],legend=False,color='red')
            self.axarr[0].tick_params(labelsize=10)

            #plot savitsky
            self.axarr[1].set_title('Smoothing (Savitzky-Golay)',fontweight="bold")
            self.Df_Savitzky.iloc[self.idx,ID_channel].plot(ax=self.axarr[1],legend=False,color='green')
            self.axarr[1].tick_params(labelsize=10)

            plt.grid(True)
            plt.suptitle(f'{self.title_emg}\n{self.muscle_name}',ha='center',fontweight="bold", fontsize = "15")
            plt.subplots_adjust(left  = 0.07, bottom = 0.11, right = 0.95, top=0.8, wspace=0.20, hspace = 0.52)
            #FINE PLOT COERENZA TRA I SEGNALI

            #PLOT SEGNALI BLE
            if self.check_BLE:
                start=datetime.datetime.now()
                self.fig_BLE[ID_channel], self.ax_BLE = plt.subplots(2, sharex=True)
                self.fig_BLE[ID_channel] = plt.gcf()

                #plot savitzky
                self.ax_BLE[0].set_title(f'Smoothing (Savitzky-Golay)',fontweight="bold")
                self.Df_Savitzky.iloc[self.idx,ID_channel].plot(ax=self.ax_BLE[0],legend=False,color='red')
                self.ax_BLE[0].tick_params(labelsize=10)

                #plot first BLE measure
                self.ax_BLE[1].set_title(f'{self.Df_BLE.columns[0]}',fontweight="bold")
                self.Df_BLE.iloc[:,0].plot(ax=self.ax_BLE[1],legend=False,color='green')
                self.ax_BLE[1].tick_params(labelsize=10)
                self.ax_BLE[1].set_xlabel('hh:mm:ss', fontsize=12)

                plt.suptitle('BLE Data',ha='center',fontweight="bold", fontsize = "15")
                plt.subplots_adjust(left  = 0.07, bottom = 0.11, right = 0.95, top=0.8, wspace=0.20, hspace = 0.52)
            #FINE PLOT BLE
            
            #PLOT SEGNALE FIT SE PRESENTE
            def make_patch_spines_invisible(ax):
                ax.set_frame_on(True)
                ax.patch.set_visible(False)
                for sp in ax.spines.values():
                    sp.set_visible(False)

            #axes layout according to the presence of .fit and lactate files
            if self.check_fit:
                start=datetime.datetime.now()
                self.fig_fit[ID_channel] = plt.figure()
                self.fig_fit[ID_channel] = plt.gcf()
                gs = GridSpec(5, 1, figure=self.fig_fit[ID_channel])
                
                self.arax=[]
                sns.set_style("ticks")
                if self.check_lattato:#se è presente sia il file .fit che il lattato
                    ax1 = self.fig_fit[ID_channel].add_subplot(gs[0:2])
                    par1 = ax1.twinx() #creazione multipla degli assi
                    par2 = ax1.twinx()
                    par2.spines["right"].set_position(("axes", 1.05)) #posizionamento assi
                    make_patch_spines_invisible(par2)
                    par2.spines["right"].set_visible(True)
                    ax2 = self.fig_fit[ID_channel].add_subplot(gs[2])
                    ax3 = self.fig_fit[ID_channel].add_subplot(gs[3])
                    ax4 = self.fig_fit[ID_channel].add_subplot(gs[4])
                    self.arax.append(ax1)
                    self.arax.append(par1)
                    self.arax.append(par2)
                    self.arax.append(ax2)
                    self.arax.append(ax3)
                    self.arax.append(ax4)
                else: #se è presente il file .fit ma non il lattato
                    ax1 = self.fig_fit[ID_channel].add_subplot(gs[0:2])
                    par1 = ax1.twinx()
                    par2 = ax1.twinx()
                    par2.spines["right"].set_position(("axes", 1.05))
                    make_patch_spines_invisible(par2)
                    par2.spines["right"].set_visible(True)
                    ax2 = self.fig_fit[ID_channel].add_subplot(gs[2:4])
                    ax3 = self.fig_fit[ID_channel].add_subplot(gs[4])
                    self.arax.append(ax1)
                    self.arax.append(par1)
                    self.arax.append(par2)
                    self.arax.append(ax2)
                    self.arax.append(ax3)
    
                #plot power
                self.Df_fit['power'].plot(ax=self.arax[0],style='-g',legend=False)
                self.arax[0].tick_params(labelsize=10)
                self.arax[0].set_xlabel('', fontsize=12)

                #plot cadenza
                self.Df_fit['cadence'].plot(ax=self.arax[1],style='-r',legend=False)
                self.arax[1].tick_params(labelsize=10)
                self.arax[1].set_xlabel('', fontsize=12)

                #plot HR
                try: 
                    self.Df_fit['HeartRateBpm'].plot(ax=self.arax[2],legend=False,style='-b')
                    self.arax[2].tick_params(labelsize=10)
                    self.arax[2].set_xlabel('', fontsize=12)
                    check_hr = True
                    self.arax[0].set_title('POWER - CADENCE - HR',fontweight="bold")
                except:
                    print('Heart rate not present')
                    check_hr = False
                    self.arax[2].set_visible(False)

                #label e colori assi multipli
                self.arax[0].set_ylabel("power")
                self.arax[1].set_ylabel("cadence")
                if check_hr:
                    self.arax[2].set_ylabel("HeartRateBpm")
                self.arax[0].yaxis.label.set_color('green')
                self.arax[1].yaxis.label.set_color('red')
                if check_hr:
                    self.arax[2].yaxis.label.set_color('blue')
                self.arax[0].tick_params(axis='y', colors='green')
                self.arax[1].tick_params(axis='y', colors='red')
                if check_hr:
                    self.arax[2].tick_params(axis='y', colors='blue')
                
                #plot RMS
                self.Df_RMS[self.Df_RMS.columns[ID_channel]].plot(ax=self.arax[3],legend=False,color='orange', linewidth=1)
                self.arax[3].set_title(f'RMS',fontweight="bold")
                self.arax[3].tick_params(labelsize=10)
                self.arax[3].set_xlabel('', fontsize=12)
                self.arax[3].tick_params(labelbottom=False)
                self.arax[3].set_xlim(self.arax[0].get_xlim())

                #plot MNF
                fit = np.polyfit(self.seconds_MNF,self.Df_MNF.iloc[:,ID_channel],1)
                fit_fn = np.poly1d(fit)
                self.Df_MNF.iloc[:,ID_channel].plot(ax=self.arax[4],legend=False,style='-xk')
                df3 = pd.DataFrame(data=fit_fn(self.seconds_MNF), index=self.Df_MNF.index)
                if fit_fn[1]>=0:
                    color='--g'
                else:
                    color='--r'
                df3.plot(ax=self.arax[4],legend=False,style=color)
                self.arax[4].set_title(f'MNF',fontweight="bold")
                self.arax[4].set_xlabel("hh:mm:ss", fontsize=12)
                self.arax[4].tick_params(labelsize=10)
                self.arax[4].set_xlim(self.arax[0].get_xlim())
                
                if self.check_lattato:
                    #plot lattato
                    self.arax[4].tick_params(labelsize=10)
                    self.arax[4].tick_params(labelbottom=False)

                    self.arax[4].set_xlabel('', fontsize=12)
                    self.Df_lattato.plot(ax=self.arax[5],style='-xk',legend=False)
                    self.Df_lattato_regression.plot(ax=self.arax[5],style='-r',legend=False)
                    self.arax[5].set_title(f'LACTATE',fontweight="bold")
                    self.arax[5].set_xlabel('hh:mm:ss', fontsize=12)
                    self.arax[5].tick_params(labelsize=10)
                    self.arax[5].set_xlim(self.arax[0].get_xlim())
                    self.arax[0].get_shared_x_axes().join(self.arax[0], self.arax[1],self.arax[2], self.arax[3],self.arax[4], self.arax[5])
                else:
                    self.arax[4].tick_params(labelsize=10)
                    self.arax[4].set_xlabel('hh:mm:ss', fontsize=12)
                    self.arax[0].get_shared_x_axes().join(self.arax[0], self.arax[1],self.arax[2], self.arax[3],self.arax[4])
    
                plt.subplots_adjust(left  = 0.09, bottom = 0.09, top=0.95, right = 0.91,hspace = 0.8)
            #FINE PLOT FIT
            
            #PLOT FEATURES
            sns.set_style("darkgrid")
            self.fig_features[ID_channel], self.assi_features= plt.subplots(2,1,sharex=True)
            self.fig_features[ID_channel] = plt.gcf()
            self.fig_features[ID_channel].canvas.manager.set_window_title('EMG AND FEATURES')

            #se le features non sono già state calcolate, le calcolo e poi plotto il grafico relativo, altrimenti faccio solo il plot
            if(not self.features):
                self.window_features()
            
            #plot segnale filtrato
            self.assi_features[0].set_title( f'Filtered [Butterworth {self.order}°Order, lowcut: {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
            self.Df_Emg_Filtered.iloc[:,ID_channel][self.idx].plot(ax=self.assi_features[0],legend=False,color='red')
            self.assi_features[0].tick_params(labelsize=10)

            #plot feature
            self.assi_features[1].set_title( f'MAV',fontweight="bold")
            self.list_Df_features[ID_channel].loc[:,'MAV'].plot(ax=self.assi_features[1],visible=True,legend=False,color='green')
            self.assi_features[1].set_xlabel('hh:mm:ss', fontsize=12)
            self.assi_features[1].tick_params(labelsize=10)

            plt.subplots_adjust(left  = 0.07, bottom = 0.11, right = 0.95, top=0.8, wspace=0.20, hspace = 0.52)
            plt.suptitle(f"EMG FEATURES (window size={self.window_size}s window overlap={self.overlap}s)", fontsize = "15",fontweight="bold")
            #fine creazione figure da andare a plottare
            #FINE PLOT FEATURES
            
            ##PLOT CINEMATICA
            if self.check_opti:
                start=datetime.datetime.now()
                self.fig_optitrack[ID_channel],self.ax_opti=plt.subplots(2,sharex=True)
                self.fig_optitrack[ID_channel] = plt.gcf()

                #plot Savitzky
                self.Df_Savitzky.iloc[self.idx,ID_channel].plot(ax=self.ax_opti[0],legend=False,color='red')
                self.ax_opti[0].set_title(f'Smoothing (Savitzky-Golay)',fontweight="bold")
                self.ax_opti[0].tick_params(labelsize=10)
            
                #optitrack
                #select columns of interest
                filter_col = [col for col in self.Df_Opti if col.startswith(f'{self.available_movements[0]}')]
                filtered_Df_Opti=self.Df_Opti[filter_col]
                filtered_Df_Opti.iloc[:,0].plot(ax=self.ax_opti[1], label='X',color='red')
                filtered_Df_Opti.iloc[:,1].plot(ax=self.ax_opti[1], label='Y',color='green')
                filtered_Df_Opti.iloc[:,2].plot(ax=self.ax_opti[1], label='Z',color='blue')
                self.ax_opti[1].legend(loc='best')
                self.ax_opti[1].set_title(f'{self.available_movements[0]}',fontweight="bold")
                self.ax_opti[1].set_xlabel('hh:mm:ss',fontsize=12)
                self.ax_opti[1].tick_params(labelsize=10)

                plt.suptitle('MUSCLE ACTIVATION',fontweight="bold")
                plt.subplots_adjust(left  = 0.07, bottom = 0.11, right = 0.95, top=0.8, wspace=0.20, hspace = 0.52)
            #FINE PLOT CINEMATICA

            #chiudo la barra di progresso
            self.start_stop_event.clear()
            self.progressbar_process=None
            
            #al termine do il focus alla tab appena creata
            self.tab_channel[ID_channel].update()
            self.tabControl.select(self.tab_channel[ID_channel])

            #figure da mostare indipendentemente dalla presenza dei .csv dei BLE,FIT e optitrack
            self.ar_fig[ID_channel]=[self.fig_coerence[ID_channel],
                                    self.fig_spectrogram[ID_channel],
                                    self.fig_PSD[ID_channel],
                                    self.fig_features[ID_channel]]

            #a seconda o meno della presenza dei .csv dei BLE,FIT e optitrack vado ad aggiungere le rispettive figure da mostrare
            self.id_fig_opti=4
            if self.check_BLE:
                self.ar_fig[ID_channel].append(self.fig_BLE[ID_channel])
                self.id_fig_opti=self.id_fig_opti+1
            
            if self.check_fit:
                self.ar_fig[ID_channel].append(self.fig_fit[ID_channel])
                self.id_fig_opti=self.id_fig_opti+1

            if self.check_opti:
                self.ar_fig[ID_channel].append(self.fig_optitrack[ID_channel])
                self.id_optitrack_feature=[0]*self.number_of_channels #optitrack feature sotto investigazione per gli self.number_of_channels canali

            self.id_feature=[0]*self.number_of_channels #emg feature sotto investigazione per gli self.number_of_channels canali
            #creo una canvas specifica per il canale sotto investigazione e mostro i plot
            self.canvas_single_channel[ID_channel] = FigureCanvasTkAgg(self.ar_fig[ID_channel][self.id_single_channel[ID_channel] % np.shape(self.ar_fig)[1]], master=self.tab_channel[ID_channel])  # A tk.DrawingArea.
            self.canvas_single_channel[ID_channel].draw()
            
            def change_plot_single_channel(id):
                """
                changes single channel figure
                """
                def change_optitrack_feature(selected_id_optitrack):
                    """
                    update optitrack fearure
                    """         
                    self.toolbar_single_channel[id_focused_tab].children['!button'].invoke() #risetto i limiti originali  
                    self.single_channel_plot_selection[id_focused_tab].destroy()
                    self.single_channel_plot_selection[id_focused_tab]=None

                    self.change_opti_feature_single_channel[id_focused_tab].destroy()
                    self.change_opti_feature_single_channel[id_focused_tab]=None

                    self.toolbar_single_channel[id_focused_tab].pack_forget()
                    self.toolbar_single_channel[id_focused_tab]=None

                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack_forget()
                    self.canvas_single_channel[id_focused_tab]=None

                    self.id_optitrack_feature[id_focused_tab]=selected_id_optitrack
                    optitrack_feature_name=self.available_movements[selected_id_optitrack]

                    #seleziono le colonne che incominciano con 'optitrack_feature_name' (es Avambraccio Rotation) e plotto le prime 3 colonne (X,Y,Z)
                    filter_col = [col for col in self.Df_Opti if col.startswith(f'{optitrack_feature_name}')]
                    filtered_Df_Opti=self.Df_Opti[filter_col]
                    
                    #optitrack
                    ax1=self.ar_fig[id_focused_tab][id].axes[1]
                    ax1.clear()
                    #self.Df_Opti.iloc[:,selected_id_optitrack].plot(ax=ax1, legend=False,color='green')
                    filtered_Df_Opti.iloc[:,0].plot(ax=ax1,label='X',color='red')
                    filtered_Df_Opti.iloc[:,1].plot(ax=ax1,label='Y',color='green')
                    filtered_Df_Opti.iloc[:,2].plot(ax=ax1,label='Z',color='blue')
                    ax1.legend(loc='best')
                    ax1.set_title(f'{self.available_movements[selected_id_optitrack]}',fontweight="bold")
                    ax1.set_xlabel('hh:mm:ss',fontsize=12)
                    ax1.tick_params(labelsize=10)

                    self.canvas_single_channel[id_focused_tab] = FigureCanvasTkAgg(self.ar_fig[id_focused_tab][id], master=self.tab_channel[id_focused_tab])  # A tk.DrawingArea.
                    self.canvas_single_channel[id_focused_tab].draw()
                    
                    self.toolbar_single_channel[id_focused_tab] = NavigationToolbar2Tk(self.canvas_single_channel[id_focused_tab], self.tab_channel[id_focused_tab])

                    #combobox per la selezione del plot
                    self.single_channel_plot_selection[id_focused_tab]= ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.single_channel_available_plot,state='readonly',width=30)
                    self.single_channel_plot_selection[id_focused_tab].place(relx=0.40,rely=0.2)
                    self.single_channel_plot_selection[id_focused_tab].current(id)
                    self.single_channel_plot_selection[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_plot_single_channel(self.single_channel_plot_selection[id_focused_tab].current()))

                    #aggiungo alla toolbar un combobox che permette di cambiare la feature dell'optitrack
                    self.change_opti_feature_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.available_movements,state='readonly',width=30)
                    self.change_opti_feature_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_opti_feature_single_channel[id_focused_tab].current(selected_id_optitrack)
                    self.change_opti_feature_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_optitrack_feature(self.change_opti_feature_single_channel[id_focused_tab].current()))

                    self.toolbar_single_channel[id_focused_tab].update()
                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                    
                def change_BLE(selected_id_BLE):
                    """
                    update ble feature
                    """
                    self.toolbar_single_channel[id_focused_tab].children['!button'].invoke() #setto i limiti originali
                    self.change_BLE_single_channel[id_focused_tab].destroy()
                    self.change_BLE_single_channel[id_focused_tab]=None

                    self.single_channel_plot_selection[id_focused_tab].destroy()
                    self.single_channel_plot_selection[id_focused_tab]=None

                    self.toolbar_single_channel[id_focused_tab].pack_forget()
                    self.toolbar_single_channel[id_focused_tab]=None

                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack_forget()
                    self.canvas_single_channel[id_focused_tab]=None
                    
                    #plot BLE measure
                    ax1=self.ar_fig[id_focused_tab][id].axes[1]
                    ax1.clear()
                    ax1.set_title(f'{self.Df_BLE.columns[selected_id_BLE]}',fontweight="bold")
                    self.Df_BLE.iloc[:,selected_id_BLE].plot(ax=ax1,legend=False,color='green')
                    ax1.tick_params(labelsize=10)
                    ax1.set_xlabel('hh:mm:ss', fontsize=12)

                    self.canvas_single_channel[id_focused_tab] = FigureCanvasTkAgg(self.ar_fig[id_focused_tab][id], master=self.tab_channel[id_focused_tab])  # A tk.DrawingArea.
                    self.canvas_single_channel[id_focused_tab].draw()
                    
                    self.toolbar_single_channel[id_focused_tab] = NavigationToolbar2Tk(self.canvas_single_channel[id_focused_tab], self.tab_channel[id_focused_tab])

                    #combobox per la selezione del plot
                    self.single_channel_plot_selection[id_focused_tab]= ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.single_channel_available_plot,state='readonly',width=30)
                    self.single_channel_plot_selection[id_focused_tab].place(relx=0.40,rely=0.2)
                    self.single_channel_plot_selection[id_focused_tab].current(id)
                    self.single_channel_plot_selection[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_plot_single_channel(self.single_channel_plot_selection[id_focused_tab].current()))

                    #aggiungo alla toolbar un combobox che permette di cambiare l'informazione mostrata dei BLE
                    self.change_BLE_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.list_available_BLE_Data,state='readonly',width=30)
                    self.change_BLE_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_BLE_single_channel[id_focused_tab].current(selected_id_BLE)
                    self.change_BLE_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_BLE(self.change_BLE_single_channel[id_focused_tab].current()))

                    self.toolbar_single_channel[id_focused_tab].update()
                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                    
                def change_feature(selected_id_feature):
                    """
                    update emg feature
                    """
                    self.toolbar_single_channel[id_focused_tab].children['!button'].invoke() #setto i limiti originali
                    self.id_feature[id_focused_tab]=selected_id_feature
                    
                    self.single_channel_plot_selection[id_focused_tab].destroy()
                    self.single_channel_plot_selection[id_focused_tab]=None

                    self.change_features_single_channel[id_focused_tab].destroy()
                    self.change_features_single_channel[id_focused_tab]=None

                    self.toolbar_single_channel[id_focused_tab].pack_forget()
                    self.toolbar_single_channel[id_focused_tab]=None

                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack_forget()
                    self.canvas_single_channel[id_focused_tab]=None
                    
                    #plot nuova feature
                    ax1=self.ar_fig[id_focused_tab][id].axes[1]
                    ax1.clear()
                    ax1.set_title( f'{self.list_Df_features[id_focused_tab].columns[self.id_feature[id_focused_tab]]}',fontweight="bold")
                    self.list_Df_features[id_focused_tab].iloc[:,self.id_feature[id_focused_tab]].plot(ax=ax1,legend=False,color='green')
                    ax1.set_xlabel('hh:mm:ss', fontsize=12)
                    ax1.tick_params(labelsize=10)
 
                    self.canvas_single_channel[id_focused_tab] = FigureCanvasTkAgg(self.ar_fig[id_focused_tab][id], master=self.tab_channel[id_focused_tab])  # A tk.DrawingArea.
                    self.canvas_single_channel[id_focused_tab].draw()
                    self.toolbar_single_channel[id_focused_tab] = NavigationToolbar2Tk(self.canvas_single_channel[id_focused_tab], self.tab_channel[id_focused_tab])

                    #combobox per la selezione del plot
                    self.single_channel_plot_selection[id_focused_tab]= ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.single_channel_available_plot,state='readonly',width=30)
                    self.single_channel_plot_selection[id_focused_tab].place(relx=0.40,rely=0.2)
                    self.single_channel_plot_selection[id_focused_tab].current(id)
                    self.single_channel_plot_selection[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_plot_single_channel(self.single_channel_plot_selection[id_focused_tab].current()))

                    #aggiungo alla toolbar un button 'change feature' che permette di cambiare la feature mostrata
                    self.change_features_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.list_available_features,state='readonly',width=30)
                    self.change_features_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_features_single_channel[id_focused_tab].current(selected_id_feature)
                    self.change_features_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_feature(self.change_features_single_channel[id_focused_tab].current()))
                    
                    self.toolbar_single_channel[id_focused_tab].update()
                    self.canvas_single_channel[id_focused_tab].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                #ciclo su tutte le possibili tab dei single channel aperte 
                for i in range(self.number_of_channels):
                    #if not self.tab_channel[i] == None: #se è stata creata la tab per il muscolo i-esimo
                    if self.check_tab_channel[i]:
                        self.tab_channel[i].update()
                        if str(self.tab_channel[i]) == self.tabControl.select(): #controllo se la tab i-esima è quella che ha il focus, ovvero determino su quale tab devo andare a cambiare il plot
                            id_focused_tab = i #indice della tab che ha il focus

                #quando cambio plot invoco il tasto 'home' della toolbar per risettare i limiti originali
                self.toolbar_single_channel[id_focused_tab].children['!button'].invoke()
                self.canvas_single_channel[id_focused_tab].get_tk_widget().pack_forget()
                self.canvas_single_channel[id_focused_tab]=None
                #sulla tab che ha il focus vado ad aggiornare la figura mostrata
                self.canvas_single_channel[id_focused_tab] = FigureCanvasTkAgg(self.ar_fig[id_focused_tab][id], master=self.tab_channel[id_focused_tab])  # A tk.DrawingArea.
                self.canvas_single_channel[id_focused_tab].draw()

                self.toolbar_single_channel[id_focused_tab].pack_forget()
                self.toolbar_single_channel[id_focused_tab]=None
                self.toolbar_single_channel[id_focused_tab] = NavigationToolbar2Tk(self.canvas_single_channel[id_focused_tab], self.tab_channel[id_focused_tab])

                #combobox per la selezione del plot
                self.single_channel_plot_selection[id_focused_tab].destroy()
                self.single_channel_plot_selection[id_focused_tab]=None
                self.single_channel_plot_selection[id_focused_tab]= ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.single_channel_available_plot,state='readonly',width=30)
                self.single_channel_plot_selection[id_focused_tab].place(relx=0.40,rely=0.2)
                self.single_channel_plot_selection[id_focused_tab].current(id)
                self.single_channel_plot_selection[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_plot_single_channel(self.single_channel_plot_selection[id_focused_tab].current()))

                #se viene mostrata la figura contenente la feature
                if id==3: 
                    #aggiungo alla toolbar un combobox che permette di cambiare la feature mostrata
                    #print(self.change_features_single_channel[id_focused_tab])
                    self.change_features_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.list_available_features,state='readonly',width=30)
                    self.change_features_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_features_single_channel[id_focused_tab].current(self.id_feature[id_focused_tab])
                    self.change_features_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_feature(self.change_features_single_channel[id_focused_tab].current()))
                
                #se viene mostrata la figura dei BLE
                if id==4 and self.check_BLE: 
                    #aggiungo alla toolbar un combobox che permette di cambiare l'informazione mostrata dei BLE
                    self.change_BLE_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.list_available_BLE_Data,state='readonly',width=30)
                    self.change_BLE_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_BLE_single_channel[id_focused_tab].current(0)
                    self.change_BLE_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_BLE(self.change_BLE_single_channel[id_focused_tab].current()))

                #se viene mostrato l'optitrack
                if id==self.id_fig_opti and self.check_opti:
                    #aggiungo alla toolbar un combobox che permette di cambiare la feature dell'optitrack
                    self.change_opti_feature_single_channel[id_focused_tab] = ttk.Combobox(master=self.toolbar_single_channel[id_focused_tab],values=self.available_movements,state='readonly',width=30)
                    self.change_opti_feature_single_channel[id_focused_tab].place(relx=0.6,rely=0.2)
                    self.change_opti_feature_single_channel[id_focused_tab].current(self.id_optitrack_feature[id_focused_tab])
                    self.change_opti_feature_single_channel[id_focused_tab].bind("<<ComboboxSelected>>",lambda e: change_optitrack_feature(self.change_opti_feature_single_channel[id_focused_tab].current()))
                
                self.toolbar_single_channel[id_focused_tab].update()
                self.canvas_single_channel[id_focused_tab].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            
            #creo una toolbar specifica per il canale sotto investigazione e aggiungo un button per poter cambiare il grafico mostrato
            self.toolbar_single_channel[ID_channel] = NavigationToolbar2Tk(self.canvas_single_channel[ID_channel], self.tab_channel[ID_channel])

            #combobox per la selezione del plot
            self.single_channel_plot_selection[ID_channel]= ttk.Combobox(master=self.toolbar_single_channel[ID_channel],values=self.single_channel_available_plot,state='readonly',width=30)
            self.single_channel_plot_selection[ID_channel].place(relx=0.40,rely=0.2)
            self.single_channel_plot_selection[ID_channel].current(0)
            self.single_channel_plot_selection[ID_channel].bind("<<ComboboxSelected>>",lambda e: change_plot_single_channel(self.single_channel_plot_selection[ID_channel].current()))

            self.toolbar_single_channel[ID_channel].update()
            self.canvas_single_channel[ID_channel].get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        else: #se era già stata creata la tab per il muscolo con id 'self.ID_channel_under_investigation'
            self.tab_channel[ID_channel].update() #update tabs
            self.tabControl.select(self.tab_channel[ID_channel])

    def all_channels(self):
        """
        shows Filtered signals, RMSs , spectrograms, PSDs and MNFs of all channels
        """
        if not self.check_tab_all_channels: #se la tab che mostra i plot alla pressione del tasto 'all channels' non è presente la creo
            #DETERMINAZIONE LAYOUT IN BASE AL NUMERO DI CANALI UTILIZZATI
            if not self.number_of_channels==1:
                if self.number_of_channels==2:
                    self.rows=2
                    self.columns=1
                elif self.number_of_channels==3:
                    self.rows=3
                    self.columns=1
                elif self.number_of_channels==4:
                    self.rows=2
                    self.columns=2
                elif self.number_of_channels==5:
                    self.rows=3
                    self.columns=2
                elif self.number_of_channels==6:
                    self.rows=3
                    self.columns=2
                elif self.number_of_channels==7:
                    self.rows=4
                    self.columns=2
                else:
                    self.rows=4
                    self.columns=2

                self.check_tab_all_channels=True

                self.ar_fig_all=[] #svuoto la lista che conterrà i plot generati alla pressione del tasto 'all channels'
                self.tab_all_channels=ttk.Frame(self.tabControl)
                self.tabControl.add(self.tab_all_channels, text=f'All channels') # Add the tab

                #PARTENZA BARRA DI PROGRESSO
                self.start_stop_event.set() #quando parte l'evento start/stop è True
                self.progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(self.start_stop_event,'Creating all channels plot...',))
                self.progressbar_process.start()
                
                #PLOT DEGLI self.number_of_channels CANALI FILTRATI
                self.fig_all_filtered, self.axarrCh = plt.subplots(self.rows,self.columns, sharex=True, sharey=False)
                self.fig_all_filtered = plt.gcf()
                self.fig_all_filtered.canvas.manager.set_window_title('EMG FILTERED')
                
                idx = np.round(np.linspace(0, len(self.Df_Emg_Filtered.iloc[:,0]) - 1, int(len(self.Df_Emg_Filtered.iloc[:,0])/self.num_ele))).astype(int)

                for i,ax_emg_filtered in enumerate(self.axarrCh.flat):
                    if i < self.number_of_channels:
                        ax_emg_filtered.xaxis.set_major_locator(plt.MaxNLocator(5))
                        ax_emg_filtered.set_title(self.array_nome_muscoli[i],fontweight="bold")
                        self.Df_Emg_Filtered.iloc[idx,i].plot(ax=ax_emg_filtered,legend=False)
                        ax_emg_filtered.set_xlabel("hh:mm:ss", fontsize=12)
                        ax_emg_filtered.tick_params(labelsize=10)

                if self.number_of_channels == 5:
                    self.fig_all_filtered.delaxes(self.axarrCh[2,1])
                    self.axarrCh[1,1].tick_params(labelbottom=True,labelsize=10)

                if self.number_of_channels == 7:
                    self.fig_all_filtered.delaxes(self.axarrCh[3,1])
                    self.axarrCh[2,1].tick_params(labelbottom=True,labelsize=10)
                
                plt.suptitle(f'{self.title_emg}\n Filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} highcut: {str(self.highcut)}]' , fontsize = "13",fontweight="bold")
                plt.subplots_adjust(left  = 0.07, top=0.85, bottom = 0.09, right = 0.95,hspace = 0.9)

                #PLOT DEGLI self.number_of_channels SPETTROGRAMMI DI TUTTI I CANALI
                self.fig_all_spectrogram, self.ax_all_spectrogram =plt.subplots(self.rows,self.columns, sharex=True)
                self.fig_all_spectrogram = plt.gcf()
                self.fig_all_spectrogram.canvas.manager.set_window_title('SPETTROGRAMMI')

                for i,ax_all_spectrogram, in enumerate(self.ax_all_spectrogram.flat):
                    if i < self.number_of_channels:
                        if i==self.number_of_channels-1:
                            self.display_spettrogramma(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_spectrogram,True)
                        
                        elif self.columns==2 and (i==self.number_of_channels-2):
                            self.display_spettrogramma(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_spectrogram,True)

                        else:
                            self.display_spettrogramma(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_spectrogram)

                if self.number_of_channels == 5:
                    self.fig_all_spectrogram.delaxes(self.ax_all_spectrogram[2,1])

                if self.number_of_channels == 7:
                    self.fig_all_spectrogram.delaxes(self.ax_all_spectrogram[3,1])

                plt.suptitle(f'{self.title_emg}\n Spectrogram Filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} highcut: {str(self.highcut)}]', fontsize = "13",fontweight="bold")
                plt.subplots_adjust(left  = 0.07, bottom = 0.09, top=0.85, right = 0.95,hspace = 0.9)

                #PLOT DEGLI self.number_of_channels PSD DI TUTTI I CANALI
                self.fig_all_PSD, self.ax_all_psd = plt.subplots(self.rows,self.columns, sharex=True,sharey=True)
                self.fig_all_PSD = plt.gcf()
                self.fig_all_PSD.canvas.manager.set_window_title('PSD')

                for i,ax_all_psd, in enumerate(self.ax_all_psd.flat):
                    if i < self.number_of_channels:
                        if i==self.number_of_channels-1:
                            self.display_PSD(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_psd,True)

                        elif self.columns==2 and (i==self.number_of_channels-2):
                            self.display_PSD(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_psd,True)
                        
                        else:
                            self.display_PSD(self.Df_Emg_Filtered.iloc[:,i],self.array_nome_muscoli[i],ax_all_psd)

                if self.number_of_channels == 5:
                    self.fig_all_PSD.delaxes(self.ax_all_psd[2,1])

                if self.number_of_channels == 7:
                    self.fig_all_PSD.delaxes(self.ax_all_psd[3,1])

                plt.suptitle(F'{self.title_emg}\nPSD Filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} highcut: {str(self.highcut)}]', fontsize = "13",fontweight="bold")
                plt.subplots_adjust(left  = 0.07, bottom = 0.09, top=0.85,right = 0.95,hspace = 0.9)

                #PLOT FREQUENZA MEDIA IN FUNZIONE DEL TEMPO DI TUTTI I CANALI
                self.fig_all_MNF, self.ax_all_mnf = plt.subplots(self.rows,self.columns, sharex=True)
                self.fig_all_MNF = plt.gcf()
                self.fig_all_MNF.canvas.manager.set_window_title('MEAN FREQUENCY')

                for i,ax_all_mnf, in enumerate(self.ax_all_mnf.flat):
                    if i < self.number_of_channels:
                        if i==self.number_of_channels-1:
                            self.display_MNF(self.Df_MNF.iloc[:,i],self.array_nome_muscoli[i],ax_all_mnf,True)
                            ax_all_mnf.set_xlim(self.axarrCh.flat[0].get_xlim())

                        elif self.columns==2 and (i==self.number_of_channels-2):
                            self.display_MNF(self.Df_MNF.iloc[:,i],self.array_nome_muscoli[i],ax_all_mnf,True)
                            ax_all_mnf.set_xlim(self.axarrCh.flat[0].get_xlim())
                        
                        else:
                            self.display_MNF(self.Df_MNF.iloc[:,i],self.array_nome_muscoli[i],ax_all_mnf)
                            ax_all_mnf.set_xlim(self.axarrCh.flat[0].get_xlim())

                if self.number_of_channels == 5:
                    self.fig_all_MNF.delaxes(self.ax_all_mnf[2,1])

                if self.number_of_channels == 7:
                    self.fig_all_MNF.delaxes(self.ax_all_mnf[3,1])
                
                plt.suptitle(f"{self.title_emg}\nMEAN FREQUENCY", fontsize = "13",fontweight="bold")
                plt.subplots_adjust(left  = 0.07, bottom = 0.09, top=0.85, right = 0.95,hspace = 0.9)

                #PLOT RMS DI TUTTI I CANALI
                self.fig_all_RMS, self.ax_all_RMS = plt.subplots(self.rows,self.columns, sharex=True)
                self.fig_all_RMS = plt.gcf()
                self.fig_all_RMS.canvas.manager.set_window_title('RMS ALL CHANNELS')
                
                idx = np.round(np.linspace(0, len(self.Df_RMS.iloc[:,0]) - 1, int(len(self.Df_RMS.iloc[:,0])/self.num_ele))).astype(int)
                for i,ax_all_RMS, in enumerate(self.ax_all_RMS.flat):
                    if i < self.number_of_channels:
                        ax_all_RMS.xaxis.set_major_locator(plt.MaxNLocator(5))
                        self.Df_RMS.iloc[idx,i].plot(ax=ax_all_RMS,legend=False,color='orange', linewidth=1)
                        ax_all_RMS.set_title(f'{self.array_nome_muscoli[i]}',fontweight="bold")
                        ax_all_RMS.set_xlabel("hh:mm:ss", fontsize=12)
                        ax_all_RMS.tick_params(labelsize=10)
                
                if self.number_of_channels == 5:
                    self.fig_all_RMS.delaxes(self.ax_all_RMS[2,1])
                    self.ax_all_RMS[1,1].tick_params(labelbottom=True,labelsize=10)

                if self.number_of_channels == 7:
                    self.fig_all_RMS.delaxes(self.ax_all_RMS[3,1])
                    self.ax_all_RMS[2,1].tick_params(labelbottom=True,labelsize=10)

                plt.suptitle(f'{self.title_emg}\nRMS',fontweight="bold",fontsize='13')
                plt.subplots_adjust(left  = 0.07, bottom = 0.09, top=0.85, right = 0.95,hspace = 0.9)

                #chiusura barra di progresso
                self.start_stop_event.clear() #l'evento diventa False per far terminare il processo
                self.progressbar_process=None

                self.tab_all_channels.update()
                self.tabControl.select(self.tab_all_channels) #seleziono la nuova tab creata

                #aggiungo alla lista le figure da plottare
                self.ar_fig_all.append(self.fig_all_filtered)
                self.ar_fig_all.append(self.fig_all_RMS)
                self.ar_fig_all.append(self.fig_all_spectrogram)
                self.ar_fig_all.append(self.fig_all_PSD)
                self.ar_fig_all.append(self.fig_all_MNF)

                self.canvas_all_channels = FigureCanvasTkAgg(self.ar_fig_all[0], master=self.tab_all_channels)  # A tk.DrawingArea.
                self.canvas_all_channels.draw()

                def change_plot_all_channels(id):
                    """
                    change all channels plot
                    """
                    self.toolbar_all_channels.children['!button'].invoke()
                    self.canvas_all_channels.get_tk_widget().pack_forget()
                    self.canvas_all_channels=None
                    self.canvas_all_channels = FigureCanvasTkAgg(self.ar_fig_all[id], master=self.tab_all_channels)  # A tk.DrawingArea.
                    self.canvas_all_channels.draw()
                    
                    self.toolbar_all_channels.pack_forget()
                    self.toolbar_all_channels=None
                    self.toolbar_all_channels = NavigationToolbar2Tk(self.canvas_all_channels, self.tab_all_channels)
                    
                    self.all_channels_plot_selection.destroy()
                    self.all_channels_plot_selection=None
                    self.all_channels_plot_selection= ttk.Combobox(master=self.toolbar_all_channels,values=self.available_all_channels_plot,state='readonly',width=40)
                    self.all_channels_plot_selection.place(relx=0.40,rely=0.2)
                    self.all_channels_plot_selection.current(id)
                    self.all_channels_plot_selection.bind("<<ComboboxSelected>>",lambda e: change_plot_all_channels(self.all_channels_plot_selection.current()))
        
                    self.canvas_all_channels.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                
                self.toolbar_all_channels = NavigationToolbar2Tk(self.canvas_all_channels, self.tab_all_channels)
                
                self.all_channels_plot_selection= ttk.Combobox(master=self.toolbar_all_channels,values=self.available_all_channels_plot,state='readonly',width=40)
                self.all_channels_plot_selection.place(relx=0.40,rely=0.2)
                self.all_channels_plot_selection.current(0)
                self.all_channels_plot_selection.bind("<<ComboboxSelected>>",lambda e: change_plot_all_channels(self.all_channels_plot_selection.current()))
                
                self.toolbar_all_channels.update()
                self.canvas_all_channels.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            else:
                tk.messagebox.showerror(title='ERROR',message='Just one muscle recorded')
        else: #se la tab non è None vuol dire che era stata aperta
            self.tab_all_channels.update() #update delle tab
            self.tabControl.select(self.tab_all_channels) #la seleziono


    def fatigue(self):
        """shows emg filtered signal, RMS and MNF of different muscles
        """
        if not self.check_tab_fatigue: #se la tab non è presente

            idx_fatigue = np.round(np.linspace(0, len(self.Df_Emg_Filtered) - 1, int(len(self.Df_Emg_Filtered)/self.num_ele))).astype(int)

            self.check_tab_fatigue=True
            self.ar_fig_fatigue=[] #lista che conterrà le figure della analisi della fatica per gli self.number_of_channels canali
            self.tab_fatigue=ttk.Frame(self.tabControl)
            self.tabControl.add(self.tab_fatigue, text=f'Fatigue analysis') # Add the tab

            #avvio barra di progresso
            self.start_stop_event.set()
            self.progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(self.start_stop_event,'Creating fatigue analysis plot...',))
            self.progressbar_process.start()
            
            for i in range(self.number_of_channels): #ciclo per calcolare l'affaticamento su tutti i muscoli                    
                fig, ax = plt.subplots(3,1, sharex=True)
                fig = plt.gcf()
                fig.canvas.manager.set_window_title('FATIGUE ANALYSIS')

                self.ar_fig_fatigue.append(fig) #aggiungo alla lista la figura 
                self.axfatigue[i]=[ax[0],ax[1],ax[2]] #aggiungo alla lista gli assi della figura i-esima

                #plot Filtered signal
                self.axfatigue[i][0].set_title( f'Filtered [Butterworth {self.order}°Order, lowcut:  {str(self.lowcut)} highcut: {str(self.highcut)}]',fontweight="bold")
                self.Df_Emg_Filtered.iloc[idx_fatigue,i].plot(ax=self.axfatigue[i][0],legend=False,color='red')
                self.axfatigue[i][0].margins(x=0)
                self.axfatigue[i][0].tick_params(labelsize=10)

                #plot RMS
                self.axfatigue[i][1].set_title( f'RMS',fontweight="bold")
                #self.Df_RMS.iloc[:,i].plot(ax=self.axfatigue[i][1],kind='area',legend=False,color='yellow')
                idx = np.round(np.linspace(0, len(self.Df_RMS) - 1, int(len(self.Df_RMS)/self.num_ele))).astype(int)
                self.Df_RMS.iloc[idx,i].plot(ax=self.axfatigue[i][1],legend=False,color='orange')
                self.axfatigue[i][1].set_xlim(self.axfatigue[i][0].get_xlim()) 
                self.axfatigue[i][1].tick_params(labelsize=10)
                
                #plot MNF
                fit = np.polyfit(self.seconds_MNF,self.Df_MNF.iloc[:,i],1) #calcolo slope
                fit_fn = np.poly1d(fit)
                self.Df_MNF.iloc[:,i].plot(ax=self.axfatigue[i][2],legend=False,style='-xk')
                df3 = pd.DataFrame(data=fit_fn(self.seconds_MNF), index=self.Df_MNF.index)
                if fit_fn[1]>=0:
                    color='--g'
                else:
                    color='--r'
                df3.plot(ax=self.axfatigue[i][2],legend=False,style=color)
                self.axfatigue[i][2].set_xlim(self.axfatigue[i][0].get_xlim())
                self.axfatigue[i][2].set_title(f'MNF',fontweight="bold")
                self.axfatigue[i][2].set_xlabel("hh:mm:ss", fontsize=12)
                self.axfatigue[i][2].tick_params(labelsize=10)

                plt.suptitle(f"{self.title_emg}\n{self.array_nome_muscoli[i]}", fontsize = "15",fontweight="bold")
                plt.subplots_adjust(left  = 0.07, bottom = 0.08, top=0.84, right = 0.95,hspace = 0.9)
                
            #chiudo la barra di progresso
            self.start_stop_event.clear()
            self.progressbar_process=None

            #seleziono la tab appena creata
            self.tab_fatigue.update()
            self.tabControl.select(self.tab_fatigue)

            self.id_fatigue=0 #id della figura da plottare
            self.canvas_fatigue = FigureCanvasTkAgg(self.ar_fig_fatigue[self.id_fatigue], master=self.tab_fatigue)  # A tk.DrawingArea.
            self.canvas_fatigue.draw()

            def change_plot_fatigue(id):
                """
                change muscle fatigue plot
                """
                self.toolbar_fatigue.children['!button'].invoke()
                self.canvas_fatigue.get_tk_widget().pack_forget()
                self.canvas_fatigue=None
                self.canvas_fatigue = FigureCanvasTkAgg(self.ar_fig_fatigue[id], master=self.tab_fatigue)  # A tk.DrawingArea.
                self.canvas_fatigue.draw()
                
                self.toolbar_fatigue.pack_forget()
                self.toolbar_fatigue=None
                self.toolbar_fatigue = NavigationToolbar2Tk(self.canvas_fatigue, self.tab_fatigue)

                self.muscle_selection.destroy()
                self.muscle_selection=None
                self.muscle_selection= ttk.Combobox(master=self.toolbar_fatigue,values=self.array_nome_muscoli,state='readonly',width=40)
                self.muscle_selection.place(relx=0.40,rely=0.2)
                self.muscle_selection.current(id)
                self.muscle_selection.bind("<<ComboboxSelected>>",lambda e: change_plot_fatigue(self.muscle_selection.current()))

                #self.toolbar_fatigue.update()
                self.canvas_fatigue.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            
            self.toolbar_fatigue = NavigationToolbar2Tk(self.canvas_fatigue, self.tab_fatigue)
            
            #combobox per la selezione del muscolo
            self.muscle_selection= ttk.Combobox(master=self.toolbar_fatigue,values=self.array_nome_muscoli,state='readonly',width=40)
            self.muscle_selection.place(relx=0.40,rely=0.2)
            self.muscle_selection.current(0)
            self.muscle_selection.bind("<<ComboboxSelected>>",lambda e: change_plot_fatigue(self.muscle_selection.current()))
            
            self.toolbar_fatigue.update()
            self.canvas_fatigue.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        else: #se non è None significa che era stata creata la tab
            self.tab_fatigue.update() #update delle tab
            self.tabControl.select(self.tab_fatigue) #la seleziono
    
    def export(self):
        """
        Export .csv file containing MNF values, and .fit values if any
        """
        if type(self.Df_export) == type(None): #se il dataframe per l'export non è già stato calcolato
            if self.check_fit:
                #se è presente un file .fit concateno i dataframe conteneti le MNF e i dati del file .fit 
                arr = np.arange(len(self.Df_RMS)) // int(self.fs_emg)
                df = self.Df_RMS.groupby(arr).mean()
                try:
                    df.index = self.Df_fit.index[:len(df)]
                except:
                    df = df.iloc[:len(self.Df_fit),:]
                    df.index = self.Df_fit.index

                self.Df_export = pd.concat([self.Df_MNF, df, self.Df_fit], axis=1, sort=True)
            else:
                #se non è presente un file .fit modifico il dataframe delle MNF per avere un dataframe campionato a 1s e non self.TMNF 
                #tempo_MNF=[]
                #for seconds in np.arange((len(self.Df_MNF) * self.TMNF)):
                    #microseconds=(seconds*1000000) % 1000000
                    #hours = seconds // 3600
                    #minutes = (seconds % 3600) // 60
                    #seconds = seconds % 60 // 1
                    #tempo_MNF.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))
                #self.Df_export = pd.DataFrame(index=tempo_MNF) #tempo campionato a 1s

                ## ROBERTO ##
                # Dalla riga 3134 alla riga 3157 ho sostituito DF_export con Df_Emg_Filtered

                arr = np.arange(len(self.Df_RMS)) // int(self.fs_emg)
                df = self.Df_RMS.groupby(arr).mean()
                try:
                    df.index = self.Df_Emg_Filtered.index[:len(df)]
                except:
                    df = df.iloc[:len(self.Df_Emg_Filtered),:]
                    df.index = self.Df_Emg_Filtered.index

                #self.Df_Emg_Filtered = pd.concat([self.Df_Emg_Filtered, self.Df_MNF, df], axis=1, sort=True)  # Roberto
                # Non c'è bisogno di questo numero extra di canali se si guarda solo l'EMG
                #self.Df_Emg_Filtered = pd.concat([self.Df_Emg_Filtered, df], axis=1, sort=True)

                
             
                #ora il dataframe è campionato a 1 secondo e non più a self.TMNF secondi
                #i nuovi valori conterranno dei nan che verranno poi interpolati

            #interpolazione, aggiunta del nome timestamp all'indice e arrotondamento a numeri interi
            self.Df_Emg_Filtered=self.Df_Emg_Filtered.interpolate(limit_direction='both')
            self.Df_Emg_Filtered.index.name='TIME'
            self.Df_Emg_Filtered=self.Df_Emg_Filtered.round(0)
        
        #scrittura del file .xlsx
        _=export_excel(self.Df_Emg_Filtered,self.check_fit)

    def export_all_rms (self) :
        """
        Export .csv file containing the entire registration of rms signals
        """
        _=export_all_rms_excel(self.Df_RMS)

    def documentation(self):
        """
        opens documentation link
        """
        import webbrowser
        new=2 #open in a new tab if possible
        index_path=os.path.abspath(os.path.join(os.getcwd(),'_build','html','index.html'))
        url = f"file://{index_path}"
        webbrowser.open(url,new=new)
        
    def quick_start(self):
        """
        opens quick start link
        """
        import subprocess
        filename=os.path.abspath(os.path.join(os.getcwd(),'Documentation','Quick_Start_App_LWT3.pdf'))
        subprocess.Popen(filename,shell=True)

    def about(self):
        """
        shows application information
        """
        def close():
            self.help_window.destroy()
            self.help_window=None

        if not self.help_window:
            #mostro una window centrata help
            self.help_window=tk.Toplevel(master=self.master)
            self.help_window.title("Raw Power")
            self.help_window.geometry("250x150")
            self.help_window.protocol("WM_DELETE_WINDOW", close)
            #geometria della finestra centrata
            x = (self.help_window.winfo_screenwidth() - self.help_window.winfo_reqwidth()) / 2
            y = (self.help_window.winfo_screenheight() - self.help_window.winfo_reqheight()) / 2
            self.help_window.geometry("+%d+%d" % (x, y))
            self.help_window.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')
            self.help_window.configure(background='black')
            self.help_window.resizable(False,False)
            help_label=tk.Label(self.help_window, text="Raw Power",font=('Ubuntu','12'),fg='red',bg='Black')
            help_label.place(x=70,y=10)
            version_label=tk.Label(self.help_window, text="Version: 1.0",font=('Ubuntu','8'),fg='white',bg='black')
            version_label.place(x=10,y=50)
            date_label=tk.Label(self.help_window, text="Date: 5/8/2020",font=('Ubuntu','8'),fg='white',bg='black')
            date_label.place(x=10,y=80)
            copyright_label=tk.Label(self.help_window, text="Author: ©LWT3",font=('Ubuntu','8'),fg='white',bg='black')
            copyright_label.place(x=10,y=110)
        else: #se la window è già presente
            self.help_window.lift() #la porta in primo piano 

    def close(self):
        """
        shows message box and eventually close the window
        """
        response=tk.messagebox.askyesnocancel(title='exit window',message='Are you sure to close the program?')
        if response: #se la risposta è affermativa
            self.master.destroy()
            sys.exit(0) 

if __name__ == "__main__":
    multiprocessing.freeze_support() #necessario per generare file .exe
    main_window=tk.Tk()
    app=Application(main_window)
    main_window.mainloop()