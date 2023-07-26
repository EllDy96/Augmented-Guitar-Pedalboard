import tkinter as tk
from tkinter import ttk

from PIL import ImageTk, Image
import matplotlib.pyplot as plt
import numpy as np
import os

class CustomNotebook(ttk.Notebook):
    """A ttk Notebook with close buttons on each tab"""

    __initialized = False

    def __init__(self, app, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        self.app=app

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._active = None

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button"""

        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index

    def on_close_release(self, event):
        """Called when the button is released over the close button"""
        if not self.instate(['pressed']):
            return

        element =  self.identify(event.x, event.y)
        index = self.index("@%d,%d" % (event.x, event.y))

        if "close" in element and self._active == index:
            name = self.tab(index, option="text")
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")
                
        self.state(["!pressed"])
        self._active = None
        
        if name == 'home': #se chiudo la tab home la riapro e la posiziono sempre come prima tab
            try:
                self.insert(0,self.app.tab_home, text='home') #Insert the tab
            except: #exception se era aperta solo la tab home quando l'ho chiusa
                self.add(self.app.tab_home, text='home') #Add the tab

            self.pack(expand=1, fill="both")  # Pack to make visible
            
            #aggiunta immagine iniziale
            self.app.img_path=os.path.abspath(os.path.join(__file__,'..', '..','LWT3.jpg')) #path dell'immagine da caricare
            self.app.img=ImageTk.PhotoImage(Image.open(self.app.img_path)) #immagine iniziale
            self.app.img_display= tk.Label(self.app.tab_home,bg='black',image=self.app.img) #creo una label in cui inserisco l'immagine caricata
            self.app.img_display.place(x=0, y=0, relwidth=1, relheight=1)
            self.select(self.app.tab_home) #focus alla tab_home
            
        if name == 'All channels': #se la tab All channels è stata chiusa
            for i in range(len(self.app.ar_fig_all)):
                plt.figure(self.app.ar_fig_all[i].number).clear()
                plt.close(self.app.ar_fig_all[i]) #chiudo le figure

            self.app.ar_fig_all=[] #reinizializzo l'array
            self.app.canvas_all_channels.get_tk_widget().pack_forget()
            self.app.canvas_all_channels.get_tk_widget().destroy()
            self.app.toolbar_all_channels.pack_forget()
            self.app.toolbar_all_channels.destroy()
            self.app.all_channels_plot_selection.destroy()

            self.app.all_channels_plot_selection=None
            self.app.tab_all_channels = None #reinizializzo a None la tab
        
            self.app.check_tab_all_channels=False
            self.app.canvas_all_channels=None
            self.app.toolbar_all_channels=None

        if name == 'Fatigue analysis': #se la tab Fatigue analysis non è aperta
            for i in range(len(self.app.ar_fig_fatigue)):
                plt.figure(self.app.ar_fig_fatigue[i].number).clear()
                plt.close(self.app.ar_fig_fatigue[i])
            
            self.app.ar_fig_fatigue=[] #reinizializzo l'array
            self.app.canvas_fatigue.get_tk_widget().pack_forget()
            self.app.canvas_fatigue.get_tk_widget().destroy()
            self.app.toolbar_fatigue.pack_forget()
            self.app.toolbar_fatigue.destroy()
            self.app.muscle_selection.destroy()

            self.app.muscle_selection=None
            self.app.tab_fatigue = None #reinizializzo a None la tab
            self.app.check_tab_fatigue=False
            self.app.canvas_fatigue=None
            self.app.toolbar_fatigue=None

        if name == 'features': #se la tab features è chiusa
            plt.figure(self.app.fig_compute.number).clear()
            plt.close(self.app.fig_compute)
            self.app.canvas_compute.get_tk_widget().pack_forget()
            self.app.canvas_compute.get_tk_widget().destroy()
            self.app.canvas_compute=None
            self.app.toolbar_compute.pack_forget()
            self.app.toolbar_compute.destroy()
            self.app.toolbar_compute=None
            
            if not self.app.copy_button.destroy()==None:
                self.app.copy_button.destroy()
                self.app.copy_button=None

            if not self.app.clear_button.destroy()==None:
                self.app.clear_button.destroy()
                self.app.clear_button=None

            if not self.app.compute_button.destroy()==None:
                self.app.compute_button.destroy()
                self.app.compute_button=None

            self.app.check_tab_editor = False #reinizializzo a None la tab
            if not self.app.textarea == None: #se c'erano scritte delle features nel'editor quando l'ho chiuso
                #salvo il contenuto dell'editor in una variabile
                #(alla prossima pressione del tasto compute, l'editor verrà inizializzato con questo contenuto)
                self.app.text_content=self.app.textarea.get(1.0,tk.END) 

        for channel in range(self.app.number_of_channels):
            if name == self.app.array_nome_muscoli[channel]: #se la tab del muscolo i-esimo non è aperta 
                for i in range(np.shape(self.app.ar_fig)[1]):
                    if not self.app.ar_fig[channel][i]==None:
                        plt.figure(self.app.ar_fig[channel][i].number).clear()
                        plt.close(self.app.ar_fig[channel][i])
                        self.app.ar_fig[channel][i]=None
                
                if not self.app.canvas_single_channel[channel]==None:
                    self.app.canvas_single_channel[channel].get_tk_widget().pack_forget()
                    self.app.canvas_single_channel[channel].get_tk_widget().destroy()
                    self.app.canvas_single_channel[channel]=None
                
                if not self.app.toolbar_single_channel[channel]==None:
                    self.app.toolbar_single_channel[channel].pack_forget()
                    self.app.toolbar_single_channel[channel].destroy()
                    self.app.toolbar_single_channel[channel]=None
                
                if not self.app.single_channel_plot_selection[channel]==None:
                    self.app.single_channel_plot_selection[channel].destroy()
                    self.app.single_channel_plot_selection[channel]=None

                if not self.app.change_features_single_channel[channel]==None:
                    self.app.change_features_single_channel[channel].destroy()
                    self.app.change_features_single_channel[channel]=None

                if not self.app.change_BLE_single_channel[channel]==None:
                    self.app.change_BLE_single_channel[channel].destroy()
                    self.app.change_BLE_single_channel[channel]=None

                if not self.app.change_opti_feature_single_channel[channel]==None:
                    self.app.change_opti_feature_single_channel[channel].destroy()
                    self.app.change_opti_feature_single_channel[channel]=None

                self.app.tab_channel[channel] = None #reinizializzo a None la tab
                self.app.check_tab_channel[channel]=False

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                '''),
            tk.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                '''),
            tk.PhotoImage("img_closepressed", data='''
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            ''')
        )

        style.element_create("close", "image", "img_close",
                            ("active", "pressed", "!disabled", "img_closepressed"),
                            ("active", "!disabled", "img_closeactive"), border=8, sticky='')
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe", 
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top", 
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top", 
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),
                                ]
                        })
                    ]
                })
            ]
        })
    ])

if __name__ == "__main__":
    root = tk.Tk()

    notebook = CustomNotebook(width=200, height=200)
    notebook.pack(side="top", fill="both", expand=True)

    for color in ("red", "orange", "green", "blue", "violet"):
        frame = tk.Frame(notebook, background=color)
        notebook.add(frame, text=color)

    root.mainloop()