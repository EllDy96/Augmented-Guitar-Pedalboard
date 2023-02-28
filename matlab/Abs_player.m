data = readtable('Abs_Test_Corretto.xlsx');
abs = data(1:end , 2);
sr = 1000

%%

MyMatrix = readmatrix('Abs_Test_Corretto.xlsx')

%%
abs_double = MyMatrix(1:end , 2)
abs_double = abs_double/max(abs_double)
%%

audiowrite("Klaas_Abs.wav", abs_double, sr)
[y,Fs] = audioread("Klaas_Abs.wav");
%sound(y,Fs);

%%
player = audioplayer(y,sr)
%play(player)