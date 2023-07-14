
import scipy as sp 
from scipy import signal
#from signal import butter
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from pathlib import Path
#import librosa
import sklearn
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
from PreProcessing.processing import *
#from Regr_model_test.ipynb import input_preprocessing



test_pd_Dataframe= pd.read_csv('firstPrototype\\thirdAcquisition\\1 Arpeggio\\arpeggio_teso\REC_COM8_20230608_181607emg.csv', sep= ';')
test_pd_Dataframe = test_pd_Dataframe.iloc[:,3:]
print(test_pd_Dataframe.isna().sum().sum(), test_pd_Dataframe.shape, test_pd_Dataframe.size )
print(test_pd_Dataframe)
#print([pd_dataframe_relaxed[i].isna().sum().sum() for i in pd_dataframe_relaxed], [pd_dataframe_relaxed[i].size for i in pd_dataframe_relaxed])
test_pd_Dataframe_1= pd.read_csv('firstPrototype\secondAcquisition\\3 Bending\\bending.csv', sep= ';')
test_pd_Dataframe_1 = test_pd_Dataframe_1.iloc[:,3:]
print(test_pd_Dataframe_1.isna().sum().sum(), test_pd_Dataframe_1.shape)
"""
model = load_model('firstPrototype\Scripts\keras_model\sEMG_binary_classifier.h5')

random_data = {
    'g00': np.random.uniform(low=-10000, high=10000, size=500),
    'g01': np.random.uniform(low=-10000, high=10000, size=500),
    'g02': np.random.uniform(low=-10000, high=10000, size=500),
    'g03': np.random.uniform(low=-10000, high=10000, size=500),
    'g10': np.random.uniform(low=-10000, high=10000, size=500),
    'g11': np.random.uniform(low=-10000, high=10000, size=500),
    'g12': np.random.uniform(low=-10000, high=10000, size=500),
    'g13': np.random.uniform(low=-10000, high=10000, size=500)
}

df_toLSTM_1= pd.DataFrame(random_data)

df_toLSTM_1_preprocessed = RNN_input_preprocessing(df_toLSTM_1)
prediction = model.predict(df_toLSTM_1_preprocessed)
prediction = np.rint(prediction.T).tolist()
#after predicting the new data i print the result 
print(type(prediction))

#argmax is used for multiclass model, to identify the index of the class with maximum likelihood, in this case the output is of shape 1, if the nuber i close to zero then the class is the first, otherwise the class in the second
print(prediction) # the round function will trasform every number less or equal to 0.5 to zero, and above 0.5 to 1
#with the round function we could evalutate wich class the model predicted between class 0 and 1
"""