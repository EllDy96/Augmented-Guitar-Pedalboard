import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Progressbar
import os
import inspect

def show_progress_bar(start_stop_event,text):
    """
    shows a popup with a red progress bar

    Args:
        start_stop_event(multiprocessing.Event): multiprocessing event to synchronize different processes
        text(str): label text above the progressbar
    """
    def on_close_loading():
        pass

    def check_stop_event():
        if start_stop_event.is_set():
            window_progress.after(100,check_stop_event)  
        else:
            window_progress.quit()

    if start_stop_event:
        master_process=tk.Tk()
        master_process.withdraw()
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
        window_progress=tk.Toplevel(master=master_process) #creazione di una finestra che mostrerà la barra di progresso
        window_progress.resizable(False, False) #dimensioni fisse
        window_progress.title("LWT3") #titolo della finestra
        window_progress.iconbitmap(rf'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\lwt3_icon.ico') #icona
        window_progress.geometry("300x100") #dimensione della finestra
        #geometria della finestra centrata
        x = (window_progress.winfo_screenwidth() - window_progress.winfo_reqwidth()) / 2
        y = (window_progress.winfo_screenheight() - window_progress.winfo_reqheight()) / 2
        window_progress.geometry("+%d+%d" % (x, y))
        window_progress.protocol("WM_DELETE_WINDOW", on_close_loading) #la finestra quando viene premuto il tasto di chiusura non fa niente
        window_progress.configure(background='black') #background black
        progress_label= tk.Label(window_progress,text=f'{text}',font=("Helvetica", 12),fg='white',bg='black') #aggiunta label
        progress_label.place(relx=0.5, rely=0.25, anchor=tk.CENTER) #posizionamento label
        progress = Progressbar(window_progress,style='red.Horizontal.TProgressbar',orient="horizontal",length=250,  mode='indeterminate') #creazione barra di progresso
        progress.place(x=25,rely=0.5) #posiziono la barra di progresso
        progress.start() #faccio partire la barra di progresso
        window_progress.after(100,check_stop_event)
        window_progress.mainloop()
        
    progress.stop() #stoppo la barra di progresso
    progress.grid_forget() #elimino la barra di progresso
    window_progress.destroy()