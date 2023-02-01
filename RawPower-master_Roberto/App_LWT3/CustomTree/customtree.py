import tkinter as tk
from tkinter import ttk

class EntryPopup(tk.Entry):
    def __init__(self,master,tree, iidrow, values,id, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(tree, **kw)
        self.window=master
        self.tv = tree
        self.iidrow = iidrow
        self.element_id=id
        self.values=values

        self.insert(0, values[id]) 
        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        # self['selectbackground'] = '#1BA1E2'
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):
        self.values[self.element_id]=self.get()
        try:
            self.values[self.element_id]=self.values[self.element_id].replace(',','.')
            self.values[self.element_id]=float(self.values[self.element_id])
            self.values=tuple(self.values)
            self.tv.item(self.iidrow,values=self.values)
        except:
            tk.messagebox.showerror(title='value error',message='Values must be real numbers')
            self.window.lift()
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'

class customtree: 
    """
    editable treeview
    """
    def __init__(self,master,frame):
        self.master=master
        self.frame=frame
        self._tree=ttk.Treeview(self.frame)
        self._tree.bind('<Double-Button-1>',self.onDoubleClick)

    def set_variables(self,names,width):
        """
        set columns names
        """
        self._tree["columns"]=names
        self._tree.column("#0",width=200,stretch=tk.NO)
        self._tree.heading("#0",text="TIME",anchor=tk.W)
        self.width_column=width
        
        for name in names:
            self._tree.column(name,width=self.width_column,stretch=tk.NO)
            self._tree.heading(name,text=name,anchor=tk.W)


    def onDoubleClick(self, event):
        ''' Executed, when a row is double-clicked. Opens 
        read-only EntryPopup above the item's column, so it is possible
        to select text '''

        # close previous popups
        # self.destroyPopups()
        
        # what row and column was clicked on
        rowid = self._tree.identify_row(event.y)
        column = self._tree.identify_column(event.x)
    
        # get column position info
        x,y,width,height = self._tree.bbox(rowid, column)
        if x>200: #not first column
            # y-axis offset
            # pady = height // 2
            pady = 9
            padx = 20
            
            id= (x-200)//self.width_column #value id

            # place Entry popup properly         
            values = self._tree.item(rowid, 'values')
            self.entryPopup = EntryPopup(self.master,self._tree, rowid, list(values),id)
            self.entryPopup.place( x=x+padx, y=y+pady, anchor=tk.W)
