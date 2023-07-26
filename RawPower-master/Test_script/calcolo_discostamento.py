#script per il calcolo del massimo discostamento tra due campioni
import tkinter as tk
from tkinter import filedialog

import pandas as pd
import numpy as np

filename= filedialog.askopenfile(filetypes=[("csv files","*.csv")])
emg = pd.read_csv(f'{filename.name}', delimiter = ';', on_bad_lines='warn')
emg=emg.iloc[:,3:]

def fun(x):
    diff=x[1:].values-x[:-1].values
    return abs(diff)

emg_delta=emg.apply(lambda x: fun(x))

Max=[]
for muscle in emg_delta:
    data=emg_delta[f'{muscle}']
    occurrence=data.value_counts()
    Max.append(occurrence)

observation=sum(Max[0].values)
a_list=[]
b_list=[]
c_list=[]
d_list=[]
e_list=[]
f_list=[]
g_list=[]
h_list=[]
i_list=[]
l_list=[]
for m in Max:
    a = round((sum(m[(m.index<128)].values[:-1])/observation)*100,0)
    a_list.append(a)
    b = round((sum(m[(m.index<256)].values[:-1])/observation)*100,0)
    b_list.append(b)
    c = round((sum(m[(m.index<512)].values[:-1])/observation)*100,0)
    c_list.append(c)
    d = round((sum(m[(m.index<1024)].values[:-1])/observation)*100,0)
    d_list.append(d)
    e = round((sum(m[(m.index<2048)].values[:-1])/observation)*100,0)
    e_list.append(e)
    f = round((sum(m[(m.index<4096)].values[:-1])/observation)*100,0)
    f_list.append(f)
    g = round((sum(m[(m.index<8192)].values[:-1])/observation)*100,0)
    g_list.append(g)
    h = round((sum(m[(m.index<16384)].values[:-1])/observation)*100,0)
    h_list.append(h)
    i = round((sum(m[(m.index<32768)].values[:-1])/observation)*100,0)
    i_list.append(i)
    l = round((sum(m[(m.index<65536)].values[:-1])/observation)*100,0)
    l_list.append(l)

print(f'% diff max 128; {a_list}')
print(f'% diff max 256; {b_list}')
print(f'% diff max 512; {c_list}')
print(f'% diff max 1024; {d_list}')
print(f'% diff max 2048; {e_list}')
print(f'% diff max 4096; {f_list}')
print(f'% diff max 8192; {g_list}')
print(f'% diff max 16384; {h_list}')
print(f'% diff max 32768; {i_list}')
print(f'% diff max 65536; {l_list}')
