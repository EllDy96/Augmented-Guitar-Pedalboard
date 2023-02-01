#funzioni di preprocessing segnale EMG
from scipy.signal.filter_design import butter
from scipy.signal import lfilter
from scipy.signal import iirfilter

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