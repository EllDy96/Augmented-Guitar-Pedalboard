# MenuBar e StatusBar
from cProfile import label
import tkinter as tk

#Definizione di una classe per la gestione dei menù
class Menubar:
    """controls menubar options
    """
    
    def __init__(self,parent):
        #creazione del menù
        font_spec=("ubuntu",10)
        self.parent=parent
        self.menubar=tk.Menu(self.parent.master,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black',font=font_spec)
        self.parent.master.config(bg='#2A2C2B',menu=self.menubar)

        #file menù
        self.file_dropdown=tk.Menu(self.menubar,font=font_spec,tearoff=0,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black')
        self.file_dropdown.add_command(label="New Acquisition",command=self.parent.new_acquisition)
        self.file_dropdown.add_command(label="Load Workout",command=self.parent.load_workout)
        self.file_dropdown.add_command(label='PCA',command=self.parent.load_pca_file)
        self.file_dropdown.add_command(label="Export .xlsx",command=self.parent.export)
        self.file_dropdown.add_command(label="Export rms",command=self.parent.export_all_rms)
        self.file_dropdown.add_separator()
        self.file_dropdown.add_command(label="Exit",command=self.parent.close)

        #channels menù
        self.channel_dropdown=tk.Menu(self.menubar,font=font_spec,tearoff=0,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black')
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(0))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(1))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(2))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(3))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(4))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(5))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(6))
        self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(7))
        self.channel_dropdown.entryconfig(0, background='#DCDCDC',foreground='red')

        #settings menù
        settings_dropdown=tk.Menu(self.menubar,font=font_spec,tearoff=0,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black')
        settings_dropdown.add_command(label="Features Settings", command=self.parent.features_settings)
        settings_dropdown.add_command(label="Filter Settings",command=self.parent.set_filter)

        #plot menù
        plot_dropdown=tk.Menu(self.menubar,font=font_spec,tearoff=0,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black')
        plot_dropdown.add_command(label="All channels",command=self.parent.all_channels)
        plot_dropdown.add_command(label="Fatigue analysis",command=self.parent.fatigue)
        plot_dropdown.add_command(label="Compute features",command=self.parent.compute_features)

        #help menù
        help_dropdown=tk.Menu(self.menubar,font=font_spec,tearoff=0,background='#DCDCDC', foreground='black',activebackground='white', activeforeground='black')
        help_dropdown.add_command(label="Documentation",command=self.parent.documentation)
        help_dropdown.add_command(label="Quick Start",command=self.parent.quick_start)
        help_dropdown.add_command(label="About",command=self.parent.about)

        #add all menù
        self.menubar.add_cascade(label="File", menu=self.file_dropdown)
        self.menubar.add_cascade(label="Muscles", menu=self.channel_dropdown)
        self.menubar.add_cascade(label="Settings", menu=settings_dropdown)
        self.menubar.add_cascade(label="Plot", menu=plot_dropdown)
        self.menubar.add_cascade(label="Help", menu=help_dropdown)
        
        #inizialmente questi menù sono disabilitati
        self.file_dropdown.entryconfigure("Export .xlsx", state="disabled")
        self.file_dropdown.entryconfigure("Export rms", state="disabled")
        self.menubar.entryconfigure("Muscles", state="disabled")
        self.menubar.entryconfigure("Plot", state="disabled")
        self.menubar.entryconfigure("Settings", state="disabled")

    def uptade_channel_labels(self,muscles_names):
        """sets the channels' labels with the muscles' names considered, after EMG file is loaded

        Args:
           muscles_names(list): list of muscles' names
        """
        
        for i in range(self.channel_dropdown.index('end'),7): #ogni volta che carico un workout parto con la possibilità di avere 8 canali
            self.channel_dropdown.add_command(label='',command=lambda:self.parent.change_channel(i))

        last=self.channel_dropdown.index('end') #number of items
        first=len(muscles_names)
        
        if not first==8: #elimino i canali non utilizzati
            self.channel_dropdown.delete(first,last)

        for i in range(len(muscles_names)): #aggiorno le label dei canali presenti
            self.channel_dropdown.entryconfigure(i, label=muscles_names[i])

class Statusbar:
    """menages the statusbar behaviour
    """

    def __init__(self,parent):
        font_specs=("Ubuntu",8)

        self.status=tk.StringVar()
        self.status.set(f"EMG {parent.title_emg}\t   MUSCLE {parent.muscle_name}") #parametri inizialmente settati a None

        #label con background nero e foreground bianco
        label=tk.Label(parent.master, textvariable=self.status, fg="#000000", bg="#DCDCDC", anchor='sw', height=0, font=font_specs)#non è possibile cambiare il font all'interno della stringa
        label.pack(side=tk.BOTTOM,fill=tk.BOTH)
    
    def update_status(self,status,*args):
        """updates the string shown in the statusbar
    
        Args:
            status(string): status to be displayed
        """
        if isinstance(args[0],bool):
            self.status.set(status)