#import openpyxl
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import librosa, librosa.display
import scipy 
from scipy.io import wavfile
import IPython.display as ipd
import os
from PyQt5.QtGui import QWidget 

file = "C:\\Users\david\OneDrive - Politecnico di Milano\Il_mio_mondo\Corsi Università\Magistrale\Tesi\LWT3\\firstPrototype\Abs_Test_rms.xlsx"
#folder = "C:\\Users\TestManager\Desktop\Test_Roberto\KLAAS_DEVOS\Abs_Audio.wav"
sheet = "Sheet1"
df = pd.read_excel(io=file, sheet_name=sheet)
#print("df type = {}".format(type(df)))
#print("df = \n{}".format(df.head(10)))
npdf = np.asarray(df)
print("npdf = \n{}".format(npdf[1:20, 1:10]))
sr=1000  # Hz

print("shape npdf = {}".format(np.shape(npdf)))
signal_bicep_Dx = npdf.T[1, 1:]
#np.save(folder, signal_bicep_Dx)
#signal_bicep_Dx = wavefile.read(folder)
#signal_bicep_Dx = wav.read(folder)
#signal_bicep_Dx = wavfile.read(folder)
#signal_bicep_Dx = librosa.load(folder, sr=sr)
s_lenght = signal_bicep_Dx.shape[0]
s_duration = (1/sr)*s_lenght
s_instants = np.arange(0, s_lenght)*1/sr


print("Original Duration: {} seconds".format(s_duration))
plt.figure(figsize=(10,6))
plt.plot(s_instants, signal_bicep_Dx)
#plt.autoscale(enable=True, axis='x', tight=True)
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')


ipd.Audio(signal_bicep_Dx, rate = sr)


NFFT = 512
frame_length = NFFT
hop_length = frame_length / 2


print("signal type = {}".format(type(signal_bicep_Dx[0])))
#X = librosa.stft(signal_bicep_Dx, n_fft=NFFT, hop_length=hop_length, win_length=frame_length, window='hamming', center=False)
#Xmag = np.abs(X)
#XdB = librosa.amplitude_to_db(Xmag)
#librosa.display.specshow(Xmag, sr=sr,hop_length=hop_length,x_axis='time', y_axis='linear', cmap='viridis')
#plt.colorbar()
#plt.title('Spectrogram [Amplitude]')




#xlsx = Path('C:\Users\TestManager\Desktop\Test_Roberto\KLAAS_DEVOS\Abs_Test.xlsx')