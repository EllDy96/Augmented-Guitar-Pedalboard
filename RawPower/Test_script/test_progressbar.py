import tkinter as tk
from tkinter import ttk
root = tk.Tk()
s = ttk.Style()
s.theme_use('clam')
s.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
ttk.Progressbar(root, style="red.Horizontal.TProgressbar", orient="horizontal", length=600, mode="indeterminate").grid(row=1, column=1)
root.mainloop()