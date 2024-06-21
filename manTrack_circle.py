import tkinter as tk
import tkinter.filedialog as TFD
import tkinter.messagebox as TMB
from matplotlib.figure import Figure
from matplotlib.image import imread
from matplotlib import colors
import matplotlib.patches as mpatches
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
        self.deleteTmpStringVar = tk.StringVar()
        self.addTmpStringVar = tk.StringVar()        
        # self.PPUStringVar = tk.StringVar()
        self.minorAxisStringVar = tk.StringVar()
        # self.PPULabelStringVar = tk.StringVar()
        self.minorAxisLabelStringVar = tk.StringVar()
        # self.PPU = 100
        self.minorAxis = 10
        self.mousePosStringVar.set(str(self.mousePos[0]) + ', ' + str(self.mousePos[1]))
        self.mode.set('I')
        self.colorButtonText.set('Color plot')
        self.workingDir = os.getcwd()
        
        self.dID = -1
        self.tID = -1
        self.deletedArtist = []
        self.addedArtist = []
        self.artistList = []
        self.data = pd.DataFrame()
        self.addedData = pd.DataFrame()
        self.deletedData = pd.DataFrame()
        # self.PPUStringVar.set(str(self.PPU))
        # self.minorAxisStringVar.set(str(self.minorAxis))
        
    def create_widgets(self):
        # DATA LOADING buttons
        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side='left')
        loadLabel = tk.Label(self.buttonFrame, text='DATA LOADING', font=('Helvetica', 10, 'bold'))
        loadLabel.pack(fill='x')
        self.loadButton = tk.Button(self.buttonFrame, text='Load', command=self.imgOpenDialog)
        self.loadButton.pack(fill='x')
        self.loadDataButton = tk.Button(self.buttonFrame, text='Load data', command=self.dataOpenDialog)
        self.loadDataButton.pack(fill='x')
        self.drawDataButton = tk.Button(self.buttonFrame, text='Draw data', command=self.drawData)
        self.drawDataButton.pack(fill='x')
        self.reloadButton = tk.Button(self.buttonFrame, text='Reload', command=self.reloadButtonCallback)
        self.reloadButton.pack(fill='x')
        spaceFrame1 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame1.pack()
        
        # DATA SAVING buttons
        saveLabel = tk.Label(self.buttonFrame, text='DATA SAVING', font=('Helvetica', 10, 'bold'))
        saveLabel.pack(fill='x')
        self.mergeDataButton = tk.Button(self.buttonFrame, text='Merge data', command=self.mergeDataButtonCallback)
        self.mergeDataButton.pack(fill='x')
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
            rb = tk.Radiobutton(self.buttonFrame, text=text, variable=self.mode, value=mode, indicatoron=0,
                                command=self.modeCallback)
            rb.pack(fill='x')

        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()
                 
        self.backwardButton = tk.Button(self.buttonFrame, text='Backward', state='disabled', command=self.backwardButtonCallback)
        self.backwardButton.pack(fill='x')       
        self.colorButton = tk.Button(self.buttonFrame, text='Color/Mono plot', command=self.colorButtonCallback)
        self.colorButton.pack(fill='x')
        
        # Status block, tracking status of background data
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()
        statLabel = tk.Label(self.buttonFrame, text='STATUS BLOCK', font=('Helvetica', 10, 'bold'))
        statLabel.pack(fill='x')
        self.mousePositionLabel = tk.Label(self.buttonFrame, textvariable=self.mousePosStringVar)
        self.mousePositionLabel.pack(fill='x') 
        self.dataStatLabel = tk.Label(self.buttonFrame, textvariable=self.dataStatStringVar)
        self.dataStatLabel.pack(fill='x')
        self.deleteTmpLabel = tk.Label(self.buttonFrame, textvariable=self.deleteTmpStringVar)
        self.deleteTmpLabel.pack(fill='x')
        self.addTmpLabel = tk.Label(self.buttonFrame, textvariable=self.addTmpStringVar)
        self.addTmpLabel.pack(fill='x')
        self.updateStatus()
    
    def initCanvas(self):        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # Use matplotlib.backend to generate GUI widget
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='left')
        self.pID = self.canvas.mpl_connect('motion_notify_event', self.mousePosCallback)
    
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
            self.artistList = []
            self.dID = -1
            self.tID = -1
        except Exception as e:
            TMB.showerror('File type error', f"Error reading file: {e}")
        self.updateStatus()

    def drawData(self):
        if self.data.empty:
            TMB.showerror('Data error', 'Please load data')
            return
        data = self.data
        for artist in self.artistList:
            artist.remove()
        self.artistList = []
        for i, row in data.iterrows():
            x = row['x']# * self.compressRatio
            y = row['y']# * self.compressRatio
            color = 'r'
            patch = mpatches.Circle((x, y), radius=row["r"], fill=False, color=color)
            patch.set_picker(True)
            self.ax.add_patch(patch)
            self.artistList.append(patch)
        self.canvas.draw()

    def modeCallback(self):
        mode = self.mode.get()
        if mode == 'D':
            self.canvas.get_tk_widget().config(cursor='cross')
            self.dID = self.canvas.mpl_connect('pick_event', self.mouseDeleteCallback)
            self.canvas.mpl_disconnect(self.tID)
        elif mode == 'T':
            self.canvas.get_tk_widget().config(cursor='tcross')
            self.tID = self.canvas.mpl_connect('button_press_event', self.mouseTrackPressCallback)
            self.canvas.mpl_disconnect(self.dID)
        else:
            self.canvas.get_tk_widget().config(cursor='')
            self.canvas.mpl_disconnect(self.dID)
            self.canvas.mpl_disconnect(self.tID)

    def mouseDeleteCallback(self, event):
        artist = event.artist
        artist.set_visible(False)
        artist.set_picker(None)
        self.canvas.draw()
        xy = artist.center
        index = self.artistList.index(artist)
        print('Delete an ellipse at (%.1f, %.1f) ...' % (xy[0], xy[1]))      
        deletedDataFrame = self.data.iloc[index].to_frame().transpose()

        try:
            self.deletedData = pd.concat([self.deletedData, deletedDataFrame])
        except:
            self.deletedData = deletedDataFrame
        self.backwardButton.config(state='normal')
        self.deletedArtist.append(artist)
        self.updateStatus()

    def mouseTrackPressCallback(self, event):
        # print('you pressed', event.button, event.xdata, event.ydata)
        self.x1 = event.xdata
        self.y1 = event.ydata
        self.releaseID = self.canvas.mpl_connect('button_release_event', self.mouseTrackReleaseCallback)      
        
    def mouseTrackReleaseCallback(self, event):
        self.canvas.mpl_disconnect(self.releaseID)
        # print('you released', event.button, event.xdata, event.ydata)
        self.x2 = event.xdata
        self.y2 = event.ydata               
        No = -1;
        Area = -1;
        X = (self.x1 + self.x2) / 2 
        Y = (self.y1 + self.y2) / 2
        R = ((self.x1 - self.x2)**2+(self.y1 - self.y2)**2)**.5 / 2
        elli = mpatches.Circle((X, Y), R)
        elli.set_fill(False)
        elli.set_color('red')
        elli.set_picker("true")
        self.ax.add_patch(elli)
        self.canvas.draw()
        print('Add an ellipse at (%.1f, %.1f) ...' % (X, Y))

        data = np.array([[X, Y, R]])
        header = self.data.columns.tolist()
        
        addedDataFrame = pd.DataFrame(data=data, columns=header)
        try:
            self.addedData = pd.concat([self.addedData, addedDataFrame])
        except:
            self.addedData = deletedDataFrame

        self.addedArtist.append(elli)
        self.backwardButton.config(state='normal')
        self.updateStatus()

    def backwardButtonCallback(self):
        if self.mode.get() == 'D':
            # draw ellipse according to the last row of self.deletedArtist
            artist = self.deletedArtist.pop()
            artist.set_visible(True)
            artist.set_picker(True)
            self.canvas.draw()       
            # delete the last row of self.deletedData
            idx = self.deletedData.last_valid_index()
            self.deletedData.drop(axis=0, index=idx, inplace=True)
            # when self.deletedData is empty, set "Backward" button to DISABLED
            if self.deletedData.empty == True:
                self.backwardButton.config(state='disabled')
                # self.deletedData = None
        if self.mode.get() == 'T':
            # Delete ellipse according to the last row of self.deletedData
            artist = self.addedArtist.pop()
            artist.set_visible(False)
            artist.set_picker(None)
            self.canvas.draw()       
            # delete the last row of self.addedData
            idx = self.addedData.last_valid_index()
            # pdb.set_trace()
            self.addedData.drop(axis=0, index=idx, inplace=True)
            # when self.deletedData is empty, set "Backward" button to DISABLED
            if self.addedData.empty == True:
                self.backwardButton.config(state='disabled')
                # self.addedData = None
        self.updateStatus()

    def colorButtonCallback(self):
        if self.colorButtonText.get() == 'Color plot':
            self.colorButtonText.set('Mono plot')
        else:
            self.colorButtonText.set('Color plot')
        self.updateStatus()

    def mergeDataButtonCallback(self):
        if self.deletedData.empty == False:
            for index, value in self.deletedData.iterrows():                    
                self.data.drop(index=index, inplace=True)
            self.deletedData = pd.DataFrame()
        if self.addedData.empty == False:
            self.data = pd.concat([self.data, self.addedData])
            self.addedData = pd.DataFrame()    
        # self.mode.set('I')
        # self.modeCallback()
        self.updateStatus()

    def saveDataButtonCallback(self):
        if self.data.empty:
            TMB.showerror('Data error', 'No data to save')
            return
        file = TFD.asksaveasfilename(filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xls;*.xlsx")))
        if not file:
            return
        try:
            if file.endswith('.csv'):
                self.data.to_csv(file, index=False)
            elif file.endswith(('.xls', '.xlsx')):
                self.data.to_excel(file, index=False)
        except Exception as e:
            TMB.showerror('Save error', f"Error saving file: {e}")

    def saveFigButtonCallback(self):
        file = TFD.asksaveasfilename(filetypes=(("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")))
        if not file:
            return
        try:
            self.fig.savefig(file)
        except Exception as e:
            TMB.showerror('Save error', f"Error saving figure: {e}")

    def reloadButtonCallback(self):
        try:
            self.imgOpenDialog()
            self.dataOpenDialog()
            self.drawData()
        except Exception as e:
            TMB.showerror('Reload error', f"Error reloading: {e}")

    def mousePosCallback(self, event):
        if event.inaxes != self.ax:
            return
        self.mousePos = [event.xdata / self.compressRatio, event.ydata / self.compressRatio]
        self.mousePosStringVar.set(f'{self.mousePos[0]:.2f}, {self.mousePos[1]:.2f}')
        self.updateStatus()

    def updateStatus(self):
        self.dataStatStringVar.set(f'Data points: {len(self.data)}')
        self.deleteTmpStringVar.set(f'Deleted points: {len(self.deletedData)}')
        self.addTmpStringVar.set(f'Added points: {len(self.addedData)}')

root = tk.Tk()
app = mplApp(master=root)
app.pack()
app.mainloop()
