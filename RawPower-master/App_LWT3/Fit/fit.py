#modulo contenente la funzione per aprire i file .fit
import numpy as np
import pandas as pd
#from fitparse import FitFile
import datetime

def open_fit(filename,fs_fit):
    """
    opens a .Fit file and returns a dataframe containing cadence, power and heart rate

    Args:
        filename(path): path of the .fit file
        fs_fit(float): sampling frequency

    Returns: 
        Dataframe: Dataframe representing the .fit values
    """

    def nan_helper(y):
        """Helper to handle indices and logical indices of NaNs.

        Input:
            - y, 1d numpy array with possible NaNs
        Output:
            - nans, logical indices of NaNs
            - index, a function, with signature indices= index(logical_indices),
            to convert logical indices of NaNs to 'equivalent' indices
        Example:
            >>> # linear interpolation of NaNs
            >>> nans, x= nan_helper(y)
            >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
        """

        return np.isnan(y), lambda z: z.nonzero()[0]

    fitfile = FitFile(filename)
    fitfile.parse()
    records = list(fitfile.get_messages(name='record'))
    cadenza=[]
    heart_rate=[]
    power=[]
    tempo=[]
    i=0
    j=0
    k=0
    z=0
    t=0

    for record in records:
        for field in record:
            if field.name=='cadence':
                cadenza.append(field.value)
                j=j+1 #number of cadence values
            if field.name=='heart_rate':
                heart_rate.append(field.value)
                k=k+1 #number of HR values
            if field.name=='power':
                power.append(field.value)
                z=z+1 #number of power values
            if field.name=='timestamp':
                tempo.append(field.value)
                t=t+1 #number of time values

        #append NaN value where there is not a value
        i=i+1 #number of records
        if(i>j): #if a value of cadence is lost, NaN value is added to mantain the signals synchronous
            cadenza.append(np.nan)
            j=j+1
        if(i>k): #if a value of HR is lost, NaN value is added to mantain the signals synchronous
            heart_rate.append(np.nan)
            k=k+1
        if(i>z): #if a value of power is lost, NaN value is added to mantain the signals synchronous
            power.append(np.nan)
            z=z+1
        if(i>t):
            tempo.append(np.nan) #if a value of time is lost, NaN value is added to mantain the signals synchronous
            t=t+1

    cadenza=np.asarray(cadenza)
    heart_rate=np.asarray(heart_rate)
    power=np.asarray(power)
    tempo=np.asarray(tempo)

    #linear interpolation where NaN are present
    nans, x= nan_helper(cadenza)
    cadenza[nans]= np.interp(x(nans), x(~nans), cadenza[~nans])
    try:
        nans, x= nan_helper(heart_rate)
        heart_rate[nans]= np.interp(x(nans), x(~nans), heart_rate[~nans])
    except:
        print('Heart Rate not present')
    nans, x= nan_helper(power)
    power[nans]= np.interp(x(nans), x(~nans), power[~nans])
    
    #creo un arry temporale per il file .Fit
    timestamp_fit=[]
    for sample in range(len(cadenza)): 
        seconds = sample * fs_fit #moltiplico il campione per la frequenza di campionamento del file .fit
        microseconds=(seconds*1000000) % 1000000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60 // 1
        timestamp_fit.append(datetime.time(hour=int(hours),minute=int(minutes),second=int(seconds),microsecond=int(microseconds)))

    d={'cadence': cadenza, 'HeartRateBpm': heart_rate, 'power': power}
    
    #creazione di un dataframe
    Df_fit=pd.DataFrame(data=d,index=timestamp_fit) 
    
    return Df_fit