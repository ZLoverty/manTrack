import tkinter as tk
import tkinter.filedialog as TFD
import tkinter.messagebox as TMB
from matplotlib.figure import Figure
from matplotlib.image import imread
from matplotlib import colors
import matplotlib.patches as mpatch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes
import os
import numpy as np
import pandas as pd
import math

class mplApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.createVars()
        self.create_widgets()
        
    """
    Components
    """
    def createVars(self):
        self.mousePos = [0, 0]
        self.mousePosStringVar = tk.StringVar()
        self.mode = tk.StringVar()
        self.colorButtonText = tk.StringVar()
        self.dataStatStringVar = tk.StringVar()
        self.cacheStringVar = tk.StringVar()
        self.mousePosStringVar.set(str(self.mousePos[0]) + ', ' + str(self.mousePos[1]))
        self.mode.set('I')
        self.workingDir = os.getcwd()
        self.history_list = []
        
        self.dID = -1
        self.tID = -1

        self.data = pd.DataFrame()
        self.tmpArtist = mpatch.Circle((0,0), 0, visible=False, color="g", fill=False)

    def create_widgets(self):
        # DATA LOADING buttons
        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side='left')
        loadLabel = tk.Label(self.buttonFrame, text='DATA LOADING', font=('Helvetica', 10, 'bold'))
        loadLabel.pack(fill='x')
        self.loadButton = tk.Button(self.buttonFrame, text='Load image', command=self.imgOpenDialog)
        self.loadButton.pack(fill='x')
        self.loadDataButton = tk.Button(self.buttonFrame, text='Load data', command=self.dataOpenDialog)
        self.loadDataButton.pack(fill='x')
        self.drawDataButton = tk.Button(self.buttonFrame, text='Draw data', command=self.drawData)
        self.drawDataButton.pack(fill='x')
        spaceFrame1 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame1.pack()
        
        # DATA SAVING buttons
        saveLabel = tk.Label(self.buttonFrame, text='DATA SAVING', font=('Helvetica', 10, 'bold'))
        saveLabel.pack(fill='x')
        self.saveDataButton = tk.Button(self.buttonFrame, text='Save data', command=self.saveDataButtonCallback)
        self.saveDataButton.pack(fill='x')
        self.saveFigButton = tk.Button(self.buttonFrame, text='Save figure', command=self.saveFigButtonCallback)
        self.saveFigButton.pack(fill='x')
        
        # MODE buttons
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()  
        modeLabel = tk.Label(self.buttonFrame, text='MODE', font=('Helvetica', 10, 'bold'))
        modeLabel.pack(fill='x')
        MODES = [('Idle mode', 'I'), ('Delete mode', 'D'), ('Track mode', 'T')]
        for text, mode in MODES:
            rb = tk.Radiobutton(self.buttonFrame, text=text, variable=self.mode, value=mode, indicatoron=0, command=self.modeCallback)
            rb.pack(fill='x')
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()
                 
        self.backwardButton = tk.Button(self.buttonFrame, text='Backward', state='disabled', command=self.backwardButtonCallback)
        self.backwardButton.pack(fill='x')       
        
        # Status block, tracking status of background data
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()
        statLabel = tk.Label(self.buttonFrame, text='STATUS BLOCK', font=('Helvetica', 10, 'bold'))
        statLabel.pack(fill='x')
        self.mousePositionLabel = tk.Label(self.buttonFrame, textvariable=self.mousePosStringVar)
        self.mousePositionLabel.pack(fill='x') 
        self.dataStatLabel = tk.Label(self.buttonFrame, textvariable=self.dataStatStringVar)
        self.dataStatLabel.pack(fill='x')
        self.cacheLabel = tk.Label(self.buttonFrame, textvariable=self.cacheStringVar)
        self.cacheLabel.pack(fill='x')
        self.updateStatus()
    
    def initCanvas(self):        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # Use matplotlib.backend to generate GUI widget
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='left')
        # self.pID = self.canvas.mpl_connect('motion_notify_event', self.mousePosCallback)
    
    """
    Callbacks
    """
    def imgOpenDialog(self):
        try:
            self.canvas.get_tk_widget().destroy()
        except AttributeError:
            pass
        imgDir = TFD.askopenfilename()
        if not imgDir:
            return
        folder, filename = os.path.split(imgDir)
        if not filename.endswith('.tif'):
            TMB.showerror('File type error', 'Please open *.tif file')
            return
        self.workingDir = folder
        img = imread(imgDir)        
        self.img = img
        h, w = img.shape[-2:]
        dpi = 100
        hcanvas = h
        wcanvas = w
        self.compressRatio = 1
        user32 = ctypes.windll.user32
        wmax = math.floor(0.92 * user32.GetSystemMetrics(0))
        hmax = math.floor(0.92 * user32.GetSystemMetrics(1))
        if wcanvas > wmax:
            wcanvas = wmax
            hcanvas = h / w * wcanvas
            self.compressRatio = wmax / w
        if hcanvas > hmax:
            hcanvas = hmax
            wcanvas = w / h * hcanvas
            self.compressRatio = hmax / h
        self.fig = Figure(figsize=(wcanvas / dpi, hcanvas / dpi), dpi=dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.imshow(img, cmap='gray')
        self.initCanvas()
        self.updateStatus()
        
    def dataOpenDialog(self):
        dataDir = TFD.askopenfilename(filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xls;*.xlsx")))
        if not dataDir:
            return
        folder, filename = os.path.split(dataDir)
        self.workingDir = folder
        try:
            if filename.endswith('.csv'):
                self.data = pd.read_csv(dataDir)
            elif filename.endswith(('.xls', '.xlsx')):
                self.data = pd.read_excel(dataDir)
            # self.artistList = []

        except Exception as e:
            TMB.showerror('File type error', f"Error reading file: {e}")
        self.updateStatus()

    def drawData(self):
        if self.data.empty:
            TMB.showerror('Data error', 'Please load data')
            return
        data = self.data

        # if there exists any artist, remove it
        for artist in self.ax.artists:
            artist.remove()

        # create artist for all entries in data table
        # add the artists to canvas
        for i, row in data.iterrows():
            x = row['x']
            y = row['y']

            # set patch url as the index of the patch
            # will be used for deleting entry in the data table
            patch = mpatch.Circle((x, y), 
                                    radius=row["r"], 
                                    fill=False, 
                                    color="r",
                                    picker=True,
                                    url=i)
            

            self.ax.add_patch(patch)
            # self.artistList.append(patch)
        self.canvas.draw()

    def modeCallback(self):
        mode = self.mode.get()
        if mode == 'D': self.deleteMode()
        elif mode == 'T': self.trackMode()
        else: self.idleMode()
            
    def idleMode(self):
        self.canvas.get_tk_widget().config(cursor='')
        self.canvas.mpl_disconnect(self.dID)
        self.canvas.mpl_disconnect(self.tID)

    def trackMode(self):
        self.canvas.get_tk_widget().config(cursor='tcross')
        self.tID = self.canvas.mpl_connect('button_press_event', self.mouseTrackPressCallback)
        self.canvas.mpl_disconnect(self.dID)
        
    def deleteMode(self):
        self.canvas.get_tk_widget().config(cursor='cross')
        self.dID = self.canvas.mpl_connect('pick_event', self.mouseDeleteCallback)
        self.canvas.mpl_disconnect(self.tID)

    def mouseDeleteCallback(self, event):
        # get picked artist
        artist = event.artist

        # delete from canvas
        artist.remove()
        
        # read artist info and print to stdout
        xy = artist.center
        print('Delete an ellipse at (%.1f, %.1f) ...' % (xy[0], xy[1]))      

        # get the index of entry to delete
        del_ind = artist.get_url()

        # delete the chosen entry
        self.data.drop(index=del_ind, inplace=True)

        # add the deleted artist to history_list, in case we want to revert the edit
        self.history_list.append((artist, "delete"))

        # set backward button to active
        self.backwardButton.config(state='normal')

        # update canvas and data status display
        self.canvas.draw()
        self.updateStatus()

    def mouseTrackPressCallback(self, event):
        # get the x y data at the click as the first point of the diameter
        self.x1 = event.xdata
        self.y1 = event.ydata

        # set temporary circle to be visible
        self.tmpArtist.set_visible(True)

        # activate the button release event
        self.moveID = self.canvas.mpl_connect("motion_notify_event", self.mouseMoveCallback)
        self.releaseID = self.canvas.mpl_connect('button_release_event', self.mouseTrackReleaseCallback)
    
    def mouseMoveCallback(self, event):
        x2 = event.xdata
        y2 = event.ydata 

        X = (self.x1 + x2) / 2 
        Y = (self.y1 + y2) / 2
        R = ((self.x1 - x2)**2 + (self.y1 - y2)**2)**.5 / 2

        self.tmpArtist.set_center((X, Y))
        self.tmpArtist.set_radius(R)
        self.ax.draw_artist(self.tmpArtist)
        self.canvas.draw()

    def mouseTrackReleaseCallback(self, event):
        self.canvas.mpl_disconnect(self.moveID)
        self.canvas.mpl_disconnect(self.releaseID)

        # set temporary artist invisible
        self.tmpArtist.set_visible(False)

        # get the x y data at the release as the second point of the diameter
        self.x2 = event.xdata
        self.y2 = event.ydata               

        # compute center location and radius
        X = (self.x1 + self.x2) / 2 
        Y = (self.y1 + self.y2) / 2
        R = ((self.x1 - self.x2)**2+(self.y1 - self.y2)**2)**.5 / 2

        # set the index of the patch to be added as the maximum of current index +1
        add_ind = self.data.index.max() + 1

        # generate the circle patch
        artist = mpatch.Circle((X, Y), R,
                             fill=False,
                             color="r",
                             picker=True, 
                             url=add_ind)
        self.ax.add_patch(artist)
        self.canvas.draw()

        print('Add an ellipse at (%.1f, %.1f) ...' % (X, Y))

        # write new circle data as a new entry in self.data
        self.data = pd.concat([self.data, pd.DataFrame(data={"x": X, "y": Y, "r": R}, index=[add_ind])])

        # append the added artist to history_list, in case we want to revert the change
        self.history_list.append((artist, "add"))

        # set backward button to active
        self.backwardButton.config(state='normal')

        # update data status display
        self.updateStatus()

    def backwardButtonCallback(self):
        # pop the most recent change out of the history_list
        artist, action = self.history_list.pop()

        # if the action is delete, we add this artist back to canvas and data
        if action == "delete": 
            # back to canvas
            self.ax.add_patch(artist)
            # back to data table
            deleted = pd.DataFrame(data={"x": artist.center[0],
                                         "y": artist.center[1],
                                         "r": artist.get_radius()}, 
                                   index=[artist.get_url()])
            self.data = pd.concat([self.data, deleted])
        # if the action is add, we remove this artist from canvas and data
        elif action == "add":
            # remove from canvas
            artist.remove()
            # remove from data
            del_ind = artist.get_url()
            self.data.drop(index=del_ind, inplace=True)

        self.canvas.draw()
        self.updateStatus()

        if self.history_list == []: # set backward button to active
            self.backwardButton.config(state='disabled')

    def saveDataButtonCallback(self):
        if self.data.empty:
            TMB.showerror('Data error', 'No data to save')
            return
        file = TFD.asksaveasfilename(filetypes=(("CSV files", "*.csv"),))
        if not file:
            return

        self.data.to_csv(file, index=False)

    def saveFigButtonCallback(self):
        file = TFD.asksaveasfilename(filetypes=(("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")))
        if not file:
            return
        try:
            self.fig.savefig(file)
        except Exception as e:
            TMB.showerror('Save error', f"Error saving figure: {e}")

    def mousePosCallback(self, event):
        if event.inaxes != self.ax:
            return
        self.mousePos = [event.xdata , event.ydata]
        self.mousePosStringVar.set(f'{self.mousePos[0]:.2f}, {self.mousePos[1]:.2f}')
        self.updateStatus()

    def updateStatus(self):
        self.dataStatStringVar.set(f'Data points: {len(self.data)}')
        self.cacheStringVar.set(f'Cached points: {len(self.history_list)}')


root = tk.Tk()
app = mplApp(master=root)
app.pack()
app.mainloop()
