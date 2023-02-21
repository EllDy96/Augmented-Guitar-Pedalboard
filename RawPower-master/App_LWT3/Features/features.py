#FUNCTIONS THAT COMPUTE FEATURES
import numpy as np
import math
from scipy.integrate import simps
from scipy import signal

def RMS(vect):
    """computes the root mean square 
    
    Args:
        vect(array_like): array on which compute RMS
 
    Returns: 
        float: RMS value
    """
    return np.sqrt(np.sum(np.square(vect))/np.size(vect))

def MAV(vect):
    """computes the mean absolute value
    
    Args:
        vect(array_like): array on which compute MAV
 
    Returns: 
        float: MAV value
    """
    return np.mean(np.absolute(vect))

def IEMG(vect):
    """computes the integreted EMG
    
    Args:
        vect(array_like): array on which compute IEMG
 
    Returns: 
        float: IEMG value
    """
    return np.sum(np.absolute(vect))

def VAR(vect):
    """computes the variance
    
    Args:
        vect(array_like): array on which compute variance
 
    Returns: 
        float: VAR value
    """
    return np.sum(np.square(vect))/(np.size(vect)-1)

def WAMP(vect,th):
    """computes the willison amplitude
    
    Args:
        vect(array_like): array on which compute willison amplitude
        th (int): threshold used to compute the feature, has to be set as a percentage of full range during a calibration phase 

    Returns: 
        float: WAMP value
    """
    return sum(np.where(vect[:-1]-vect[1:]>=th,1,0))

def WL(vect):
    """computes the waveform length
    
    Args:
        vect(array_like): array on which compute the waveform length

    Returns: 
        float: WL value
    """
    return np.sum(np.absolute(vect[1:]-vect[:-1]))

def ZC(vect):
    """computes the zero_crossing
    
    Args:
        vect(array_like): array on which compute the zero crossing

    Returns: 
        int: ZC value
    """
    return len(np.where(np.diff(np.sign(vect)))[0])

def SSC(vect,th):
    """computes the slope sign change
    
    Args:
        vect(array_like): array on which compute slope sign change
        th(int): threshold used to compute the feature, has to be set as a percentage of full range during a calibration phase 

    Returns: 
        int: SSC value
    """
    return sum(np.where(np.multiply(vect[1:-1]-vect[:-2],vect[1:-1]-vect[2:])>=th,1,0))

def MNF(freqs, psd):
    """computes the mean frequency of the spectrum 
    
    Args:
        freqs(array_like): frequency values
        psd (array_like): psd values of the corresponding frequencies 

    Returns: 
        float: MNF value
    """
    return np.sum(np.multiply(freqs,psd))/np.sum(psd)

def MDF(freqs, psd):
    """computes the median frequency of the spectrum 
    
    Args:
        freqs(array_like): frequency values
        psd (array_like): psd values of the corresponding frequencies 

    Returns: 
        float: MDF value
    """
    #la funzione simps integra i valori di psd, e quando l'area alla destra e alla sinistra sono uguali restituisce il valore della frequenza
    for f in range(len(freqs)-1):
        if((simps(psd[:f+1], dx=1)-simps(psd[f+1:], dx=1))>=0):
            return freqs[f]
    return None

def window_rms(input_signal, window_size):
    """computes RMS along the signal through convolution 
    
    Args:
        input_signal(array_like): original signal
        window_size (int): length of the rectangular window 
 
    Returns: 
        array_like: RMS values
    """
    a2 = np.power(input_signal,2)
    window = np.ones(window_size)/float(window_size)
    return np.sqrt(np.convolve(a2, window, 'valid'))

def window_MNF(data,Tout,T_window,fsampling):
    '''computes signal's mean frequency every Tout seconds, considering a window length of T_window seconds centered on the time considered

    Args:
        data(array_like): original time signal
        Tout(int): time period in seconds, every Tout seconds a mean frequency is computed
        T_window(int): time in seconds of the window used to compute the mean frequency, it is centered on the time considered
        fsampling(int): sampling frequency 

    Returns: 
        array_like: mean frequency values
    Returns:
        array_like: time instants in seconds where mean frequencies are computed
    '''
    Tcampioni=Tout*fsampling #conversione dei secondi in campioni
    Tcampioni_finestra=T_window*fsampling  #nperseg=Tcampioni_finestra
    MNF_it=[]
    time_plot=[]
    for i in range(math.floor(len(data)/Tcampioni)): #determina il numero di MNF che vengono calcolate sul segnale
        if((Tcampioni*(i+1)+Tcampioni_finestra/2)>len(data)): #se la finestra su cui calcolo l'MNF esce dal segnale, prendo solo i campioni apparteneti al segnale 
            f,p=signal.welch(data[int(Tcampioni*(i+1)-Tcampioni/2):],fsampling) #calcolo dello spettro
        elif((Tcampioni*(i+1)-Tcampioni_finestra/2)<0): #se la finestra su cui calcolo l'MNF esce dal segnale, prendo solo i campioni apparteneti al segnale
            f,p=signal.welch(data[:int(Tcampioni*(i+1)+Tcampioni_finestra/2)],fsampling) #calcolo dello spettro
        else:
            f,p=signal.welch(data[int(Tcampioni*(i+1)-Tcampioni_finestra/2):int(Tcampioni*(i+1)+Tcampioni_finestra/2)],fsampling) #calcolo dello spettro
        fmean=MNF(f,p) #calcolo della frequenza media
        tempo=Tout*(i+1) #tempo corrispondente al calcolo della frequenza media
        time_plot.append(tempo) #inserimento in una lista
        MNF_it.append(fmean)
    return np.asarray(MNF_it),np.asarray(time_plot) #conversione in un array