#convert .png to .ico
from PIL import Image
import os
import inspect
filename=f'{os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))}\logo_lwt3.png'
print(filename)
#filename = r'logo_lwt3.png'
img = Image.open(filename)
img.save('logo_lwt3.ico',format = 'ICO', sizes=[(32,32)])