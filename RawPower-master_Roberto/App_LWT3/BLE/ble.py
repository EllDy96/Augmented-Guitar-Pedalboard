#MODULO PER LA GESTIONE DEI DISPOSITIVI BLE

import asyncio

import platform
import logging

import psutil
import datetime
import time

import csv
import numpy as np

def scan_BLE():   
    """
    scan BLE devices

    Returns: 
        list of strings: BLE devices
    """
    from bleak import discover
    async def run():
        BLE_MAC=[]
        devices = await discover()
        for d in devices:
            BLE_MAC.append(str(d))
        return BLE_MAC

    loop = asyncio.get_event_loop()
    BLE_MAC=loop.run_until_complete(run())
    
    return BLE_MAC

def BLE_acquiring(BLE_MAC,start_event,stop_event,path_directory):
    """
    acquires BLE data

    Args:
        BLE_MAC (list): list containing tuples (BLE MAC address, UUID and NAME)
        start_event (multiprocessing.Event): event that syncrhonyze acquisition start 
        stop_event (multiprocessing.Event): event that syncrhonyze acquisition stop 
        path_directory(string): path of the directory where files will be saved
    """
    from bleak import BleakClient
    #alzo priorità del processo
    p=psutil.Process()
    p.nice(psutil.REALTIME_PRIORITY_CLASS)

    async def run(address, UUID,name, loop):
        while not stop_event.is_set(): #fino a quando non premo STOP nella GUI prova a stabilire una connessione con il dispositivo BLE
            try:
                async with BleakClient(address, loop=loop) as client:
                    x = await client.is_connected()
                    print(f'Connected {address} {datetime.datetime.now()}')  

                    #apertura file CSV (da customizzare in base alle caratteristiche del BLE)
                    timestr = time.strftime("%Y%m%d_%H%M%S")
                    name=name.replace(' ','_')
                    path_file=os.path.abspath(os.path.join(f'{path_directory}',f'{name}_{timestr}.csv'))
                    outfile=open(path_file, 'w+') #open a .csv file and write header
                    filewriter = csv.writer(outfile, delimiter=';',
                                        quotechar=' ', quoting=csv.QUOTE_MINIMAL,lineterminator = '\n')
                    filewriter.writerow(['TIME','HR']) #csv header
   
                    def notify_handler(sender, data):
                        filewriter.writerow([datetime.datetime.now(),data[1]]) #HR è in data[1]
                        
                    start_event.wait() #fino a questo punto arrivo in maniera sincrona agli altri processi
                    await client.start_notify(UUID, notify_handler) #notifica di avvio
                    while not stop_event.is_set(): #fino a quando non premo il tasto stop nella GUI
                        await asyncio.sleep(1.0, loop=loop)
                    await client.stop_notify(UUID) #stoppo la comunicazione
                    print(f'Disconnected {address} {datetime.datetime.now()}')
                    outfile.close()
            except Exception as e: #se non riesco a connettermi
                print(f'Trying to connect... {e}')    

    if not BLE_MAC == []: #check se esistono dei BLE address
        import os
        os.environ["PYTHONASYNCIODEBUG"] = str(1)
        addresses=[]
        UUIDs=[]
        names=[]
        for address_uuid_name in BLE_MAC:
            addresses.append(address_uuid_name[0]) 
            UUIDs.append(address_uuid_name[1])
            names.append(address_uuid_name[2])
        
        loop = asyncio.get_event_loop()
        
        #processi diversi per i diversi dispositivi BLE
        tasks = asyncio.gather(
        *(run(address,UUID,name, loop) for address,UUID,name in zip(addresses,UUIDs,names))
        )
        
        loop.run_until_complete(tasks)

def service_explorer(address):
    """
    finds and returns BLE services

    Args:
        address (string): BLE MAC address
    
    Returns:
        list of strings: BLE services
    """
    from bleak import BleakClient
    async def run(address, loop):
        connect=False
        while not connect:
            try:
                async with BleakClient(address, loop=loop) as client:
                    x = await client.is_connected()
                    print(f'get services for {address}')

                    list_services=[]
                    for service in client.services:
                        list_services.append(service.description)
                        
                    connect=True
                    return list_services
            except Exception as e:
                print(f'Trying to connect... {e}')

    import multiprocessing
    from ProgressBar.progress_bar import show_progress_bar
    progressbar_process=None 
    start_stop_event=multiprocessing.Event()
    start_stop_event.set() 
    progressbar_process=multiprocessing.Process(target=show_progress_bar,args=(start_stop_event,'Connecting to BLEs...',))
    progressbar_process.start()

    loop = asyncio.get_event_loop()
    list_services=loop.run_until_complete(run(address, loop))

    start_stop_event.clear()
    progressbar_process=None

    return list_services

if __name__ == "__main__":
    list_services=service_explorer('C1:C0:1D:3D:3D:9D')
    print(list_services)
