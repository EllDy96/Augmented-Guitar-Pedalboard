import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, freqz
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks
from scipy.signal.filter_design import butter
from scipy.signal import lfilter, peak_widths, peak_prominences
from scipy.signal import iirfilter
import peakutils

# PERCORSO FILE EMG
#path = "\\Users\TestManager\Desktop\python files cashier\Des_Por\REC_COM3_20220502_120941emg.csv"   # 14927-1000: CAMPIONI DA SCARARE
#path = '\\Users\TestManager\Desktop\python files cashier\Lusien_Bardhi\REC_COM3_20220502_160342emg.csv'   #14102-1000
#path = '\\Users\TestManager\Desktop\python files cashier\Andrea_Randone\REC_COM3_20220504_111203emg.csv'    # 16435-1000
# path = '\\Users\TestManager\Desktop\python files cashier\Cecilia_Raho\REC_COM3_20220526_131940emg.csv'
#path = '\\Users\TestManager\Desktop\python files cashier\Federico_Spinelli\REC_COM3_20220509_160454emg.csv' # 9518-1000
# path = '\\Users\TestManager\Desktop\python files cashier\Margherita_La_Gamba\REC_COM3_20220426_124921emg.csv'   # 17434-1000
# path = '\\Users\TestManager\Desktop\python files cashier\Angela_Viscione\REC_COM3_20220512_112426emg.csv'  # 11018-1000
# path = '\\Users\TestManager\Desktop\python files cashier\Alessandro_Deponti\REC_COM3_20220503_125154emg.csv'    # 18860-2000
#path = '\\Users\TestManager\Desktop\python files cashier\Chiara_Montrasio\REC_COM3_20220513_122830emg.csv'  # 13685-2000
path = '\\Users\TestManager\Desktop\python files cashier\Tania_Brusati\REC_COM3_20220406_114747emg.csv' # 10501 - 1000

df = pd.read_csv(path, delimiter=";")

dove_salvare = '\\Users\TestManager\Desktop\python files cashier\Tania_Brusati\muscles_activity_TKEO.csv'
campioni_da_scartare=   10501 - 1000 # artefatti del filtro interno alla scheda, dobbiamo togliere il primo secondo di samples [1000 samples]
treshold_start = 178000 # no sono sample del segnale, non so perchè ma sono samples
treshold_end = 182000   #

rel_height = 0.96 # cosa è?

# FILTRI
def butter_bandpass(lowcut, highcut, fs, order):
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

def butter_bandpass_filter(data, lowcut, highcut, fs, order):
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
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    y = lfilter(b, a, data)
    return y

def butter_lowpass(cutoff, fs, order=2):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=2):
    b, a = butter_lowpass(cutoff, fs, order=2)
    y = lfilter(b, a, data)
    return y


fig, axs = plt.subplots(4,2, sharex=True)

def TKEO_processing(data, muscle_to_plot, relative_height, i_plot, j_plot):

    data=data[campioni_da_scartare:len(data)-campioni_da_scartare]
    data.index = range(0, data.shape[0])

    # BUTTER BANDPASS
    data_bandpass = butter_bandpass_filter(data, 20, 499, 1000, 3)
    data_bandpass = pd.DataFrame(data_bandpass, columns=[muscle_to_plot])
    
    # TKEO
    data_TKEO = []
    for i in range (1, len(data_bandpass)-1):
        tkeo_i = pow(data_bandpass[muscle_to_plot][i], 2) - data_bandpass[muscle_to_plot][i-1]*data_bandpass[muscle_to_plot][i+1]
        data_TKEO.append(tkeo_i)

    data_TKEO = pd.DataFrame(data_TKEO, columns=[muscle_to_plot])
    # RECTIFICATION
    data_TKEO = abs(data_TKEO)

    # LOW PASS FILTER 50 Hz 2nd Order
    data_TKEO_filtered = butter_lowpass_filter(data_TKEO, 50, 1000)
    data_TKEO_filtered = pd.DataFrame(data_TKEO_filtered, columns=[muscle_to_plot])

    # MOVING AVERAGE
    data_TKEO_filtered = pd.DataFrame.rolling(data_TKEO_filtered, 500).mean()

    # TRESHOLD
    height_threshold = np.round(treshold_detection(data_TKEO_filtered))

    peaks_found = peakutils.peak.indexes(data_TKEO_filtered[muscle_to_plot], thres_abs=True, thres=int(height_threshold), min_dist=9000)
    average_pf1 = np.mean(data_TKEO_filtered[muscle_to_plot][peaks_found])

    print('PEAKS FOUND: ', muscle_to_plot, '\t', len(peaks_found))
    # print(df_ErectorSpinaeSx[muscle_to_plot][peaks_found])
    axs[i_plot, j_plot].plot(data_TKEO_filtered[muscle_to_plot])
    axs[i_plot, j_plot].plot(peaks_found, data_TKEO_filtered[muscle_to_plot][peaks_found], 'x')
    axs[i_plot, j_plot].plot(np.full_like(data_TKEO_filtered, height_threshold), "--", color="gray")
    axs[i_plot, j_plot].set_title(muscle_to_plot)

    prominences, left_bases, right_bases = peak_prominences(data_TKEO_filtered[muscle_to_plot], peaks_found)
    widths, h_eval, left_ips1, right_ips1 = peak_widths(
        data_TKEO_filtered[muscle_to_plot], peaks_found, 
        rel_height=relative_height,
        prominence_data=(prominences, left_bases, right_bases)
    )
    for i in range (0, len(h_eval)):
        axs[i_plot, j_plot].hlines(y=h_eval[i], xmin=left_ips1[i], xmax=right_ips1[i], color="blue")

    

    axs[i_plot, j_plot].plot(data_TKEO_filtered)
    return peaks_found, left_ips1, right_ips1

def treshold_detection(data):
    data = data[treshold_start:treshold_end]
    # data = data[35:85]
    data.index = range(0, data.shape[0])
    mean = data.mean()
    std = data.std()
    cost = 6
    treshold = mean + cost*std
    return treshold

df_ErectorSpinaeSx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
    ' Infraspinatus  Sx ', ' Upper  Trapezius  Sx ',
    ' Latissimus  Dorsi  Sx ', ' Upper  Trapezius  Dx ',
    ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
    ' Erector  Spinae  Dx ', 'LAP'], axis=1)
peaks_found_1, left_ips1, right_ips1 = TKEO_processing(df_ErectorSpinaeSx, ' Erector  Spinae  Sx ', rel_height, 0, 0)

df_UpperTrapeziusSx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Infraspinatus  Sx ', ' Erector  Spinae  Sx ',
       ' Latissimus  Dorsi  Sx ', ' Upper  Trapezius  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
       ' Erector  Spinae  Dx ', 'LAP'], axis=1)
peaks_found_2, left_ips2, right_ips2 = TKEO_processing(df_UpperTrapeziusSx, ' Upper  Trapezius  Sx ', rel_height, 1, 0)

df_LatissimusDorsiSx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Infraspinatus  Sx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Upper  Trapezius  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
       ' Erector  Spinae  Dx ', 'LAP'], axis=1)
peaks_found_3, left_ips3, right_ips3 = TKEO_processing(df_LatissimusDorsiSx, ' Latissimus  Dorsi  Sx ', rel_height, 2, 0)

df_InfraspinatusSx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Latissimus  Dorsi  Sx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Upper  Trapezius  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
       ' Erector  Spinae  Dx ', 'LAP'], axis=1)
peaks_found_4, left_ips4, right_ips4 = TKEO_processing(df_InfraspinatusSx, ' Infraspinatus  Sx ', 0.93, 3, 0)

df_ErectorSpinaeDx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Latissimus  Dorsi  Sx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Upper  Trapezius  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
       ' Infraspinatus  Sx ', 'LAP'], axis=1)
peaks_found_5, left_ips5, right_ips5 = TKEO_processing(df_ErectorSpinaeDx, ' Erector  Spinae  Dx ', rel_height, 0, 1)

df_UpperTrapeziusDx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Latissimus  Dorsi  Sx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Erector  Spinae  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Dx ',
       ' Infraspinatus  Sx ', 'LAP'], axis=1)
peaks_found_6, left_ips6, right_ips6 = TKEO_processing(df_UpperTrapeziusDx, ' Upper  Trapezius  Dx ', rel_height, 1, 1)

df_LatissimusDorsiDx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Upper  Trapezius  Dx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Erector  Spinae  Dx ',
       ' Infraspinatus  Dx ', ' Latissimus  Dorsi  Sx ',
       ' Infraspinatus  Sx ', 'LAP'], axis=1)
peaks_found_7, left_ips7, right_ips7 = TKEO_processing(df_LatissimusDorsiDx, ' Latissimus  Dorsi  Dx ', rel_height, 2, 1)

df_InfraspinatusDx = df.drop(['TIMESTAMP', 'STREAM_ID', 'SEQUENCE',
       ' Upper  Trapezius  Dx ', ' Erector  Spinae  Sx ',
       ' Upper  Trapezius  Sx ', ' Erector  Spinae  Dx ',
       ' Latissimus  Dorsi  Dx ', ' Latissimus  Dorsi  Sx ',
       ' Infraspinatus  Sx ', 'LAP'], axis=1)
peaks_found_8, left_ips8, right_ips8 = TKEO_processing(df_InfraspinatusDx, ' Infraspinatus  Dx ', 0.90, 3, 1)

plt.show()

min_len = []

min_len.append(len(peaks_found_1))
min_len.append(len(peaks_found_2))
min_len.append(len(peaks_found_3))
min_len.append(len(peaks_found_4))
min_len.append(len(peaks_found_5))
min_len.append(len(peaks_found_6))
min_len.append(len(peaks_found_7))
min_len.append(len(peaks_found_8))

to_be_deleted = []
to_be_deleted2 = []

for i in range(0, 7):
    if min_len[i] < 51:
        to_be_deleted.append(i)
        to_be_deleted2.append(i)

for i in range(0, len(to_be_deleted)):
    popped = min_len.pop(to_be_deleted[i])
    print('POPPED: ', popped)
    print('indec ', to_be_deleted[i])
    for j in range(i, len(to_be_deleted)):
        to_be_deleted[j] = to_be_deleted[j]-1
print(min_len)
print(to_be_deleted)
print(to_be_deleted)
print(to_be_deleted2)
mini = min(min_len)

if(mini > 52):
    mini = 52

if not 0 in to_be_deleted2:
    peaks_found_1 = peaks_found_1[0:mini]
    left_ips1 = left_ips1[0:mini]
    right_ips1 = right_ips1[0:mini]

if not 1 in to_be_deleted2:    
    peaks_found_2 = peaks_found_2[0:mini]
    left_ips2 = left_ips2[0:mini]
    right_ips2 = right_ips2[0:mini]

if not 2 in to_be_deleted2:    
    peaks_found_3 = peaks_found_3[0:mini]
    left_ips3 = left_ips3[0:mini]
    right_ips3 = right_ips3[0:mini]

if not 3 in to_be_deleted2:
    peaks_found_4 = peaks_found_4[0:mini]
    left_ips4 = left_ips4[0:mini]
    right_ips4 = right_ips4[0:mini]

if not 4 in to_be_deleted2:
    peaks_found_5 = peaks_found_5[0:mini]
    left_ips5 = left_ips5[0:mini]
    right_ips5 = right_ips5[0:mini]

if not 5 in to_be_deleted2:
    peaks_found_6 = peaks_found_6[0:mini]
    left_ips6 = left_ips6[0:mini]
    right_ips6 = right_ips6[0:mini]

if not 6 in to_be_deleted2:
    peaks_found_7 = peaks_found_7[0:mini]
    left_ips7 = left_ips7[0:mini]
    right_ips7 = right_ips7[0:mini]

if not 7 in to_be_deleted2:
    peaks_found_8 = peaks_found_8[0:mini]
    left_ips8 = left_ips8[0:mini]
    right_ips8 = right_ips8[0:mini]

left_ips1 = np.round(left_ips1)
left_ips2 = np.round(left_ips2)
left_ips3 = np.round(left_ips3)
left_ips4 = np.round(left_ips4)
left_ips5 = np.round(left_ips5)
left_ips6 = np.round(left_ips6)
left_ips7 = np.round(left_ips7)
left_ips8 = np.round(left_ips8)

right_ips1 = np.round(right_ips1)
right_ips2 = np.round(right_ips2)
right_ips3 = np.round(right_ips3)
right_ips4 = np.round(right_ips4)
right_ips5 = np.round(right_ips5)
right_ips6 = np.round(right_ips6)
right_ips7 = np.round(right_ips7)
right_ips8 = np.round(right_ips8)


time_converted = []
def time_conversion(array):
    for ms in left_ips1:
       duration = ms
       minutes, seconds = divmod(duration / 1000, 60)
       time = f'{minutes:0>2.0f}:{seconds:.3f}'
       time_converted.append(time)
    return time_converted

time_start1 = time_conversion(left_ips1)
time_end1 = time_conversion(right_ips1)

time_start2 = time_conversion(left_ips1)
time_end2 = time_conversion(right_ips2)

time_start3 = time_conversion(left_ips3)
time_end3 = time_conversion(right_ips3)

time_start4 = time_conversion(left_ips4)
time_end4 = time_conversion(right_ips4)

time_start5 = time_conversion(left_ips5)
time_end5 = time_conversion(right_ips5)

time_start6 = time_conversion(left_ips6)
time_end6 = time_conversion(right_ips6)

time_start7 = time_conversion(left_ips7)
time_end7 = time_conversion(right_ips7)

time_start8 = time_conversion(left_ips8)
time_end8 = time_conversion(right_ips8)

final_df = {}

if not 0 in to_be_deleted2:
    final_df['Erector_Spinae_Sx_LEFT'] = left_ips1
    final_df['Erector_Spinae_Sx_RIGHT'] = right_ips1

if not 1 in to_be_deleted2:    
    final_df['Upper_Trapezius_Sx_LEFT'] = left_ips2
    final_df['Upper_Trapezius_Sx_RIGHT'] = right_ips2

if not 2 in to_be_deleted2:    
    final_df['Latissimus_Dorsi_Sx_LEFT'] = left_ips3
    final_df['Latissimus_Dorsi_Sx_RIGHT'] = right_ips3

if not 3 in to_be_deleted2:
    final_df['Infraspinatus_Sx_LEFT'] = left_ips4
    final_df['Infraspinatus_Sx_RIGHT'] = right_ips4

if not 4 in to_be_deleted2:
    final_df['Erector_Spinae_Dx_LEFT'] = left_ips5
    final_df['Erector_Spinae_Dx_RIGHT'] = right_ips5

if not 5 in to_be_deleted2:
    final_df['Upper_Trapezius_Dx_LEFT'] = left_ips6
    final_df['Upper_Trapezius_Dx_RIGHT'] = right_ips6    

if not 6 in to_be_deleted2:
    final_df['Latissimus_Dorsi_Dx_LEFT'] = left_ips7
    final_df['Latissimus_Dorsi_Dx_RIGHT'] = right_ips7

if not 7 in to_be_deleted2:
    final_df['Infraspinatus_Dx_LEFT'] = left_ips8
    final_df['Infraspinatus_Dx_RIGHT'] = right_ips8


#SCRIVO IL DATAFRAME
# final_df = pd.DataFrame({'Erector_Spinae_Sx_LEFT':left_ips1, 'Erector_Spinae_Sx_RIGHT':right_ips1, 'Upper_Trapezius_Sx_LEFT':left_ips2, 'Upper_Trapezius_Sx_RIGHT':right_ips2, 'Latissimus_Dorsi_Sx_LEFT':left_ips3, 'Latissimus_Dorsi_Sx_RIGHT':right_ips3, 'Infraspinatus_Sx_LEFT':left_ips4, 'Infraspinatus_Sx_RIGHT':right_ips4,
#                         'Erector_Spinae_Dx_LEFT':left_ips5, 'Erector_Spinae_Dx_RIGHT':right_ips5, 'Upper_Trapezius_Dx_LEFT':left_ips6, 'Upper_Trapezius_Dx_RIGHT':right_ips6, 'Latissimus_Dorsi_Dx_LEFT':left_ips7, 'Latissimus_Dorsi_Dx_RIGHT':right_ips7, 'Infraspinatus_Dx_LEFT':left_ips8, 'Infraspinatus_Dx_RIGHT':right_ips8})
final_df = pd.DataFrame(final_df)
#final_df.to_csv(dove_salvare)
# final_time_df = pd.DataFrame({'Erector_Spinae_Sx_LEFT':time_start1, 'Erector_Spinae_Sx_RIGHT':time_end1, 'Upper_Trapezius_Sx_LEFT':time_start2, 'Upper_Trapezius_Sx_RIGHT':time_end2, 'Latissimus_Dorsi_Sx_LEFT':time_start3, 'Latissimus_Dorsi_Sx_RIGHT':time_end3, 'Infraspinatus_Sx_LEFT':time_start4, 'Infraspinatus_Sx_RIGHT':time_end4,
#                         'Erector_Spinae_Dx_LEFT':time_start5, 'Erector_Spinae_Dx_RIGHT':time_end5, 'Upper_Trapezius_Dx_LEFT':time_start6, 'Upper_Trapezius_Dx_RIGHT':time_end6, 'Latissimus_Dorsi_Dx_LEFT':time_start7, 'Latissimus_Dorsi_Dx_RIGHT':time_end7, 'Infraspinatus_Dx_LEFT':time_start8, 'Infraspinatus_Dx_RIGHT':time_end8})
# final_time_df.to_csv('/Users/davidezmg/Personal/LWT3/sync DESIREE PORCEDDU/muscles_activity_time_TKEO.csv')

