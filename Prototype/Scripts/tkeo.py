import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter, butter
from scipy.signal import lfilter, peak_widths, peak_prominences
import peakutils

rel_height = 0.8 
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
def treshold_detection(data):
    """
    We can compute the th in two ways: 

    """
    #data = data[treshold_start:treshold_end]
    # data = data[35:85]
    #my implementation of the thresold
    data_np= np.asarray(data)
    rms_data = np.sqrt(np.sum(np.square(data_np))/np.size(data_np)) #rms computation 
    mean_rms= np.mean(rms_data)
    std_rms= np.std(data_np)
    thresholdWeight= 0.25
    mean_rms_threshold= thresholdWeight * mean_rms
    treshold_rms= mean_rms + mean_rms_threshold*std_rms
    #Try this threshold  
    
    data.index = range(0, data.shape[0])
    mean = data.mean()
    std = data.std()
    cost = 4
    treshold = mean + cost*std
    return treshold

#function to compute the peack of a muscle, it's been called inside the class tkeo filtering
def TKEO_processing(data, muscle_to_plot, relative_height, ax):
    """
    returns the filtered signal after TKEO filtering
    
    Args:
        data (array_like): original signal
        muscle_to_plot (list of string): list of muscles for the plotting 
        relative_height(float [0,1]): Chooses the relative height at which the peak width is measured as a percentage of its prominence. 
        1.0 calculates the width of the peak at its lowest contour line while 0.5 evaluates at half the prominence height. Must be at least 0
    Returns:
        peaks_found: list of couple muscle-num_peaks_found 
        left_ips1: 
        right_ips1: 
       
    """
    
    # BUTTER BANDPASS
    data_bandpass = butter_bandpass_filter(data, 20, 499, 1000, 3)
    data_bandpass = pd.DataFrame(data_bandpass, columns=[muscle_to_plot])
    
    # TKEO
    data_TKEO = []
    for i in range (1, len(data_bandpass)-1):
        tkeo_i = pow(data_bandpass[muscle_to_plot][i], 2) - data_bandpass[muscle_to_plot][i-1]*data_bandpass[muscle_to_plot][i+1]
        data_TKEO.append(tkeo_i)

    data_TKEO = pd.DataFrame(data_TKEO, columns=[muscle_to_plot])

    #REMOVING THE BASELINE 
    #baseline= peakutils.baseline(data_TKEO, deg= 2) # deg= Degree of the polynomial that will estimate the envelope.
    #data_TKEO = data_TKEO - baseline #subtracting the baseline
    #plt.plot(data_TKEO)
    #plt.plot(baseline)

    # RECTIFICATION
    data_TKEO = abs(data_TKEO)

    # LOW PASS FILTER 50 Hz 2nd Order
    data_TKEO_filtered = butter_lowpass_filter(data_TKEO, 50, 1000)
    data_TKEO_filtered = pd.DataFrame(data_TKEO_filtered, columns=[muscle_to_plot])

    # MOVING AVERAGE
    data_TKEO_filtered = pd.DataFrame.rolling(data_TKEO_filtered, 500).mean()

    # TRESHOLD
    height_threshold = np.round(treshold_detection(data_TKEO_filtered))
    #print('the threshold for ', muscle_to_plot, ' is equal to: ', height_threshold)

    peaks_found = peakutils.peak.indexes(data_TKEO_filtered[muscle_to_plot], thres_abs=True, thres=int(height_threshold), min_dist=9000)
    average_pf1 = np.mean(data_TKEO_filtered[muscle_to_plot][peaks_found])

    #print('PEAKS FOUND: ', muscle_to_plot, '\t', len(peaks_found))
    # print(df_ErectorSpinaeSx[muscle_to_plot][peaks_found])
    plt.plot(data_TKEO_filtered) #plot the signal
    plt.plot(peaks_found, data_TKEO_filtered[muscle_to_plot][peaks_found], 'x') # highlist the peaks found crossed by x 
    plt.plot(np.full_like(data_TKEO_filtered, height_threshold), "--", color="gray") # plot a line in the y axis to show the threshold level
    plt.title(muscle_to_plot)

    #the peak prominance is the relative peack height, the vertical line that start from.
    #the vertical distance between the peak and its lowest contour line in comparison to the surrounding baseline of the signal. 
    prominences, left_bases, right_bases = peak_prominences(data_TKEO_filtered[muscle_to_plot], peaks_found)
    
    #peak_widths calculates the width of a peak in samples at a relative distance to the peak’s height and prominence.
    widths, h_eval, left_ips1, right_ips1 = peak_widths(data_TKEO_filtered[muscle_to_plot], peaks_found, 
                                                        rel_height=relative_height,
                                                        prominence_data=(prominences, left_bases, right_bases)
    )
   
    # left_ips1, right_ips1: Interpolated positions of left and right intersection points of a horizontal line at the respective evaluation height= rel_height.
    for i in range (0, len(h_eval)):
        plt.hlines(y=h_eval[i], xmin=left_ips1[i], xmax=right_ips1[i], color="blue")
    
    #data_TKEO_filtered.loc[int(left_ips1):int(right_ips1)].at[muscle_to_plot] = np.mean(data_TKEO_filtered[muscle_to_plot])
    for j in range(len(peaks_found)): #if we found some peaks 
        for i in range(int(left_ips1[j]), int(right_ips1[j])):
            data_TKEO_filtered.loc[i].at[muscle_to_plot] = np.mean(data_TKEO_filtered[muscle_to_plot])
    
    data_TKEO_filtered_array= np.asarray(data_TKEO_filtered[muscle_to_plot])
    #print(data_TKEO_filtered_array)
    ax.plot(data_TKEO_filtered)
    #plt.show()
    
    return peaks_found, left_ips1, right_ips1, data_TKEO_filtered_array

################################################################## CLASSE ####################################################################
##################################################################        ####################################################################
##################################################################        ####################################################################
##################################################################        ####################################################################
##################################################################        ####################################################################
class tkeo_filtering:
    """
    This class take in input your RawPower CVS file, it remove the spikes creating a new filtered csv files in the path that you specify.
    Args:
        inputPath (string): export excel path of the rawPower Recording 
        finalPath(string): the path where you want to save the filtered dataframe 
        rel_height(float [0,1]): Chooses the relative height at which the peak width is measured as a percentage of its prominence. 
                                 1.0 calculates the width of the peak at its lowest contour line while 0.5 evaluates at half the prominence height. 
                                 Must be at least 0.
        nColumns_plot(int): number of columns of the final plot
        nRows_plot(int): number of raws of the final plot

    Returns:
        matplotlib plot: the plot with the spikes that will be removed 
        pandas dataframes: the peaks filtered dataframess
    """
    #costructore
    def __init__(self, title, inputPath, finalPath= "", rel_height= 0.80, nColumns_plot = 4, nRows_plot= 2):
        self.title= title
        self.inputPath= inputPath
        self.finalPath= finalPath
        #self.df = pd.read_csv(self.inputPath, delimiter=";") #create the dataframe for the istance 
        self.df= pd.read_excel(io=self.inputPath, sheet_name= "Sheet1", engine= "openpyxl")
        self.rel_height= rel_height
        self.muscles = self.df.columns.values[1:] # get the list of muscles for the specific acquisition, discarding the first 3 columns equal to 'TIMESTAMP', 'STREAM_ID', 'SEQUENCE'
        self.nColumns_plot = nColumns_plot
        self.nRows_plot = nRows_plot
        self.np_df= np.asarray(self.df)
        self.filteredInput= [] 
        self.peaks_found = [] 
        self.left_ips = []   
        self.right_ips = []  
        self.time_start = [] 
        self.time_end = []    
        self.min_len = []
        self.peak_to_be_deleted = []
        self.peak_to_be_deleted2 = []
        self.mini= 0
        self.final_df = {}

    #method to apply a time conversion in the takeo_computation
    def time_conversion(self,array):
        """
        Takes an array and convert each values in a time unit in ms
        Return : array of time converted elements
        """
        time_converted = []
        for ms in array:
            duration = ms
            minutes, seconds = divmod(duration / 1000, 60)
            time = f'{minutes:0>2.0f}:{seconds:.3f}'
            time_converted.append(time)
        return time_converted

    def Tkeo_computation(self):
        
        fig = plt.figure(figsize=(20,10))
        fig.suptitle(self.title, fontsize=15)
        fig.subplots_adjust(hspace=0.5, wspace=0.3)

        for k in range(len(self.muscles)):
            
            ax = fig.add_subplot(self.nRows_plot,self.nColumns_plot, k+1)
            
            peaks_found,left_ips,right_ips,takeoFilteredOutput = TKEO_processing(self.np_df[1:,1+k], self.muscles[k], self.rel_height, ax)
            plt.ylabel('Amplitude')
            plt.xlabel('Time[ms]')
            plt.title(self.muscles[k])
            
            self.peaks_found.append(peaks_found)
            self.left_ips.append(left_ips)
            self.right_ips.append(right_ips)
            self.filteredInput.append(takeoFilteredOutput) # for the final dataframe
        plt.show()
    
        #devi fare i plot dopo, prima calcoli i 7 muscoli e poi fai la plot 
                 
        for i in range(len(self.muscles)):
            #per ogni muscolo aggiungo alla lista min_len il numero di peacks trovati
            self.min_len.append(len(self.peaks_found[i]))
        
        for i in range(len(self.muscles)):
            if self.min_len[i] < 51: #se al muscolo i ho trovato meno di 51 picchi allora aggiungo il numero alla lista picchi da eliminare
                self.peak_to_be_deleted.append(i)
                self.peak_to_be_deleted2.append(i)

        #TOGLIE I PEAK AGGIUNTI A TO_BE_DELATED DA MIN_LEN 
        for i in range(len(self.peak_to_be_deleted)):
            if self.min_len: # check if the list is not empty 
                popped = self.min_len.pop(self.peak_to_be_deleted[i])
                #print('POPPED: ', popped)
                #print('indec ', self.peak_to_be_deleted[i])
                for j in range(i, len(self.peak_to_be_deleted)): # if one peack is popped out of the list I fill the gap moving everything downward 
                    self.peak_to_be_deleted[j] = self.peak_to_be_deleted[j]-1 # shift all the element to fill the gap
        
        if self.min_len: # check if the list is not empty
            self.mini = min(self.min_len)
            if(self.mini > 52): 
                self.mini = 52

        for i in range(len(self.muscles)):
            if not i in self.peak_to_be_deleted2:
                self.peaks_found[i] = self.peaks_found[i][0:self.mini]
                self.left_ips[i] = self.left_ips[i][0:self.mini]
                self.right_ips[i] = self.right_ips[i][0:self.mini]

        
        for i in range(len(self.left_ips)):
          self.left_ips[i] = np.round(np.asarray(self.left_ips[i]))
          #self.left_ips.append(np.round(self.left_ips[i]))
        
        for i in range(len(self.right_ips)):
           self.right_ips[i] = np.round(np.asarray(self.right_ips[i]))
           #self.right_ips.append(np.round(self.right_ips[i]))

        for i in range(len(self.left_ips)):
           self.time_start.append(self.time_conversion(self.left_ips[i]))

        for i in range(len(self.right_ips)):
           #self.time_end[i] = self.time_conversion(self.right_ips[i])
           self.time_end.append(self.time_conversion(self.right_ips[i]))
        
        for i in range(len(self.muscles)):
            if not i in self.peak_to_be_deleted2:
                print('sono dentro il if not i in peak_to_be_deleted2')
                self.final_df[self.muscles[i]] = self.left_ips[i]
                self.final_df[self.muscles[i]] = self.right_ips[i]
            
        
        
        self.final_df= pd.DataFrame(np.asarray(self.filteredInput).T, columns= self.muscles)
        
        """
        DA SISTEMARE:  IL WRITE EXCEL DEL FINAL DATAFRAME 
        non usa la parte del time_conversation per ora
        """
        #self.final_df.to_excel(self.finalPath, engine= "openpyxl")
        #self.final_df.to_csv(self.finalPath)
        return self.final_df
##allora sei arrivato a n_rows e NColumns devi capire come iterare tra le righe e le colonne 
    
###Class testing 

arpeggio_path =  "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\1 Arpeggio\Arpeggio_rms_exp.xlsx"
strumming_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\2 Strumming\Strumming_rms_exp.xlsx"
bending_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\3 Bending\Bending_rms_exp.xlsx"
pullOffHammerOn_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\4 PullOffHammerOn\PullOffHammerOn_rms_exp.xlsx"
tapping_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\5 Tapping\\tapping_rms_exp.xlsx"
strongPick_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\6 StrongPick\\strongPick_rms_exp.xlsx"
doublePick_path = "C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\GItDesktop\MAE_Thesis\\firstPrototype\secondAcquisition\\7 DoublePick\\doublePick_rms_exp.xlsx"

arpeggio = tkeo_filtering(title= "Arpeggio", inputPath="C:\\Users\david\OneDrive - Politecnico di Milano\Documenti\Recordings\Davide_Lionetti\\1 Arpeggio_20230222_140600\\Arpeggio_exp.xlsx")   
arpeggioFinalDataframe= arpeggio.Tkeo_computation()

strumming=tkeo_filtering(title= "Strumming", inputPath= strumming_path)
strummingFilteredDataFrame= strumming.Tkeo_computation()

bending=tkeo_filtering(title= "Bending", inputPath= bending_path)
bendingFilteredDataFrame= bending.Tkeo_computation()

pullOffHammerOn=tkeo_filtering(title= "pullOffHammerOn", inputPath= pullOffHammerOn_path)
pullOffHammerOnFilteredDataFrame= pullOffHammerOn.Tkeo_computation()

tapping=tkeo_filtering(title= "tapping", inputPath= tapping_path)
tappingFilteredDataFrame= tapping.Tkeo_computation()

strongPick=tkeo_filtering(title= "strongPick", inputPath= strongPick_path)
strongPickFilteredDataFrame= strongPick.Tkeo_computation()

doublePick=tkeo_filtering(title= "doublePick", inputPath= doublePick_path)
doublePickFilteredDataFrame= doublePick.Tkeo_computation()

#strumming= tkao_filtering( title= "Strumming", input)
#print(finalDataframe)