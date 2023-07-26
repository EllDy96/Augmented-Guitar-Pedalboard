from tkinter import filedialog
import xlsxwriter
import pandas as pd

def export_excel(Dataframe, check_fit):
    """export processed dataframe in .xlsx file  
    
    Args:
        Dataframe (pd.DataFrame): Dataframe containing the data  
        check_fit (bool): variable equals True when file .fit is available

    Returns:
        String: name of the exported file
    """
    f = filedialog.asksaveasfile(mode='w', defaultextension=".xlsx",filetypes=[('Excel Files','*.xlsx'),('All Files','*.*')])
    
    if check_fit:
        number_of_channels=len(Dataframe.columns)-3
    else:
        number_of_channels=len(Dataframe.columns)

    if not f==None: #se ho specificato il nome del file da salvare
        workbook = xlsxwriter.Workbook(f'{f.name}')
        worksheet = workbook.add_worksheet()

        # Add a bold format to use to highlight cells
        bold = workbook.add_format({'bold': True})

        # date format
        date_format_type = 'hh:mm:ss'

        # Create a format for the date or time.
        date_format = workbook.add_format({'num_format': date_format_type,'align': 'left'})

        # num format 
        number_format = workbook.add_format({'num_format': '#,##0'})

        # Write header
        worksheet.write('A1','TIME',bold)
        # ROBERTO # se c'è solo gli 8 canali dell'EMG bastano solo 8 canali
        #list_columns_mnf=['B1','C1','D1','E1','F1','G1','H1','I1','J1','K1','L1','M1','N1','O1','P1','Q1']
        list_columns_mnf=['B1','C1','D1','E1','F1','G1','H1','I1']


        print("number of channels, list_columns_mnf, dataframe columns = {}, {}, {}".format(number_of_channels,len(list_columns_mnf), len(Dataframe.columns)))
        print("\nlist_columns_mnf, dataframe columns = {}, {}".format(list_columns_mnf, Dataframe.columns))
        for id in range(number_of_channels):
            #worksheet.write(list_columns_mnf[id],f'{Dataframe.columns[id]}', bold)
            worksheet.write(list_columns_mnf[id],f'{Dataframe.columns[id]}', bold)

        #if .fit file availavle
        list_columns_fit=['C1','D1','E1','F1','G1','H1','I1','J1','K1','L1','M1','N1','O1','P1','Q1','R1','S1','T1']
        if check_fit:
            #write power, HR and cadence header
            for i in range(3):
                worksheet.write(list_columns_fit[number_of_channels -1 + i],f'{Dataframe.columns[number_of_channels + i]}', bold)

        for i in range(len(Dataframe)):
            #write MNF values and timestamp
            worksheet.write_datetime(i+1,0,Dataframe.index[i],date_format)
            for channel in range(number_of_channels):
                worksheet.write_number(i+1,channel+1,Dataframe.iloc[i,channel],number_format)

            #if .fit file available
            if check_fit:
                #write power, HR and cadence
                worksheet.write_number(i+1,number_of_channels + 1, Dataframe.iloc[i,number_of_channels],number_format)
                worksheet.write_number(i+1,number_of_channels + 2 , Dataframe.iloc[i,number_of_channels + 1],number_format)
                worksheet.write_number(i+1,number_of_channels + 3, Dataframe.iloc[i,number_of_channels + 2],number_format)

        workbook.close()
        
        return f

def export_all_rms_excel(Dataframe):
    """export rms dataframe in .xlsx file  
    
    Args:
        Dataframe (pd.DataFrame): Dataframe containing the data  

    Returns:
        String: name of the exported file
    """
    f = filedialog.asksaveasfile(mode='w', defaultextension=".xlsx",filetypes=[('Excel Files','*.xlsx'),('All Files','*.*')])

    if not f==None: #se ho specificato il nome del file da salvare
        workbook = xlsxwriter.Workbook(f'{f.name}')
        worksheet = workbook.add_worksheet()

        number_of_channels=len(Dataframe.columns)

        # Add a bold format to use to highlight cells
        bold = workbook.add_format({'bold': True})

        # date format
        date_format_type = 'hh:mm:ss.000'

        # Create a format for the date or time.
        date_format = workbook.add_format({'num_format': date_format_type,'align': 'left'})

        # num format 
        number_format = workbook.add_format({'num_format': '#,##0.00'})

        # Write header
        worksheet.write('A1','TIME',bold)
        list_columns=['B1','C1','D1','E1','F1','G1','H1','I1']
        for id in range(number_of_channels):
            worksheet.write(list_columns[id],f'{Dataframe.columns[id]}', bold)
    
        for i in range(len(Dataframe)):
            worksheet.write_datetime(i+1,0,Dataframe.index[i],date_format)
            for channel in range(number_of_channels):
                worksheet.write_number(i+1,channel+1,Dataframe.iloc[i,channel],number_format)

        workbook.close()
        
        return f

def save_report(finish_event,profile,file_directory):
    """
    saves pandas profile in file_directory

    Args:
        finish_event (multiprocessing.Event): event set to True when the report will be saved  
        profile (pandas ProfileReport): report to be saved
        file_directory (string): file_directory path
    """
    from pandas_profiling import ProfileReport
    finish_event.clear()
    profile.to_file(f'{file_directory}/features_report.html')
    finish_event.set()
