#APPLICAZIONE PER LA REGISTRAZIONE REAL TIME DEI SEGNALI EMG E OPTITRACK

#import delle librerie
from ast import Assign
from operator import index
from tkinter import messagebox
from tkinter.font import BOLD
from turtle import right
from typing_extensions import Self
from matplotlib import markers
import serial 
import serial.tools.list_ports #utilizzata per elencare le porte COM disponibili

import pandas as pd
import PySimpleGUI as sg

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *

import csv

import time
import datetime 

import os
import inspect
import threading
from threading import Thread,Event
import multiprocessing #libreria per operare su diversi processori in parallelo
import psutil #libreria utile per alzare la priorità dei processi d'interesse

import numpy as np
import math
from tkcalendar import DateEntry

#import funzioni per l'acquisizione
from Acquisition.Acquisition import continuos_acquiring, continuos_optitrack
from BLE.ble import scan_BLE, BLE_acquiring, service_explorer
from CustomTree.customtree import customtree

class Acquisition_app():

    additional_data_form=''
    """
    control registration operations
    """
    def __init__(self,master):
    #inizializzazione
        self.master=master
        self.master.title("REAL TIME ACQUSISTION") #titolo master
        self.master.configure(background='black') #background master
        self.master.resizable(0,0) #dimensioni fisse

        #geometria master centrata
        w = 900 # width for the Tk self
        h = 500 # height for the Tk self

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

        #BUTTON
        self.start_button= tk.Button(self.master, text="START",background='red',foreground='white',font=('Helvetica','12'),padx=5,pady=5,command=self.start) #bottone start per far partire l'acquisizione
        self.start_button.place(x=800,y=430) #posizionamento bottone start

        file_path=os.path.abspath(os.path.join(__file__, '..','BLE.png'))
        photo = tk.PhotoImage(file = rf"{file_path}") 
        # Resizing image to fit on button 
        self.icon_BLE = photo.subsample(7, 7) 
        self.find_BLE_button= tk.Button(self.master,text="SCAN BLE", image=self.icon_BLE,background='red',foreground='white',padx=5,pady=5,compound=tk.LEFT,command=self.scan_BLE) #bottone start per far partire l'acquisizione
        self.find_BLE_button.place(x=20,y=330) #posizionamento bottone start
        self.athlete_import_button=tk.Button(self.master,text="LOAD ATHLETE",bg='red',fg='white',font=('Helvetica','8'),padx=5,pady=5,command=self.import_athlete)
        self.athlete_import_button.place(x=20,y=20)
        self.template_import_button=tk.Button(self.master,text="LOAD TEMPLATE",bg='red',fg='white',font=('Helvetica','8'),padx=5,pady=5,command=self.import_template)
        self.template_import_button.place(x=750,y=300)
        self.cashier_template_button=tk.Button(self.master, text='ADDITIONAL DATA',bg='red',fg='white',font=('Helvetica','8'),padx=5,pady=5,command=self.additional_data)
        self.cashier_template_button.place(x=750,y=400)
        self.insert_data_button= tk.Button(self.master, text="SET VARIABLES DATA",background='red',foreground='white',font=('Helvetica','12'),padx=5,pady=5,command=self.set_variables_data) #bottone start per far partire l'acquisizione
        self.insert_data_button.place(x=350,y=330) #posizionamento bottone
        
        #CLOSE PROCEDURE
        self.master.protocol("WM_DELETE_WINDOW", self.close) #quando si chiude la master viene eseguita la funzione close
        
        self.check_first_entry=False #variable to check for first value manually added throug "INSERT DATA" 

        #DRAW CIRCLE
        self.canvas = tk.Canvas(self.master,width=40,height=40,bg='black',highlightbackground='black')
        self.circle=self.canvas.create_oval(5, 5, 35, 35, outline="#000000",fill="#000000", width=2)
        self.canvas.place(x=650,y=430)

        #MODE SELECTION
        self.MODES=[ #variabile per creare i Radiobutton per la scelta della modalità
            "MODE 0 - fsampling 2700 Hz",
            "MODE 1 - fsampling 2700 Hz",
            "MODE 2 - fsampling 2000 Hz",
            "MODE 3 - fsampling 2000 Hz",
            "MODE 4 - fsampling 1000 Hz",
            "MODE 5 - fsampling 1000 Hz",
            "MODE 6 - fsampling 500 Hz",
            "MODE 7 - fsampling 500 Hz"]

        self.mode_selection= ttk.Combobox(self.master,values=self.MODES,state='readonly',width=30)
        self.mode_selection.place(x=360,y=90)
        self.mode_selection.current(5)

        self.mode_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        tk.Label(self.master,text="SAMPLING FREQUENCY",justify=tk.LEFT,bg='black',fg='white').place(x=360,y=70) #posizionamento label setting

        #TYPE SELECTION (single/double)
        self.TYPES=[
            "1",
            "2"
        ]
        self.type_selection= ttk.Combobox(self.master,values=self.TYPES,state='readonly',width=30)
        self.type_selection.place(x=360,y=30)
        self.type_selection.current(0)
        self.type_selection.bind("<<ComboboxSelected>>",lambda e:self.TYPE_settings(self.type_selection.current()))
        tk.Label(self.master,text="N° DEVICES",bg='black',fg='white').place(x=360,y=10) #posizionamento label per la selezione del tipo di acquisizione

        #TEMPLATE SELECTION
        self.TEMPLATES=[ #variabile per creare i Radiobutton per la scelta del template
            "SHIRT",
            "MOTORBIKE",
            "BIKE",
            "RUN",
            "POSTURAL EFFICIENCY 1",
            "POSTURAL EFFICIENCY 2",
            "POSTURAL EFFICIENCY 3",
            "POSTURAL EFFICIENCY 4",
            "BIKE METABOLIMETER",
            "BIKE BIOMECHANICS",
            "RUN BIOMECHANICS 1",
            "RUN BIOMECHANICS 2",
            "LEFT ARCHER",
            "RIGHT ARCHER",
            "HANDBIKE",
            "CASHIER",
            "OTHER"
        ]

        self.template_selection= ttk.Combobox(self.master,values=self.TEMPLATES,state='readonly',width=30)
        self.template_selection.place(x=360,y=150)
        self.template_selection.current(16)
        self.template_selection.bind("<<ComboboxSelected>>",lambda e:self.TEMPLATE_settings(self.template_selection.current()))
        #indici dei muscoli corrispondenti al template specifico
        self.template_muscles=[[42,48,44,46,0,6,1,4], #maglia
                                [51,48,44,55,9,6,2,13], #moto
                                [46,48,52,55,4,10,12,13], #bici
                                [53,54,52,55,11,12,10,13], #corsa
                                [56,53,14,11,84,84,84,84], #postural efficiency 1
                                [56,53,82,84,14,11,40,84], #postural efficiency 2
                                [56,53,46,84,14,11,4,84], #postural efficiency 3
                                [56,53,82,46,14,11,40,4], #postural efficiency 4
                                [56,53,14,11,84,84,84,84], #bike metabolimeter
                                [56,53,14,11,84,84,84,84], #bike biomechanics
                                [56,53,14,11,84,84,84,84], #run biomechanics
                                [56,53,82,84,14,11,40,84], #run biomedics
                                [0,7,5,47,44,45,49,50], #arciere mancino
                                [42,49,47,5,2,3,7,8], #arciere destro
                                [8,7,6,5,50,49,48,47], #handbike
                                [60,45,47,46,18,3,5,4], #cashier
                                [84,84,84,84,84,84,84,84]] #other

        tk.Label(self.master,text="TEMPLATE",justify=tk.LEFT,bg='black',fg='white').place(x=360,y=130) #posizionamento label setting

        self.set_muscoli={
            0 : "PECTORALIS MAJOR DDX",
            1 : 'LOWER TRAPEZIUS DX',
            2 : 'RHOMBOID MAJOR DX',
            3 : 'INFRASPINATUS DX',
            4 : 'ERECTOR SPINAE DX',
            5 : 'LATISSIMUS DORSI DX',
            6 : 'DELTOID LATERAL DX',
            7 : 'TRICEPS BRACHII LONG HEAD DX',
            8 : 'BICEPS BRACHII DX',
            9 : 'BRACHIORADIALIS DX',
            10 : 'GLUTEUS MAXIMUS DX',
            11 : 'BICEPS FEMORIS DX',
            12 : 'GASTROCNEMIUS LATERALIS DX',
            13 : 'RECTUS FEMORIS DX',
            14 : 'VASTUS LATERALIS DX',
            15 : 'STERNOCLEIDOMASTOID DX',
            16 : 'SERRATUS ANTERIOR DX',
            17 : 'RECTUS ABDOMINIS DX',
            18 : 'UPPER TRAPEZIUS DX',
            19 : 'MIDDLE TRAPEZIUS DX',
            20 : 'RHOMBOID MINOR DX',
            21 : 'POSTERIOR DELTOID DX',
            22 : 'ANTERIOR DELTOID DX',
            23 : 'TRICEPS LONG HEAD DX',
            24 : 'TRICEPS LATERAL HEAD DX',
            25 : 'BICEPS BRACHII SHORT HEAD DX',
            26 : 'BICEPS BRACHII LONG HEAD DX',
            27 : 'PALMARIS LONGUS DX',
            28 : 'FLEXOR CARPI RADIALIS DX',
            29 : 'PRONATOR TERES DX',
            30 : 'EXTENSOR CARPI ULNARIS DX',
            31 : 'EXTENSOR CARPI RADIALIS DX',
            32 : 'ABDUCTOR DIGITI MINIMI DX',
            33 : 'FLEXOR POLLICIS BREVIS DX',
            34 : 'GLUTEUS MEDIUS DX',
            35 : 'SEMITENDINOSUS DX',
            36 : 'GASTROCNEMIUS MEDIALIS DX',
            37 : 'SOLEUS DX',
            38 : 'TENSOR FASCIAE LATAE DX',
            39 : 'VASTUS MEDIALIS DX',
            40 : 'TIBIALIS ANTERIOR DX',
            41 : 'PERONEUS LONGUS DX',


            42 : 'PECTORALIS MAJOR SX',
            43 : 'LOWER TRAPEZIUS SX',
            44 : 'RHOMBOID MAJOR SX',
            45 : 'INFRASPINATUS SX',
            46 : 'ERECTOR SPINAE SX',
            47 : 'LATISSIMUS DORSI SX',
            48 : 'DELTOID LATERAL SX',
            49 : 'TRICEPS BRACHII LONG HEAD SX',
            50 : 'BICEPS BRACHII SX',
            51 : 'BRACHIORADIALIS SX',
            52 : 'GLUTEUS MAXIMUS SX',
            53 : 'BICEPS FEMORIS SX',
            54 : 'GASTROCNEMIUS LATERALIS SX',
            55 : 'RECTUS FEMORIS SX',
            56 : 'VASTUS LATERALIS SX',
            57 : 'STERNOCLEIDOMASTOID SX',
            58 : 'SERRATUS ANTERIOR SX',
            59 : 'RECTUS ABDOMINIS SX',
            60 : 'UPPER TRAPEZIUS SX',
            61 : 'MIDDLE TRAPEZIUS SX',
            62 : 'RHOMBOID MINOR SX',
            63 : 'POSTERIOR DELTOID SX',
            64 : 'ANTERIOR DELTOID SX',
            65 : 'TRICEPS LONG HEAD SX',
            66 : 'TRICEPS LATERAL HEAD SX',
            67 : 'BICEPS BRACHII SHORT HEAD SX',
            68 : 'BICEPS BRACHII LONG HEAD SX',
            69 : 'PALMARIS LONGUS SX',
            70 : 'FLEXOR CARPI RADIALIS SX',
            71 : 'PRONATOR TERES SX',
            72 : 'EXTENSOR CARPI ULNARIS SX',
            73 : 'EXTENSOR CARPI RADIALIS SX',
            74 : 'ABDUCTOR DIGITI MINIMI SX',
            75 : 'FLEXOR POLLICIS BREVIS SX',
            76 : 'GLUTEUS MEDIUS SX',
            77 : 'SEMITENDINOSUS SX',
            78 : 'GASTROCNEMIUS MEDIALIS SX',
            79 : 'SOLEUS SX',
            80 : 'TENSOR FASCIAE LATAE SX',
            81 : 'VASTUS MEDIALIS SX',
            82 : 'TIBIALIS ANTERIOR SX',
            83 : 'PERONEUS LONGUS SX',

            84: 'NOT CONNECTED'
        }

        #funzione per velocizzare la ricerca dei muscoli dal menu di ogni combobox
        #FIXME: Funzione da generalizzare -> come passare il combobox muscleN_selection alla funzione?
        def check_input_m1(event):
            value = event.widget.get()
            if value == '':
                self.muscle1_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle1_selection['values'] = data  

        def check_input_m2(event):
            value = event.widget.get()
            if value == '':
                self.muscle2_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle2_selection['values'] = data        

        def check_input_m3(event):
            value = event.widget.get()
            if value == '':
                self.muscle3_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle3_selection['values'] = data 

        def check_input_m4(event):
            value = event.widget.get()
            if value == '':
                self.muscle4_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle4_selection['values'] = data        

        def check_input_m5(event):
            value = event.widget.get()
            if value == '':
                self.muscle5_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle5_selection['values'] = data        

        def check_input_m6(event):
            value = event.widget.get()
            if value == '':
                self.muscle6_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle6_selection['values'] = data        

        def check_input_m7(event):
            value = event.widget.get()
            if value == '':
                self.muscle7_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle7_selection['values'] = data        

        def check_input_m8(event):
            value = event.widget.get()
            if value == '':
                self.muscle8_selection['values'] = list(self.set_muscoli.values())
            else:
                data = []
                for item in list(self.set_muscoli.values()):
                    if value.upper() in item.upper():
                        data.append(item)
                self.muscle8_selection['values'] = data


        #muscle selections, creazione label e liste dei muscoli tra cui è possibile scegliere
        tk.Label(self.master,text="Muscle 1",bg='blue',fg='white').place(x=595,y=10) #creazione label primo muscolo
        self.muscle1_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle1_selection.place(x=670,y=10)
        tk.Label(self.master,text="Muscle 2",bg='red',fg='white').place(x=595,y=40)
        self.muscle2_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle2_selection.place(x=670,y=40)
        tk.Label(self.master,text="Muscle 3",bg='saddle brown',fg='white').place(x=595,y=70)
        self.muscle3_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle3_selection.place(x=670,y=70)
        tk.Label(self.master,text="Muscle 4",bg='black',fg='white').place(x=595,y=100)
        self.muscle4_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle4_selection.place(x=670,y=100)
        tk.Label(self.master,text="Muscle 5",bg='blue',fg='white').place(x=595,y=130)
        self.muscle5_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle5_selection.place(x=670,y=130)
        tk.Label(self.master,text="Muscle 6",bg='red',fg='white').place(x=595,y=160)
        self.muscle6_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle6_selection.place(x=670,y=160)
        tk.Label(self.master,text="Muscle 7",bg='saddle brown',fg='white').place(x=595,y=190)
        self.muscle7_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle7_selection.place(x=670,y=190)
        tk.Label(self.master,text="Muscle 8",bg='black',fg='white').place(x=595,y=220)
        self.muscle8_selection= ttk.Combobox(self.master,values=list(self.set_muscoli.values()),state='normal',width=30)
        self.muscle8_selection.place(x=670,y=220)

        #to speed up the search engine, possibility to search a muscle
        self.muscle1_selection.bind("<KeyRelease>", check_input_m1)
        self.muscle2_selection.bind("<KeyRelease>", check_input_m2)
        self.muscle3_selection.bind("<KeyRelease>", check_input_m3)
        self.muscle4_selection.bind("<KeyRelease>", check_input_m4)
        self.muscle5_selection.bind("<KeyRelease>", check_input_m5)
        self.muscle6_selection.bind("<KeyRelease>", check_input_m6)
        self.muscle7_selection.bind("<KeyRelease>", check_input_m7)
        self.muscle8_selection.bind("<KeyRelease>", check_input_m8)

        #muscle selction default values, relative to the default template ('OTHER')
        self.muscle1_selection.current(self.template_muscles[self.template_selection.current()][0])
        self.muscle2_selection.current(self.template_muscles[self.template_selection.current()][1])
        self.muscle3_selection.current(self.template_muscles[self.template_selection.current()][2])
        self.muscle4_selection.current(self.template_muscles[self.template_selection.current()][3])
        self.muscle5_selection.current(self.template_muscles[self.template_selection.current()][4])
        self.muscle6_selection.current(self.template_muscles[self.template_selection.current()][5])
        self.muscle7_selection.current(self.template_muscles[self.template_selection.current()][6])
        self.muscle8_selection.current(self.template_muscles[self.template_selection.current()][7])
        
        #avoid blue higlight
        self.muscle1_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle2_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle3_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle4_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle5_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle6_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle7_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())
        self.muscle8_selection.bind("<<ComboboxSelected>>",lambda e: self.master.focus())

        #MANDATORY FIELD LABEL
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=10,y=475)
        tk.Label(self.master,text="mandatory fields",bg='black',fg='white').place(x=20,y=475)

        #ATHLETE'S NAME
        tk.Label(self.master,text="Name",bg='black',fg='white').place(x=20,y=70)
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=55,y=70)
        self.name_input=tk.Entry(self.master,width=20,justify='left')
        self.name_input.insert(0,'')
        self.name_input.place(x=20,y=90)

        #ATHLETE'S DATE OF BIRTH
        tk.Label(self.master,text="Date of birth",bg='black',fg='white').place(x=20,y=120)
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=90,y=120)
        self.date_input = DateEntry(self.master, width=17, background='darkred',foreground='white', borderwidth=2)
        self.date_input.delete(0, 'end')
        self.date_input.place(x=20,y=140)

        #WEIGHT'S NAME
        tk.Label(self.master,text="Weight (Kg)",bg='black',fg='white').place(x=180,y=70)
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=245,y=70)
        self.weight_input=tk.Entry(self.master,width=20,justify='left')
        self.weight_input.insert(0,'')
        self.weight_input.place(x=180,y=90)

        #HEIGHT'S NAME
        tk.Label(self.master,text="Height (cm)",bg='black',fg='white').place(x=180,y=120)
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=247,y=120)
        self.height_input=tk.Entry(self.master,width=20,justify='left')
        self.height_input.insert(0,'')
        self.height_input.place(x=180,y=140)

        #REFERENCE POSITION
        tk.Label(self.master,text="Reference",bg='black',fg='white').place(x=595,y=250)
        tk.Label(self.master,text="*",bg='black',fg='red',font=('Helvetica','15')).place(x=650,y=250)
        self.reference_input=tk.Entry(self.master,width=33,justify='left')
        self.reference_input.insert(0,'')
        self.reference_input.place(x=670,y=250)

        #TASK'S DESCRIPTION
        tk.Label(self.master,text="Description",bg='black',fg='white').place(x=20,y=180)
        self.description_input=tk.Text(self.master,height=4,width=76)
        self.description_input.configure(font=("Helvetica",10))
        self.description_input.insert('0.0','Task description')
        self.description_input.place(x=20,y=200)
        self.scroll = tk.Scrollbar(self.master,command=self.description_input.yview)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.description_input.config(yscrollcommand=self.scroll.set)

        #OPTITRACK SELECTION
        def optitrack_available():
            if self.optitrack_selected.get():
                self.optitrack_server.config(state='normal')
            else:
                self.optitrack_server.config(state='disabled')

        tk.Label(self.master,text="Optitrack",bg='black',fg='white').place(x=20,y=290)
        self.optitrack_selected=tk.IntVar(value=1) #variabile per gestire la scelta
        self.optitrack_checkbutton=tk.Checkbutton(self.master,text='',variable=self.optitrack_selected,bg='black',fg='white',selectcolor='black',command=optitrack_available)
        self.optitrack_checkbutton.place(x=75,y=290)
        self.optitrack_server=tk.Entry(self.master,width=15,justify='right')
        self.optitrack_IP='127.0.0.1'
        self.optitrack_server.insert(0,self.optitrack_IP)
        self.optitrack_server.place(x=100,y=290)
        
        #variable initialization
        self.thread1 = None #thread prima scheda
        self.thread2 = None #thread seconda scheda
        self.thread_optitrack= None #thread optitrack
        self.thread_blink= None  #thread blink led
        self.thread_button= None #thread per controllare la chiusura del plot real time tramite tasto X
        self.stop_blink=False #varibile controllo all'interno di thread blink
        self.stop_threads = multiprocessing.Event() #variabile per gestire la chiusura sincrona dei processi
        self.start_event=multiprocessing.Event() #variabile per gestie l'avvio sincrono delle registrazioni
        self.hide_event=multiprocessing.Event()
        self.hide_event.clear()
        self.delete_button_event=multiprocessing.Event()
        self.delete_button_event.clear()

        self.TYPE=True #variabile per controllare se si vuole acquisire una o due schede (default TRUE= singola scheda)
        self.STOP=False #variabile per controllare se è stato premuto il tasto STOP
        self.START=True #variabile per controllare la possibilità di far partire la registrazione (all' inizio è possibile far partire la registrazione)

        #available com ports
        ports = list(serial.tools.list_ports.comports())
        self.porte_com=[]
        for p in ports:
            print(p) #all available com
            if(str(p).split('-')[-1].split('(')[0] in [' USB Serial Device ',' Dispositivo seriale USB ']): #se le com sono collegate ad un dispositivo seriale
                self.porte_com.append(str(p).split(' ')[0])
        print(f'Available serial device {self.porte_com}') #stampa le com seriali
    #fine inizializzaizone
    
    def import_athlete(self):
        """
        read description file and fill athlet's name, date of birth, height and weight
        """
        in_dir=os.path.expanduser('~\Documents\Recordings')
        if not (os.path.isdir(in_dir)):
            os.mkdir(in_dir)
        description_file=filedialog.askopenfilename(title='select a decription file',initialdir=f'{in_dir}',filetypes = (("text files","description.txt"),("all files","*.*")))
        if not description_file=='':
            with open(f'{description_file}', 'r') as f:
                try: #parse del file description
                    data = f.read().replace('\n','').replace(' ','')
                    name=data.split('NAME')[-1].split('DATEOFBIRTH')[0]
                    name=name.replace('_', ' ')
                    self.name_input.delete(0, 'end')
                    self.name_input.insert(0,f'{name}')
                    date_of_birth=data.split('DATEOFBIRTH')[-1].split('HEIGHT')[0]
                    self.date_input.delete(0, 'end')
                    self.date_input.insert(0,f'{date_of_birth}')
                    height=data.split('HEIGHT')[-1].split('cmWEIGHT')[0]
                    self.height_input.delete(0, 'end')
                    self.height_input.insert(0,f'{height}')
                    weight=data.split('cmWEIGHT')[-1].split('KgDESCRIPTION')[0]
                    self.weight_input.delete(0, 'end')
                    self.weight_input.insert(0,f'{weight}')
                except:
                    tk.messagebox.showerror(title='ERROR',message='file not correct')

    def import_template(self):
        """
        read template file and fill the 8 muscles
        """
        in_dir=os.path.expanduser('~\Documents\Recordings')
        if not (os.path.isdir(in_dir)):
            os.mkdir(in_dir)
        description_file=filedialog.askopenfilename(title='select a decription file',initialdir=f'{in_dir}',filetypes = (("text files","template.txt"),("all files","*.*")))
        if not description_file=='':
            with open(f'{description_file}', 'r') as f:
                try: #parse del file description
                    data = f.read().split('\n')
                    data.remove('')
                    muscles=[]
                    for item in data:
                        muscles.append(item.upper())

                    reset_muscle_values(self)   #prima resetto i valori delle combobox a set_muscoli, perchè potrebbero essere stati cambiati utilizzando la ricerca

                    self.muscle1_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[0])])    #dalla stringa della lista muscles[] calcolo la keys corrispondente al muscolo nel dictionary e posso poi settare muscle1_seletion
                    self.muscle2_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[1])])
                    self.muscle3_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[2])])
                    self.muscle4_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[3])])
                    self.muscle5_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[4])])
                    self.muscle6_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[5])])
                    self.muscle7_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[6])])
                    self.muscle8_selection.current(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(muscles[7])])

                except:
                    tk.messagebox.showerror(title='ERROR',message='file not correct or maybe one of the muscles in the file does not exist.')

    def additional_data(self):
    #     self.additional_data_window = tk.Toplevel(self.master)
    #     self.additional_data_window.title("New Window")
    #     # sets the geometry of toplevel
    #     self.additional_data_window.geometry("800x800")
        # A Label widget to show in toplevel

        self.ws = tk.Toplevel(master=self.master)
        self.ws.title('CASHIER TEST - low loads high frequency')
        self.ws.config(bg='black')
        self.ws.grab_set()

        f = ('Helvetiga', 11)

        variable= StringVar()
        temp_for_gender = StringVar()
        temp_for_hand= StringVar()
        temp_for_injury= StringVar()
        temp_for_pathologies=StringVar()
        temp_for_physical_activity=StringVar()
        temp_for_testisperformed = StringVar()
        temp_for_temperature = StringVar()
        temp_for_electrodes_type = StringVar()
        temp_for_electrodes_geometry = StringVar()
        temp_for_markers = StringVar()
        # world = open('countries.txt', 'r')
        # for country in world:
        #     country = country.rstrip('\n')
        #     countries.append(country)
        # variable.set(countries[1])

        gender_choices = ['male', 'female']
        variable.set(gender_choices[0])

        hand_choices = ['right', 'left']
        temp_for_hand.set(hand_choices[0])

        injury_choices = ['none', 'back', 'shoulder', 'arm', 'hip', 'knee','ankle', 'foot']
        temp_for_injury.set(injury_choices[0])

        pathologies_choices = ['none', 'back', 'shoulder', 'arm', 'hip', 'knee','ankle', 'foot']
        temp_for_pathologies.set(pathologies_choices[0])

        physical_activity_choices = ['I rarely or never do physical activities', 'I do some light or moderate physical activities, but not every week', 'I do some light physicala ctivity every week', 'I do moderate physical activities every week, but less than 30 min a day or 5 days a week', 'I do vigorous physical activities every week, but less than 20 min a day or 3 days a week', 'I do 30 min or more a day of moderate physical activities, 3 or more days a week','I do 20 min or more a day of vigorous physical activities, 3 or more days a week']
        variable.set(pathologies_choices[0])

        testisperformed = ['indoor', 'outdoor']
        temp_for_testisperformed.set(testisperformed[0])

        electrodes_type = ['Single Differential', 'Double Differential']
        temp_for_electrodes_type.set(electrodes_type[1])

        electrodes_geometry = ['square', 'rectangular', 'cylindrical', 'circular']
        temp_for_electrodes_geometry.set(electrodes_geometry[3])

        temperaturevariable = ['less than 18°C', '18°C - 25°C','25°C - 34°C', 'more than 34°C']
        temp_for_temperature.set(temperaturevariable[1])

        markers_choice = ['marker based', 'marker less']
        temp_for_markers.set(markers_choice[0])

        def testVal(inStr,acttyp):
            if acttyp=='1': #insert
                if not inStr.isdigit():
                    return False
            return True


        #EXCEL_FILE = r'C:\Users\Davide Zamagna\Desktop\CASHIER TEST tables\test_data.xlsx'
        #df = pd.read_excel(EXCEL_FILE)

        def get_value():

            e_name=name_surname.get()
            e_gender=temp_for_gender.get()
            e_age=age.get()
            e_hand=temp_for_hand.get()
            e_pathologies=temp_for_pathologies.get()
            e_injury=temp_for_injury.get()

            e_height=height.get()
            e_weight=weight.get()
            e_height_to_right_trochanter= height_to_right_trochanter.get()
            e_shoulder_width=shoulder_width.get()
            e_arm_length=arm_lenght.get()
            e_inseam_height=inseam_height.get()
            e_fibula_length=fibula_length.get()
            e_lower_limb_length=lower_limb_length.get()
            e_ASIS_distance=ASIS_distance.get()
            e_knee_width=knee_width.get()
            e_ankle_width=ankle_width.get()
            e_foot_length=foot_length.get()

            e_testisperformed=temp_for_testisperformed.get()
            e_temperature=temp_for_temperature.get()

            e_workstation=workstation_height.get()
            e_load=load_weight.get()
            e_duration=test_duration.get()
            e_techactions=technical_actions.get()

            e_emgsystem=emg_system.get()
            e_emgsampling=emg_sampling_rate.get()
            e_channels=no_channels.get()
            e_electrodessize=electrodes_size.get()
            e_electrodesgeometry=temp_for_electrodes_geometry.get()
            e_electrodestype=temp_for_electrodes_type.get()

            e_mocapsystem=mocap_system.get()
            e_mocaptsampling=mocap_sampling_rate.get()
            e_cameras=no_cameras.get()
            e_markers=temp_for_markers.get()
        
            self.additional_data_form=f'ANAMNESTIC INFORMATION\n\nNAME AND SURNAME: {e_name}\nGENDER: {e_gender}\nAGE: {e_age}\nHANDEDNESS: {e_hand}\nINJURY HISTORY: {e_injury}\nPATHOLOGIES: {e_pathologies}\n\nANTHROPOMETRIC MEASUREEMNTS\n\nHEIGHT: {e_height}\nWEIGHT: {e_weight}\nHEIGHT TO RIGHT TROCHANTER: {e_height_to_right_trochanter}\nSHOULDER WIDTH: {e_shoulder_width}\nARM LENGTH: {e_arm_length}\nINSEAM HEIGHT: {e_inseam_height}\nFIBULA LENGTH: {e_fibula_length}\nLOWER LIMB LENGTH: {e_lower_limb_length}\nASIS-TROCHANTER DISTANCE: {e_ASIS_distance}\nKNEE WIDTH: {e_knee_width}\nANKLE WIDTH: {e_ankle_width}\nFOOT LENGTH: {e_foot_length}\n\nENVIRONMENT CONDITIONS\n\nWORKING ENVIRONMENT: {e_testisperformed}\nWORKING TEMPERATURE: {e_temperature}\n\nWORKING TASK\n\nWORKSTATION HEIGH: {e_workstation}\nLOAD WEIGHT: {e_load}\nTEST DURATION: {e_duration}\nNO TECHNICAL ACTIONS PER MINUTE {e_techactions}\n\nsEMG\n\nsMG SYSTEM NAME: {e_emgsystem}\SAMPLING RATE: {e_emgsampling}\nNO. CHANNELS: {e_channels}\nELECTRODES SIZE: {e_electrodessize}\nELECTRODES GEOMETRY: {e_electrodesgeometry}\nELECTRODES TYPE: {e_electrodestype}\n\nMOTION CAPTURE\n\nMOCAP SYSTEM NAME: {e_mocapsystem}\nSAMPLING RATE: {e_mocaptsampling}\nNO. CAMERAS: {e_cameras}\nMARKERS: {e_markers}\n'
            
       
        # ANAMNESTIC INFORMATION FRAME

        anamnestic_frame = Frame(
            self.ws, 
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
            )
        anamnestic_frame= LabelFrame(self.ws, text='  ANAMNESTIC INFORMATION', fg='white', bg='black',font= ('Helvetica 13'))

        Label(
            anamnestic_frame, 
            text="  Name and Surname", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)  

        Label(
            anamnestic_frame, 
            text="  Gender", 
            bg='black', fg='white',
            font=f
            ).grid(row=3, column=0, sticky=W, pady=10)  
        
        Label(
            anamnestic_frame, 
            text="  Age", 
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)  

        Label(
            anamnestic_frame, 
            text="  Handedness", 
            bg='black', fg='white',
            font=f
            ).grid(row=4, column=0, sticky=W, pady=10)  

        Label(
            anamnestic_frame, 
            text="  Injury history", 
            bg='black', fg='white',
            font=f
            ).grid(row=5, column=0, sticky=W, pady=10)  

        Label(
            anamnestic_frame, 
            text="  Pathologies", 
            bg='black', fg='white',
            font=f
            ).grid(row=6, column=0, sticky=W, pady=10)  

        Label(
            anamnestic_frame, 
            text="  Physical activity", 
            bg='black', fg='white',
            font=f
            ).grid(row=7, column=0, sticky=W, pady=10)  

        name_surname = Entry(
            anamnestic_frame, 
            font=f,
            validate='key'
            )

        gender = OptionMenu(
            anamnestic_frame,
            temp_for_gender,
            *gender_choices
        )

        age = Entry(
            anamnestic_frame, 
            font=f,
            validate='key'
            )
        age['validatecommand']=(age.register(testVal), '%P', '%d')

        hand = OptionMenu(
            anamnestic_frame,
            temp_for_hand,
            *hand_choices
        )

        injury_history = OptionMenu(
            anamnestic_frame,
            temp_for_injury,
            *injury_choices
        )

        pathologies = OptionMenu(
            anamnestic_frame,
            temp_for_pathologies,
            *pathologies_choices
        )
        
        physical_activity = OptionMenu(
            anamnestic_frame,
            temp_for_physical_activity,
            *physical_activity_choices
        )

        # ANTHROPOMETRIC FRAME

        anthropometric_frame = Frame(
            self.ws, 
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
            )
        anthropometric_frame= LabelFrame(self.ws, text='  ANTHROPOMETRIC MEASUREMENTS', fg='white', bg='black',font= ('Helvetica 13'))

        Label(
            anthropometric_frame, 
            text="  Height (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Weight (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Height to right trochanter (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=3, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Shoulder width (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=4, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Arm lenght (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=5, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Inseam height (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=6, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Fibula length (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=7, column=0, sticky=W, pady=10)


        Label(
            anthropometric_frame, 
            text="  Lower limb length (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=8, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  ASIS-Trochanter distance (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=9, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Knee width (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=10, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Ankle width (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=11, column=0, sticky=W, pady=10)

        Label(
            anthropometric_frame, 
            text="  Foot length (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=12, column=0, sticky=W, pady=10)

        height = Entry(
            anthropometric_frame, 
            font=f,
            validate='key'
            )
        height['validatecommand']=(height.register(testVal), '%P', '%d')

        weight = Entry(
            anthropometric_frame, 
            font=f,
            validate='key'
            )
        weight['validatecommand']=(weight.register(testVal), '%P', '%d')

        height_to_right_trochanter = Entry(
            anthropometric_frame,
            font=f,
            validate='key'
            )
        height_to_right_trochanter['validatecommand']=(height_to_right_trochanter.register(testVal), '%P', '%d')

        shoulder_width = Entry(
            anthropometric_frame,
            font=f,
            validate='key'
            )
        shoulder_width['validatecommand']=(shoulder_width.register(testVal), '%P', '%d')

        arm_lenght = Entry(
            anthropometric_frame, 
            font=f,
            validate='key'
            )
        arm_lenght['validatecommand']=(arm_lenght.register(testVal), '%P', '%d')


        inseam_height = Entry(
            anthropometric_frame, 
            font=f,
            validate='key'
            )
        inseam_height['validatecommand']=(inseam_height.register(testVal), '%P', '%d')


        fibula_length = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        fibula_length['validatecommand']=(fibula_length.register(testVal), '%P', '%d')


        lower_limb_length = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        lower_limb_length['validatecommand']=(lower_limb_length.register(testVal), '%P', '%d')


        ASIS_distance = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        ASIS_distance['validatecommand']=(ASIS_distance.register(testVal), '%P', '%d')


        knee_width = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        knee_width['validatecommand']=(knee_width.register(testVal), '%P', '%d')


        ankle_width = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        ankle_width['validatecommand']=(ankle_width.register(testVal), '%P', '%d')


        foot_length = Entry(
            anthropometric_frame, 
            font=f,
            validate='key',
            )
        foot_length['validatecommand']=(foot_length.register(testVal), '%P', '%d')


       

        #ENVIRONMENT FRAME 

        enviroment_frame = Frame(
            self.ws,
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
        )

        enviroment_frame= LabelFrame(self.ws, text='  ENVIRONMENT CONDITIONS', fg='white', bg='black',font= ('Helvetica 13'))

        Label(
            enviroment_frame, 
            text="  The test is performed", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)

        Label(
            enviroment_frame,
            text='  The working temperature is',
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)


        the_test_is_performed = OptionMenu(
            enviroment_frame,
            temp_for_testisperformed,
            *testisperformed
        )

        the_working_temperature_is = OptionMenu( 
            enviroment_frame,
            temp_for_temperature,
            *temperaturevariable,
        )

       



        #WORKING TASK FRAME

        working_task_frame = Frame(
            self.ws,
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
        )
        working_task_frame= LabelFrame(self.ws, text='  WORKING TASK', fg='white', bg='black',font= ('Helvetica 13'))


        Label(
            working_task_frame, 
            text="  Workstation height (cm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)


        Label(
            working_task_frame, 
            text="  Load weight (kg)", 
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)

        Label(
            working_task_frame,
            text='  The test duration is (min)',
            bg='black', fg='white',
            font=f
            ).grid(row=3, column=0, sticky=W, pady=10)


        Label(
            working_task_frame, 
            text="  No. technical actions per minute", 
            bg='black', fg='white',
            font=f
            ).grid(row=4, column=0, sticky=W, pady=10)

        workstation_height = Entry(
            working_task_frame, 
            font=f,
            validate='key',
            )
        workstation_height.insert(END,'87')
        workstation_height['validatecommand']=(workstation_height.register(testVal), '%P', '%d')

        
        load_weight = Entry(
            working_task_frame, 
            font=f,
            validate='key',
            )
        load_weight.insert(END,'3')
        load_weight['validatecommand']=(load_weight.register(testVal), '%P', '%d')


        test_duration = Entry(
            working_task_frame, 
            font=f,
            validate='key',
            )
        test_duration.insert(END,'10')
        test_duration['validatecommand']=(test_duration.register(testVal), '%P', '%d')


        technical_actions = Entry(
            working_task_frame, 
            font=f,
            validate='key',
            )
        technical_actions.insert(END,'20')
        technical_actions['validatecommand']=(technical_actions.register(testVal), '%P', '%d')


        # EMG FRAME

        emg_frame = Frame(
            self.ws,
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
        )

        emg_frame= LabelFrame(self.ws, text='  sEMG', fg='white', bg='black',font= ('Helvetica 13'))

        Label(
            emg_frame, 
            text="  sEMG system", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)

        Label(
            emg_frame, 
            text="  Sampling rate (Hz)", 
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)

        Label(
            emg_frame, 
            text="  No. channels", 
            bg='black', fg='white',
            font=f
            ).grid(row=3, column=0, sticky=W, pady=10)

        Label(
            emg_frame, 
            text="  Electrodes size (mm)", 
            bg='black', fg='white',
            font=f
            ).grid(row=4, column=0, sticky=W, pady=10)
            
        Label(
            emg_frame, 
            text="  Electrodes geometry", 
            bg='black', fg='white',
            font=f
            ).grid(row=5, column=0, sticky=W, pady=10)

        Label(
            emg_frame, 
            text="  Electrodes type", 
            bg='black', fg='white',
            font=f
            ).grid(row=6, column=0, sticky=W, pady=10)

        emg_system = Entry(
            emg_frame, 
            font=f,
            validate='key',
            )  
        emg_system.insert(END,'Raw Power')

        emg_sampling_rate = Entry(
            emg_frame, 
            font=f,
            validate='key',
            )
        emg_sampling_rate['validatecommand']=(emg_sampling_rate.register(testVal), '%P', '%d')
        emg_sampling_rate.insert(END,'1000')

        no_channels = Entry(
            emg_frame, 
            font=f,
            validate='key',
            )
        no_channels.insert(END,'8')
        no_channels['validatecommand']=(no_channels.register(testVal), '%P', '%d')

        electrodes_size = Entry(
            emg_frame, 
            font=f,
            validate='key',
            )
        electrodes_size.insert(END,'50')
        electrodes_size['validatecommand']=(electrodes_size.register(testVal), '%P', '%d')


        electrodes_geometry_shape = OptionMenu(
            emg_frame,
            temp_for_electrodes_geometry,
            *electrodes_geometry
        )

        insert_electrodes_type = OptionMenu(
            emg_frame,
            temp_for_electrodes_type,
            *electrodes_type
        )

         # MOTION CAPTURE SYSTEM FRAME

        mocap_frame = Frame(
            self.ws,
            bd=2, 
            bg='black',
            relief=SOLID, 
            padx=10, 
            pady=10
        )

        mocap_frame= LabelFrame(self.ws, text='  MOTION CAPTURE SYSTEM', fg='white', bg='black',font= ('Helvetica 13'))

        Label(
            mocap_frame, 
            text="  Motion Capture system", 
            bg='black', fg='white',
            font=f
            ).grid(row=1, column=0, sticky=W, pady=10)

        Label(
            mocap_frame, 
            text="  Sampling rate (Hz)", 
            bg='black', fg='white',
            font=f
            ).grid(row=2, column=0, sticky=W, pady=10)

        Label(
            mocap_frame, 
            text="  No. cameras", 
            bg='black', fg='white',
            font=f
            ).grid(row=3, column=0, sticky=W, pady=10)

        Label(
            mocap_frame, 
            text="  Markers", 
            bg='black', fg='white',
            font=f
            ).grid(row=4, column=0, sticky=W, pady=10)


        mocap_system = Entry(
            mocap_frame, 
            font=f,
            validate='key',
            )
        mocap_system.insert(END,'Optitrack')


        mocap_sampling_rate = Entry(
            mocap_frame, 
            font=f,
            validate='key',
            )
        mocap_sampling_rate.insert(END,'120')
        mocap_sampling_rate['validatecommand']=(mocap_sampling_rate.register(testVal), '%P', '%d')

        no_cameras = Entry(
            mocap_frame, 
            font=f,
            validate='key',
            )
        no_cameras.insert(END ,'6')
        no_cameras['validatecommand']=(no_cameras.register(testVal), '%P', '%d')

        markers = OptionMenu(
            mocap_frame,
            temp_for_markers,
            *markers_choice
        )

        register_btn = Button(
            mocap_frame, 
            width=15, 
            text='REGISTER', 
            font=f, 
            background='red',foreground='white',
            relief=SOLID,
            cursor='hand2',
            command=get_value
        )

        name_surname.grid(row=1, column=1, pady=10, padx=20)
        gender.grid(row=3, column=1, pady=10, padx=20)
        age.grid(row=2, column=1, pady=10, padx=20)
        hand.grid(row=4, column=1, pady=10, padx=20)
        injury_history.grid(row=5, column=1, pady=10, padx=20)
        pathologies.grid(row=6, column=1, pady=10, padx=20)
        physical_activity.grid(row=7, column=1, pady=10, padx=20)
        anamnestic_frame.pack(expand=True, fill='both', side='top')

        height.grid(row=1, column=1, pady=10, padx=20)
        weight.grid(row=2, column=1, pady=10, padx=20) 
        height_to_right_trochanter.grid(row=3, column=1, pady=10, padx=20)
        shoulder_width.grid(row=4, column=1, pady=10, padx=20)
        arm_lenght.grid(row=5, column=1, pady=10, padx=20)
        inseam_height.grid(row=6, column=1, pady=10, padx=20)
        fibula_length.grid(row=7, column=1, pady=10, padx=20)
        lower_limb_length.grid(row=8, column=1, pady=10, padx=20)
        ASIS_distance.grid(row=9, column=1, pady=10, padx=20)
        knee_width.grid(row=10, column=1, pady=10, padx=20)
        ankle_width.grid(row=11, column=1, pady=10, padx=20)
        foot_length.grid(row=12, column=1, pady=10, padx=20)
        anthropometric_frame.pack(expand=True, fill='both', side='left')

        the_test_is_performed.grid(row=1, column=1, pady=10, padx=20)
        the_working_temperature_is.grid(row=2, column=1, pady=10, padx=20)
        enviroment_frame.pack(expand=True, fill='both', side='left')
  
        workstation_height.grid(row=1, column=1, pady=10, padx=20)
        load_weight.grid(row=2, column=1, pady=10, padx=20)
        test_duration.grid(row=3, column=1, pady=10, padx=20)
        technical_actions.grid(row=4, column=1, pady=10, padx=20)
        working_task_frame.pack(expand=True, fill='both', side='left')

        emg_system.grid(row=1, column=1, pady=10, padx=20)
        emg_sampling_rate.grid(row=2, column=1, pady=10, padx=20)
        no_channels.grid(row=3, column=1, pady=10, padx=20)
        electrodes_size.grid(row=4, column=1, pady=10, padx=20)
        electrodes_geometry_shape.grid(row=5, column=1, pady=10, padx=20) 
        insert_electrodes_type.grid(row=6, column=1, pady=10, padx=20)
        emg_frame.pack(expand=True, fill='both', side='left')

        mocap_system.grid(row=1, column=1, pady=10, padx=20)
        mocap_sampling_rate.grid(row=2, column=1, pady=10, padx=20)
        no_cameras.grid(row=3, column=1, pady=10, padx=20)
        markers.grid(row=4, column=1, pady=10, padx=20)
        register_btn.grid(row=12, column=1, pady=10, padx=20)
        mocap_frame.pack(expand=True, fill='both', side='left')


       




        

    def set_variables_data(self):
        def apply():
            i=0
        
            try:
                for label in self.data_labels:
                    label.destroy()
            except: #non c'erano scitte labels
                pass
            
            self.data_labels=[]

            for var,name_var in zip(data_type,possible_variables):
                if var.get(): #se è stato selezionato nel checkbox
                    self.data_variables.append(name_var)
                    self.data_labels.append(tk.Label(self.master,text=f'{name_var}',bg='black',fg='white'))
            
            for label in self.data_labels:
                label.place(x=350,y=380 + i*20)
                i=i+1
            variables_window.destroy() 

        variables_window=tk.Toplevel(self.master,bg='black')
        variables_window.resizable(False,False)
        variables_window.protocol("WM_DELETE_WINDOW", apply)
        #geometria master centrata
        w = 300 # width for the Tk self
        h = 200 # height for the Tk self

        # get screen width and height
        ws = variables_window.winfo_screenwidth() # width of the screen
        hs = variables_window.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk self window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        variables_window.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
        
        #ICONA
        variables_window.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')

        self.data_variables=[] #variabile per controllare se è stato selezionato o meno un dispositivo BLE
        possible_variables=['LACTATE','POWER','V02','V3'] #variabile che conterrà le tuble (nome dispositivo, identificativo)
        data_type=[]
        
        for _ in range(len(possible_variables)):
            data_type.append(tk.IntVar(value=0))

        tk.Label(variables_window,text="DATA AVAILABLE VARIABLES",bg='black',fg='white',font=('Helvetica','10')).place(x=50,y=20) #posizionamento label per la selezione del tipo di acquisizione
        
        for val,name in enumerate(possible_variables): #bottoni relativi alla scelta della modalità di acquisizione
            checkbutton=tk.Checkbutton(variables_window,text=name,variable=data_type[val],bg='black',fg='white',selectcolor='black')
            checkbutton.place(x=30,y=40+(val+1)*20)

        self.set_variables_button= tk.Button(variables_window, text="OK",background='red',foreground='white',font=('Helvetica','8'),padx=5,pady=5,command=apply) #bottone start per far partire l'acquisizione
        self.set_variables_button.place(x=130,y=160)
    
    def scan_BLE(self):
        """scan for BLE devices and show a gui where available BLE could be selected
        """
        def ok_pressed(): #eseguita quando premo il button 'Ok' della GUI
            try:
                self.BLE_label.destroy()
                for label in self.BLE_devices_label:
                    label.destroy()
            except: #entra nell'except se non erano presenti dei dispositivi BLE
                pass
            from bleak.uuids import uuid16_dict
            uuid16_dict = {v: k for k, v in uuid16_dict.items()}
            self.BLE_MAC=[] #variabile che conterrà i MAC dei dispositivi presenti e i corrispondenti UUID d'interesse  
            self.BLE_devices_label=[]
            for var,ble_device in zip(BLE_type,BLE_devices):
                if var.get(): #se è stato selezionato nel checkbox
                    uuid16_dict = {v: k for k, v in uuid16_dict.items()}
                    services=service_explorer(ble_device.split(' ')[0][:-1]) #lista di tutti i service del dispositivo selezionato
                    if 'Heart Rate' in services: #mi aspetto che se tra i services c'è Heart Rate, questo dispositivo venga utilizzato per registrare l'HR
                        UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Heart Rate Measurement"))
                        self.BLE_MAC.append((ble_device.split(' ')[0][:-1],UUID,ble_device.split(':')[-1][1:]))#list of tubles with MAC, UUID and NAME
                        self.BLE_devices_label.append(tk.Label(self.master,text=f"{ble_device.split(':')[-1][1:]}",bg='black',fg='white'))
            """
            for var,ble_device in zip(BLE_type,BLE_devices):
                if var.get(): #se è stato selezionato nel checkbox
                    services=service_explorer(ble_device.split(' ')[0][:-1]) #lista di tutti i service del dispositivo selezionato
                    print(services)
                    if 'Heart Rate' in services: #mi aspetto che se tra i services c'è Heart Rate, questo dispositivo venga utilizzato per registrare l'HR
                        UUID = []
                        UUID1 = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Heart Rate Measurement"))
                        UUID.append(UUID1)
                        self.BLE_MAC.append((ble_device.split(' ')[0][:-1],UUID,ble_device.split(':')[-1][1:]))#list of tubles with MAC, UUID and NAME
                        self.BLE_devices_label.append(tk.Label(self.master,text=f"{ble_device.split(':')[-1][1:]}",bg='black',fg='white'))
                    if 'Cycling Speed and Cadence' in services and 'Cycling Power' in services: #rullo
                        UUID = []
                        UUID1 = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("CSC Measurement"))
                        UUID.append(UUID1)
                        UUID2 = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Cycling Power Measurement"))
                        UUID.append(UUID2)
                        self.BLE_MAC.append((ble_device.split(' ')[0][:-1],UUID,ble_device.split(':')[-1][1:]))#list of tubles with MAC, UUID and NAME
                        self.BLE_devices_label.append(tk.Label(self.master,text=f"{ble_device.split(':')[-1][1:]}",bg='black',fg='white'))
                    #stryd
                    if 'Generic Access Profile' in services and 'Generic Attribute Profile' in services and 'Cycling Power' in services and 'Running Speed and Cadence' in services and 'Unknown' in services and 'Unknown' in services and 'Battery Service' in services and 'Device Information' in services:
                        UUID = []
                        UUID1 = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("RSC Measurement"))
                        UUID.append(UUID1)
                        UUID2 = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Cycling Power Measurement"))
                        UUID.append(UUID2)
                        self.BLE_MAC.append((ble_device.split(' ')[0][:-1],UUID,ble_device.split(':')[-1][1:]))#list of tubles with MAC, UUID and NAME
                        self.BLE_devices_label.append(tk.Label(self.master,text=f"{ble_device.split(':')[-1][1:]}",bg='black',fg='white'))
            """
            BLE_window.destroy()
            for label,id in zip(self.BLE_devices_label, range(len(self.BLE_devices_label))):
                if id==0:
                    self.BLE_label=tk.Label(self.master,text="BLE devices",bg='black',fg='white')
                    self.BLE_label.place(x=20,y=370)
                label.place(x=35,y=(390+id*15))

        BLE_devices=scan_BLE() #ricerca dei dispositivi BLE
        try: #ogni volta che effettuo un nuovo scan provo ad elimare le label dei BLE nella GUI
            self.BLE_label.destroy() #label titolo BLE
            for label in self.BLE_devices_label: #label specifica per il singolo BLE
                label.destroy() 
        except: #entra nell'except se non erano presenti dei dispositivi BLE
            pass
        self.BLE_MAC=[]
        if not BLE_devices == []: #se sono presenti BLE
            #creates custom window
            BLE_window=tk.Toplevel(master=self.master)
            BLE_window.title('BLE DEVICES')
            BLE_window.geometry(f"{600}x{200 + len(BLE_devices)*20}")
            BLE_window.protocol("WM_DELETE_WINDOW", BLE_window.destroy)
            #centered geometry
            x = (BLE_window.winfo_screenwidth() - BLE_window.winfo_reqwidth()) / 2
            y = (BLE_window.winfo_screenheight() - BLE_window.winfo_reqheight()) / 2
            BLE_window.geometry("+%d+%d" % (x, y))
            BLE_window.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')
            BLE_window.configure(background='black')
            BLE_window.resizable(False,False)
            BLE_label=tk.Label(BLE_window, text=f'BLE DEVICES',font=('Ubuntu','12'),fg='white',bg='black')
            BLE_label.place(relx=0.35,rely=0.05)
            BLE_button=tk.Button(BLE_window,text="Ok",width=10,command=ok_pressed)
            BLE_button.place(relx=0.4,rely=0.85)

            #create checkbutton
            BLE_type=[] #variabile per controllare se è stato selezionato o meno un dispositivo BLE
            BLEs=[] #variabile che conterrà le tuble (nome dispositivo, identificativo)
            i=0
            for bles in BLE_devices:
                d=bles.split(':')[-1][1:]
                BLEs.append((d,i)) #tuple contenente il nome del dispositivo e l'indice (0,1...)
                BLE_type.append(tk.IntVar(value=0)) #variabile per gestire la scelta
                i=i+1
            tk.Label(BLE_window,text="BLE AVAILABLE DEVICES",bg='black',fg='white').place(x=10,y=50) #posizionamento label per la selezione del tipo di acquisizione
            
            for val,BLE_name in enumerate(BLEs): #bottoni relativi alla scelta della modalità di acquisizione
                checkbutton=tk.Checkbutton(BLE_window,text=BLE_name[0],variable=BLE_type[val],bg='black',fg='white',selectcolor='black')
                checkbutton.place(x=20,y=60+(val+1)*20)

            def select_deselect_all():
                for val in BLE_type:
                    if select_deselect_variable.get():
                        val.set(1)
                    else:
                        val.set(0)

            select_deselect_variable=tk.IntVar(value=0)
            select_deselect_checkbutton=tk.Checkbutton(BLE_window,text='Select/Deselect all',variable=select_deselect_variable,bg='black',fg='white',selectcolor='black',command=select_deselect_all)
            select_deselect_checkbutton.place(x=20,rely=0.85)

            #blocks the execution of the main application until the popup is closed
            BLE_window.transient(self.master)
            BLE_window.grab_set()
            self.master.wait_window(BLE_window)
        else: #se non sono presenti
            #show_popup(self.master,'BLE ERROR','Found 0 BLE devices')
            tk.messagebox.showinfo(title='BLE ERROR',message='Found 0 BLE devices')
            self.BLE_MAC=[] #variabile che conterrà i MAC dei dispositivi presenti e i corrispondenti UUID d'interesse
            try:
                self.BLE_label.destroy()
                for label in self.BLE_devices_label:
                    label.destroy()
            except: #entra nell'except se non erano presenti dei dispositivi BLE
                pass

    def TYPE_settings(self,id):
        """sets the variable to TRUE or FALSE depending on the acquisition type (TRUE=single, FALSE=double)
        """
        #questa funzione viene chiamata quando si preme un bottone nella sezione type
        type_set={
            0:True,
            1:False
        }
        self.TYPE=type_set.get(id) #set variabile TRUE/FALSE rispettivamente se viene premuto single o double
        ports = list(serial.tools.list_ports.comports()) #lista delle porte COM
        #seleziono solamente le COM collegate ad un dispositivo seriale
        porte_com=[]
        for p in ports:
            if(str(p).split('-')[-1].split('(')[0] in [' USB Serial Device ',' Dispositivo seriale USB ']): #se le com sono collegate ad un dispositivo seriale
                porte_com.append(str(p).split(' ')[0])

        if not self.TYPE and len(porte_com)<2: #se non ci sono collegate 2 schede mostro un popup e torno ad acquisizione singola
            tk.messagebox.showerror(title='DEVICER ERROR',message='just one device available')
            self.TYPE=True
            self.type_selection.current(0)
        self.master.focus()

    def TEMPLATE_settings(self,id):
        """sets the muscles for the selected template
        """
        #questa funzione viene chiamata quando si cambia template

        reset_muscle_values(self)   #prima devo resettare i valori della lista set_muscoli, nel caso in cui fossero stati cambiati usando la funzione ricerca nei combobox

        if(id == 15):
            self.cashier_template_button['state']='normal'
        else:
            self.cashier_template_button['state']='disabled'

        self.muscle1_selection.current(self.template_muscles[id][0])
        self.muscle2_selection.current(self.template_muscles[id][1])
        self.muscle3_selection.current(self.template_muscles[id][2])
        self.muscle4_selection.current(self.template_muscles[id][3])
        self.muscle5_selection.current(self.template_muscles[id][4])
        self.muscle6_selection.current(self.template_muscles[id][5])
        self.muscle7_selection.current(self.template_muscles[id][6])
        self.muscle8_selection.current(self.template_muscles[id][7])

        self.master.focus()
        
    def blink(self):
        """
        shows recording label and change 'led' color every 500ms
        """
        try:
            self.recording_label=tk.Label(self.master,text="RECORDING",justify=tk.LEFT,bg='black',fg='#FFFFFF') #posizionamento label recording
            self.recording_label.place(x=680,y=410)
            seconds=0
            time_string=time.strftime(f'%H:%M:%S',time.gmtime(seconds))
            self.time_label=tk.Label(self.master,text=f"{time_string}",justify=tk.LEFT,bg='black',fg='#FFFFFF',font=("Helvetiga", 16)) #posizionamento label time
            self.time_label.place(x=700,y=435)
            while not self.stop_blink:
                self.canvas.itemconfig(self.circle,outline="#FFFFFF", fill="#FF0000") # change color
                time.sleep(0.5)
                self.canvas.itemconfig(self.circle, outline="#FFFFFF",fill="#691503")
                time.sleep(0.5)
                seconds=seconds+1
                time_string=time.strftime(f'%H:%M:%S',time.gmtime(seconds))
                self.time_label.config(text=f"{time_string}")
    
        except Exception as e: #entra nell'exception quando chiudo la gui della registrazione mentre è in corso la registrazione, in quanto non trova più la canvas, oppure quando premo il tasto STOP
            try: #quando premo il tasto STOP
                self.canvas.itemconfig(self.circle, outline="#000000",fill="#000000")
                self.recording_label.config(fg="#000000")
                self.time_label.destroy()
                self.master.update_idletasks()
            except: #quando chiudo la gui della registrazione mentre è in corso la registrazione
                pass
        
    def insert_data(self):        
        """
        show a editable treeview, doubleclick to the value you want to change, than press enter
        """
        def delate_insert():
            try:
                selected_item = self.data_tree._tree.selection()[0] ## get selected item
                result=tk.messagebox.askyesno(title='info',message="Are you sure to delate this observation?")
                if result:
                    self.data_tree._tree.delete(selected_item)
                    self.top_level_data.lift() #la porto in primo piano
                else:
                    self.top_level_data.lift() #la porto in primo piano
            except:
                tk.messagebox.showinfo(title='info',message="Select a item, than press 'Delete Observation'")
                self.top_level_data.lift() #la porto in primo piano

        def save_insert():
            """
            save insert data
            """
            check_message=False
            #controllo se ci sono dei valori vuoti
            for line in self.data_tree._tree.get_children():
                if '' in self.data_tree._tree.item(line)['values']:
                    check_message=True
                    break

            if check_message: #se ci sono dei valori vuoti mostro un popup
                result=tk.messagebox.askyesnocancel(title='close',message='Are you sure to save? some data are empty!')                   
                if result==True: #si
                    self.top_level_data.withdraw() #chiudo la finestra
                elif result==False: #no
                    #cancello l'ultima osservazione
                    child_id = self.data_tree._tree.get_children()[-1]
                    self.data_tree._tree.focus(child_id)
                    self.data_tree._tree.selection_set(child_id)
                    self.data_tree._tree.delete(child_id)
                    self.top_level_data.withdraw() #chiudo la finestra
                else: #annulla
                    self.top_level_data.lift() #la porto in primo piano

            else: #se non ci sono valori vuoti
                self.top_level_data.withdraw() #chiudo la finestra

        if not self.check_first_entry: #se è la prima volta che premo insert data
            self.check_first_entry=True #variabile diventa vera
            self.time_data=[] #lista che conterrà i valori del tempo di inserimento dei dati
            self.top_level_data=tk.Toplevel(self.master) #creo una top level window
            self.top_level_data.resizable(False,False)
            #geometria master centrata
            w = 600 # width for the Tk self
            h = 500 # height for the Tk self

            # get screen width and height
            ws = self.top_level_data.winfo_screenwidth() # width of the screen
            hs = self.top_level_data.winfo_screenheight() # height of the screen

            # calculate x and y coordinates for the Tk self window
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)

            # set the dimensions of the screen 
            # and where it is placed
            self.top_level_data.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
            
            #ICONA
            self.top_level_data.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico')
            self.top_level_data.protocol("WM_DELETE_WINDOW",save_insert)
            
            #FRAMEs
            #frame dove posizionare il treeview
            self.frame_table = tk.Frame(self.top_level_data, bd=1,bg='black')
            #frame dove posizionare il button save data
            self.ok_frame = tk.Frame(self.top_level_data, bd=1, bg='black')
            self.frame_table.place(rely=0, relheight=0.9, relwidth=1)
            self.ok_frame.place(rely=0.9, relheight=0.1, relwidth=1)
        
            self.data_tree=customtree(self.top_level_data,self.frame_table)
            self.data_tree._tree.pack(side=tk.TOP,expand=True,fill=tk.BOTH)
            #setto le variabile da inserire
            column_width=int((w-200)/len(self.data_variables))
            self.data_tree.set_variables(self.data_variables,column_width)
            timestamp=self.time_label.cget("text")
            self.time_data.append(timestamp)
            val=tuple(['']*len(self.data_variables))
            self.data_tree._tree.insert("","end",text=f'{timestamp}',values=val)
            self.save_insert_button=tk.Button(self.ok_frame,text='Save Data',command=save_insert)
            self.save_insert_button.place(x=340,y=10)
            self.delate_insert_button=tk.Button(self.ok_frame,text='Delate Observation',command=delate_insert)
            self.delate_insert_button.place(x=180,y=10)
        else: #se non è la prima volta
            self.top_level_data.deiconify() #mostro la top level
            timestamp=self.time_label.cget("text") #nuovo inserimento con il timestamp
            self.time_data.append(timestamp)
            val=tuple(['']*len(self.data_variables))
            self.data_tree._tree.insert("","end",text=f'{timestamp}',values=val)
        
    def start(self):
        """sets the settings and call the acquisition functions on different processors
        """
        ports = list(serial.tools.list_ports.comports()) #lista delle porte COM
        #seleziono solamente le COM collegate ad un dispositivo seriale
        porte_com=[]
        for p in ports:
            if(str(p).split('-')[-1].split('(')[0] in [' USB Serial Device ',' Dispositivo seriale USB ']): #se le com sono collegate ad un dispositivo seriale
                porte_com.append(str(p).split(' ')[0])

        if len(porte_com)>0: #controllo se è collegata almeno una porta COM seriale     
            if not (self.reference_input.get() == '' or self.name_input.get() == '' or self.height_input.get() == '' or self.weight_input.get() == '' or self.date_input.get() == ''): #se sono stati specificati i campi obbligatori
                self.check_entries=False #variabile per controllare il type di height and weight
                self.all_disconnected=False
                self.weight_height_error=False
                self.same_muscle=False

                try:
                    height=self.height_input.get().replace(',','.')
                    height=float(height)
                    weight=self.weight_input.get().replace(',','.')
                    weight=float(weight)

                    if self.muscle1_selection.get()=='NOT CONNECTED' and self.muscle2_selection.get()=='NOT CONNECTED' and self.muscle3_selection.get()=='NOT CONNECTED' and self.muscle4_selection.get()=='NOT CONNECTED' and self.muscle5_selection.get()=='NOT CONNECTED' and self.muscle6_selection.get()=='NOT CONNECTED' and self.muscle7_selection.get()=='NOT CONNECTED' and self.muscle8_selection.get()=='NOT CONNECTED': #NON CONNESSO
                        self.all_disconnected=True
                        self.check_entries=False

                    else:
                        muscles=list([self.muscle1_selection.get(),
                                    self.muscle2_selection.get(),
                                    self.muscle3_selection.get(),
                                    self.muscle4_selection.get(),
                                    self.muscle5_selection.get(),
                                    self.muscle6_selection.get(),
                                    self.muscle7_selection.get(),
                                    self.muscle8_selection.get()])
                        not_connected=muscles.count('NOT CONNECTED')
                        used_muscles=list(filter(lambda a: a != 'NOT CONNECTED', muscles))
                        unique_muscles=list(set(used_muscles))
                        if not (len(unique_muscles) + not_connected)==8:
                            self.same_muscle=True
                            self.check_entries=False
     
                    if not (self.same_muscle or self.all_disconnected or self.weight_height_error):
                        self.check_entries=True

                except:
                    self.weight_height_error=True
                    self.check_entries=False

                if self.check_entries: #se tutte le entrate erano corrette
                    self.STOP=False #il bottone STOP non è stato premuto
                    #quando parte l'acqusizione disabilito i settings 
                    self.find_BLE_button.config(state='disabled')
                    self.athlete_import_button.config(state='disabled')

                    self.mode_selection['state']='disabled'
                    self.template_selection['state']='disabled'
                    self.type_selection['state']='disabled'

                    self.muscle1_selection['state']='disabled'
                    self.muscle2_selection['state']='disabled'
                    self.muscle3_selection['state']='disabled'
                    self.muscle4_selection['state']='disabled'
                    self.muscle5_selection['state']='disabled'
                    self.muscle6_selection['state']='disabled'
                    self.muscle7_selection['state']='disabled'
                    self.muscle8_selection['state']='disabled'


                    self.name_input.config(state='disabled')
                    self.height_input.config(state='disabled')
                    self.weight_input.config(state='disabled')
                    self.date_input.config(state='disabled')
                    self.reference_input.config(state='disabled')
                    self.description_input.config(state='disabled')
                    self.optitrack_checkbutton.configure(state = 'disabled')
                    self.optitrack_server.config(state='disabled')

                    if self.START: #se è possibile iniziare una nuova registrazione
                        self.stop_threads.clear() #quando parte una nuova acquisizione la variabile che controlla lo stop delle acquisizioni è falsa
                        self.start_event.clear() #inizialmente quando premo start la variabile che permette l'acquisizione è falsa, in attesa che tutte le periferiche diventino sincrone
                        MODE=self.mode_selection.current() #modalità da comunicare (MODE0, MODE1...)
                        id_muscoli=[] #lista che conterrà gli indici dei muscoli selezionati

                        try:
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle1_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle2_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle3_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle4_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle5_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle6_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle7_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                            id_muscoli.append(list(self.set_muscoli.keys())[list(self.set_muscoli.values()).index(self.muscle8_selection.get())])   #per ogni stringa muscolo calcolo il suo indice (keys) corrispondente nel dictionary
                        except:
                            tk.messagebox.showerror(title='ERROR',message='One of the muscles does not exist.')

                        #nome dell'atleta
                        name=self.name_input.get().replace(' ','_')

                        #task's description
                        description=self.description_input.get('0.0',tk.END)

                        #posizione reference
                        reference=self.reference_input.get()

                        #dare of birth
                        date_of_birth=self.date_input.get()

                        description=f'NAME {name}\n\nDATE OF BIRTH {date_of_birth}\n\nHEIGHT {height} cm\n\nWEIGHT {weight} Kg\n\nDESCRIPTION:\nReference: {reference}.\n{description}\n'

                        

                        #CALCOLO DEL PATH DELLA DIRECTORY
                        timestr = time.strftime("%Y%m%d_%H%M%S")
                        #se non è stato specificato un nome viene utilizzato 'unknown'
                        if name=='':
                            name='Unknown'
                        #se sono presenti degli spazi vengono sostituiti con '_'
                        name=name.replace(" ", "_")

                        documents_path=os.path.expanduser('~\Documents')
                        if not (os.path.isdir(os.path.join(f'{documents_path}','Recordings'))): #se non esiste questa directory la creo
                                os.mkdir(os.path.join(f'{documents_path}','Recordings'))
                        if not (os.path.isdir(os.path.join(f'{documents_path}','Recordings',f'{name}'))): #se non esiste questa directory la creo
                                os.mkdir(os.path.join(f'{documents_path}','Recordings',f'{name}'))
                        if not (os.path.isdir(os.path.join(f'{documents_path}','Recordings',f'{name}',f'REC_{self.template_selection.get()}_{timestr}'))): #se non esiste questa directory la creo
                                os.mkdir(os.path.join(f'{documents_path}','Recordings',f'{name}',f'REC_{self.template_selection.get()}_{timestr}'))
                                path_directory=os.path.abspath(os.path.join(f'{documents_path}','Recordings',f'{name}',f'REC_{self.template_selection.get()}_{timestr}'))

                        #button to instert data

                        self.path_csv_insert_data=os.path.abspath(os.path.join(f'{path_directory}',f'Task_data_{timestr}.csv'))
                        try:
                            if len(self.data_variables)>0:
                                self.insert_data_button.config(text="INSERT DATA",command=self.insert_data)
                            else:
                                self.insert_data_button.config(text="INSERT DATA",state='disabled',command=self.insert_data)
                        except:
                            self.insert_data_button.config(text="INSERT DATA",state='disabled',command=self.insert_data)

                        #utilizzo processori differenti per la registrazione dei segnali Emg e dell'optitrack 
                        serial_1_number=self.porte_com[0][-1] #prendo l'ultimo carattere che rappresenta il numero della COM selezionata
                        self.thread1=multiprocessing.Process(target=continuos_acquiring, args=(serial_1_number,self.start_event,self.stop_threads,self.hide_event,self.delete_button_event,MODE,id_muscoli,path_directory,description,self.additional_data_form,False,))
                        if self.optitrack_selected.get():
                            optitrack_server=self.optitrack_server.get()
                            self.optitrack_IP=optitrack_server
                            self.thread_optitrack=multiprocessing.Process(target=continuos_optitrack,args=(self.start_event,self.stop_threads,optitrack_server,False,))
                            self.thread_optitrack.start()
                        #parte l'inizializzazione delle periferiche in attesa che la variabile che gestisce l'acquisizione diventi vera
                        self.thread1.start()

                        if not self.TYPE: #se l'acquisizione è doppia parte anche la seconda acquisizione
                            serial_2_number=self.porte_com[1][-1] #prendo l'ultimo carattere
                            self.thread2=multiprocessing.Process(target= continuos_acquiring, args=(serial_2_number,self.start_event,self.stop_threads,self.hide_event,self.delete_button_event,MODE,id_muscoli,path_directory,description,self.additional_data_form,False,))
                            self.thread2.start()
                        
                        try:
                            if not self.BLE_MAC == []:
                                BLE_MAC=self.BLE_MAC
                                self.thread_BLE=multiprocessing.Process(target=BLE_acquiring, args=(BLE_MAC,self.start_event,self.stop_threads,path_directory,)) #faccio partire l'acquisizione dei dispositivi BLE
                                self.thread_BLE.start()
                        except Exception as e: #entra nell'except quando self.BLE_MAC non è definito, ovvero quando non si effettua lo scan dei dispositivi
                            pass

                        time.sleep(10) #attendo 4 secondi per permettere l'inizializzazione dei processi prima del while loop, per renderli più sincroni
                        
                        #la variabile per far partire l'acquisizione diventa vera
                        self.start_event.set() #parte l'acquisizione
                        self.START=False #una volta che è attiva una registrazione non è possibile farne partire un'altra
                        self.stop_blink=False
                        self.thread_blink=threading.Thread(target=self.blink) #parte il thread per far lampeggiare un'icona sulla gui
                        self.thread_blink.daemon=True
                        self.thread_blink.start()
                        self.start_button.configure(text = "STOP", command=self.stop) #il pulsante ora diventa di STOP (uyilizzo di un solo pulsante)
                        #self.find_BLE_button.destroy() #elinimo il button per la ricerca dei BLE 
                        self.show_hide_plot_button= tk.Button(self.master, text="HIDE MUSCLES",background='red',foreground='white',font=('Helvetica','8'),padx=5,pady=5,command=self.show_hide) #bottone start per far partire l'acquisizione
                        self.show_hide_plot_button.place(x=750,y=360) #posizionamento bottone start
                        self.delete_button_event.clear()
                        self.check_delete_button=True #variabile per andare a controllare se bisognia eliminare il burron hide_plot
                        self.thread_button=threading.Thread(target=self.thread_delete_button) 
                        self.thread_button.daemon=True
                        self.thread_button.start()
                    else:
                        pass
                        #print('\nProcesso in esecuzione, premere STOP per interromperlo')
                else:
                    if self.weight_height_error:
                        tk.messagebox.showerror(title='ERROR',message='Weight and Height fields must be numbers')
                    elif self.all_disconnected:
                        tk.messagebox.showerror(title='ERROR',message='All channels disconnected')
                    else:
                        tk.messagebox.showerror(title='ERROR',message='Same muscle connected at different channels')

            else: #se non sono stati specificati tutti i campi obbligatori
                tk.messagebox.showerror(title='MANDATORY FIELDS',message='Please, specify all mandatory fields')
        else:
            tk.messagebox.showerror(title='DEVICE ERROR',message='No device available')

    def show_hide(self):
        """
        shows/hide realtime plot
        """
        self.hide_event.set() #quando premo il pulsante show/hide l'evento diventa vero (in acquisition verrà nascosto o mostrato il plot)
        #se prima il pulsante era HIDE ora diventa SHOW e viceversa
        button_text = self.show_hide_plot_button['text']
        if button_text == 'HIDE MUSCLES':
            self.show_hide_plot_button.configure(text = "SHOW MUSCLES")
        elif button_text == 'SHOW MUSCLES':
            self.show_hide_plot_button.configure(text = "HIDE MUSCLES")

    def thread_delete_button(self):
        """
        deletes shows/hide button
        """
        while self.check_delete_button: #diventa falsa quando stoppo la registrazione o quando chiudo il plot realtime direttamente dalla sua finestra (tasto X)
            if self.delete_button_event.is_set(): #l'evento diventa vero quando chiudo il plot realtime direttamente dalla sua finestra (tasto X)
                self.show_hide_plot_button.destroy()
                self.check_delete_button=False

    def stop(self):
        """stops the acquisition and closes csv file
        """
        self.STOP=True #è stato premuto il tasto stop
        self.START=True #è possibile far ripartire una nuova acquisizione
        self.check_delete_button=False #quando premo stop non devo più andare a controllare se eliminare il pulsante show/hide

        if self.check_first_entry:
            if len(self.data_tree._tree.get_children())>0: #se è stato inserito almeno un dato
                #save inserted_data
                csv_file=open(self.path_csv_insert_data, 'w+') #open a .csv file and write header
                filewriter = csv.writer(csv_file, delimiter=';',
                                        quotechar=' ', quoting=csv.QUOTE_MINIMAL,lineterminator = '\n')

                var_names=list(self.data_variables)
                var_names.insert(0,'TIME')
                filewriter.writerow(var_names) #csv header
                
                id=0
                for line in self.data_tree._tree.get_children():
                    val=[]
                    for values in self.data_tree._tree.item(line)['values']:
                        val.append(values)
                    val.insert(0,self.time_data[id])
                    id=id+1
                    filewriter.writerow(val)
                csv_file.close()
            
            self.check_first_entry=False

        try:
            self.top_level_data.destroy()
            self.top_level_data=None
        except:
            self.top_level_data=None

        
        self.insert_data_button.config(text="SET VARIABLES DATA",state='normal',command=self.set_variables_data)
        try:
            for label in self.data_labels:
                label.destroy()
        except: #non c'erano scitte labels
            pass


        try: #se è presente il pulsante lo elimino
            self.show_hide_plot_button.destroy()
        except: #entra nell'exception se non è presente il button show_hide (può non essere presente se chiudo il plot realtime 'manualmente')
            pass

        try:
            self.BLE_label.destroy()
            for label in self.BLE_devices_label:
                label.destroy()
        except: #entra nell'except se non erano presenti dispositivi BLE
            pass

        self.canvas.itemconfig(self.circle, outline="#000000",fill="#000000")
        
        try:
            self.recording_label.config(fg="#000000")
            self.time_label.destroy()

        except Exception as e: #entra se la label era stata distrutta correttamente
            pass
            #print(e)
        
        self.master.update_idletasks() 

        self.BLE_MAC=[] #elinimo il contenuto dei dispositivi BLE per una nuova acquisizione

        if self.TYPE: #se l'acquisizione è singola
            if(self.thread1): #la funzione stop deve essere eseguita solo quando c'è attivo il processo
                self.stop_threads.set() #la variabile per stoppare i processi diventa vera
                self.thread1.join() #join thread prima scheda
                if self.optitrack_selected.get():
                    self.thread_optitrack.join()
                self.stop_blink=True
                self.thread1 = None
                self.thread_optitrack= None
                self.thread_blink=None
                self.thread_button=None
        else:
            if(self.thread1 and self.thread2): #la funzione stop deve essere eseguita solo quando sono attivi i processi
                self.stop_threads.set()
                self.thread1.join()
                self.thread2.join()
                if self.optitrack_selected.get():
                    self.thread_optitrack.join()
                self.stop_blink=True
                self.thread1 = None
                self.thread2 = None
                self.thread_blink=None
                self.thread_button=None
                self.thread_optitrack= None

        #una volta stoppata l'acqusizione riabilito i settings
        self.find_BLE_button.config(state='normal')
        self.athlete_import_button.config(state='normal')

        self.mode_selection['state']='readonly'
        self.template_selection['state']='readonly'
        self.type_selection['state']='readonly'

        self.muscle1_selection['state']='normal'
        self.muscle2_selection['state']='normal'
        self.muscle3_selection['state']='normal'
        self.muscle4_selection['state']='normal'
        self.muscle5_selection['state']='normal'
        self.muscle6_selection['state']='normal'
        self.muscle7_selection['state']='normal'
        self.muscle8_selection['state']='normal'

        self.name_input.config(state='normal')
        self.height_input.config(state='normal')
        self.weight_input.config(state='normal')
        self.date_input.config(state='normal')
        self.reference_input.config(state='normal')
        self.description_input.config(state='normal')
        self.optitrack_checkbutton.configure(state = 'normal')
        self.optitrack_server.config(state='normal')

        self.start_button.configure(text = "START", command=self.start)

    def close(self):
        """calls stops function and close the window
        """
        self.stop() #ferma i processi
        self.master.destroy() #chiude l'applicazione

def reset_muscle_values(self):
    #resetto i valori del muscolo che veninano modificati nella funzione check_input

    self.muscle1_selection['values']=list(self.set_muscoli.values())
    self.muscle2_selection['values']=list(self.set_muscoli.values())
    self.muscle3_selection['values']=list(self.set_muscoli.values())
    self.muscle4_selection['values']=list(self.set_muscoli.values())
    self.muscle5_selection['values']=list(self.set_muscoli.values())
    self.muscle6_selection['values']=list(self.set_muscoli.values())
    self.muscle7_selection['values']=list(self.set_muscoli.values())
    self.muscle8_selection['values']=list(self.set_muscoli.values())


