#funzioni di preprocessing segnale EMG
import numpy as np
import pandas as pd
from scipy.signal import butter
from scipy.signal import lfilter
from scipy.signal import iirfilter
from sklearn.preprocessing import MinMaxScaler


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
    n=int(nyq/freq)-1 #number of armonics
    for i in range(n): #n harmonics
        low  = freq*(i+1)- band/2.0
        high = freq*(i+1) + band/2.0
        low  = low/nyq
        high = high/nyq
        b, a = iirfilter(order, [low, high], rp=ripple, btype='bandstop',
                        analog=False, ftype=filter_type)
        filtered_data = lfilter(b, a, filtered_data)
    return filtered_data
def RNN_input_preprocessing(raw_dataframe, fs= 1000): 
    '''
    Shaping the data before feddding them into the RNN model for real time prediction. It applies a bandpass and a Notch filter, then a window rms, scales from (0,1) and adjust the shape. 
    Args:
        raw_dataframe(Pandas dataframe): the pd dataframe containing the sEMG raw data collected by the board in real time. 
        fs(int): Sample rate
    '''

    #Defining the band pass parameters and the windows size
    lowcut = 30.0 #inizializzazione frequenza taglia basso
    highcut = 300.0  #inizializzazione frequenza taglia alto (verrà comunque detrminata automaticamente all'apertura del file EMG)
    order=5 #ordine del filtro di butterworth
    rms_window_size=125 #numero di campioni su cui effettuare la convoluzione per il calcolo del RMS

    #CALCOLO DF SEGNALI FILTRATI
    #casting to int before applying the bandpas, othetwise it rainses ad exeption
    #for i in range(len(raw_dataframe.columns[:-1])):
    #   raw_dataframe[raw_dataframe.columns[i]] = raw_dataframe[raw_dataframe.columns[i]].astype('int64')

    
    #applicazione filtro passa panda e di notch su ogni colonna (canale) del dataframe Raw
    #raw_dataframe= raw_dataframe.fillna(0).astype(int)
    #now we apply the notch filter feeding it with the prefiltered bandapassed stream 
    df_Emg_Filtered= raw_dataframe.apply(lambda x: Implement_Notch_Filter(fs,1,50, None, 3, 'butter', 
                                        butter_bandpass_filter(x,lowcut,highcut, fs, order=order)))

    
    #CALCOLO DF SEGNALI RMS
    def df_rms(vect):
        rect=abs(vect.fillna(0).values)
        for i in range(25):
            rect[i]=int(1)
        return window_rms(rect,rms_window_size)

    #applicazione della funzione df_rms su ogni colonna (canale) del dataframe contente i segnali filtrati
    #apply the RMS to the band passed dataframe
    df_RMS= df_Emg_Filtered.apply(lambda x: df_rms(x))
    df_RMS= df_RMS.round(2)                                                                                                                                                                                                                                                                                                                                                     

    
    #tempo del segnale rms è uguale a quello emg solo tagliato all'inizio e alla fine per via della convoluzione 'valid'
    #il primo campione del RMS è stato assegnato a metà della prima finestra
    #tempo_rms= raw_dataframe['TIMESTAMP'][int(rms_window_size/2):-int(rms_window_size/2)+1] 
    
    print('df_RMS with initial shape ', df_RMS.shape) # '\n', df_RMS, '\n', type(df_RMS))

    #scaling the dataset 
    #raw_dataframe= scaler.fit_transform(raw_dataframe) # it return an np array 
    #df_RMS= df_RMS.values

    #print('the shape of the df array: ', df_RMS.shape)
    #scaling the value from (0,1)
    scaler = MinMaxScaler()
    df_RMS= scaler.fit_transform(df_RMS)

    #df_RMS[i]= df_RMS[i].values

    sequence_length = 32
    # Print the shape of the raw data before reshaping
    #print("Raw Data Shape:", df_RMS.shape[0])

    # Calculate the number of groups
    num_groups = df_RMS.shape[0] // sequence_length
    # Print the number of groups
    #print("Number of Groups:", num_groups)
    
    casting_index= num_groups * sequence_length
    # Calculate the number of remaining elements
    #num_remaining = df_RMS[i].shape[0] % sequence_length
    
    # Reshape the input data into a 3D matrix
    input_sequences = np.reshape(df_RMS[:casting_index], (num_groups, sequence_length, df_RMS.shape[1]))
    df_RMS = input_sequences     


    # The shape of 'input_sequences' will be (num_groups + 1, sequence_length, num_features)
    print('The final shape:' , df_RMS.shape)

    return df_RMS

def RNN_input_preprocessing_csv(raw_csv_path, fs= 1000): 
    '''
    Shaping the data before feddding them into the RNN model for real time prediction. It applies a bandpass and a Notch filter, then a window rms, scales from (0,1) and adjust the shape. 
    Args:
        raw_dataframe(Pandas dataframe): the pd dataframe containing the sEMG raw data collected by the board in real time. 
        fs(int): Sample rate
    '''
    raw_dataframe= pd.read_csv(raw_csv_path, sep= ';')
    #Defining the band pass parameters and the windows size
    lowcut = 30.0 #inizializzazione frequenza taglia basso
    highcut = 300.0  #inizializzazione frequenza taglia alto (verrà comunque detrminata automaticamente all'apertura del file EMG)
    order=5 #ordine del filtro di butterworth
    rms_window_size=125 #numero di campioni su cui effettuare la convoluzione per il calcolo del RMS

    #CALCOLO DF SEGNALI FILTRATI
    #casting to int before applying the bandpas, othetwise it rainses ad exeption
    #for i in range(len(raw_dataframe.columns[:-1])):
    #   raw_dataframe[raw_dataframe.columns[i]] = raw_dataframe[raw_dataframe.columns[i]].astype('int64')

    
    #applicazione filtro passa panda e di notch su ogni colonna (canale) del dataframe Raw
    #raw_dataframe= raw_dataframe.fillna(0).astype(int)
    #now we apply the notch filter feeding it with the prefiltered bandapassed stream 
    df_Emg_Filtered= raw_dataframe.apply(lambda x: Implement_Notch_Filter(fs,1,50, None, 3, 'butter', 
                                        butter_bandpass_filter(x,lowcut,highcut, fs, order=order)))

    
    #CALCOLO DF SEGNALI RMS
    def df_rms(vect):
        rect=abs(vect.fillna(0).values)
        for i in range(25):
            rect[i]=int(1)
        return window_rms(rect,rms_window_size)

    #applicazione della funzione df_rms su ogni colonna (canale) del dataframe contente i segnali filtrati
    #apply the RMS to the band passed dataframe
    df_RMS= df_Emg_Filtered.apply(lambda x: df_rms(x))
    df_RMS= df_RMS.round(2)                                                                                                                                                                                                                                                                                                                                                     

    
    #tempo del segnale rms è uguale a quello emg solo tagliato all'inizio e alla fine per via della convoluzione 'valid'
    #il primo campione del RMS è stato assegnato a metà della prima finestra
    #tempo_rms= raw_dataframe['TIMESTAMP'][int(rms_window_size/2):-int(rms_window_size/2)+1] 
    
    print('df_RMS with initial shape ', df_RMS.shape) # '\n', df_RMS, '\n', type(df_RMS))

    #scaling the dataset 
    #raw_dataframe= scaler.fit_transform(raw_dataframe) # it return an np array 
    #df_RMS= df_RMS.values

    #print('the shape of the df array: ', df_RMS.shape)
    #scaling the value from (0,1)
    scaler = MinMaxScaler()
    df_RMS= scaler.fit_transform(df_RMS)

    #df_RMS[i]= df_RMS[i].values

    sequence_length = 32
    # Print the shape of the raw data before reshaping
    #print("Raw Data Shape:", df_RMS.shape[0])

    # Calculate the number of groups
    num_groups = df_RMS.shape[0] // sequence_length
    # Print the number of groups
    #print("Number of Groups:", num_groups)
    
    casting_index= num_groups * sequence_length
    # Calculate the number of remaining elements
    #num_remaining = df_RMS[i].shape[0] % sequence_length
    
    # Reshape the input data into a 3D matrix
    input_sequences = np.reshape(df_RMS[:casting_index], (num_groups, sequence_length, df_RMS.shape[1]))
    df_RMS = input_sequences     


    # The shape of 'input_sequences' will be (num_groups + 1, sequence_length, num_features)
    print('The final shape:' , df_RMS.shape)

    return df_RMS