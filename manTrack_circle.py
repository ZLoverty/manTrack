"""
manTrack_circle.py
==================

Description
-----------

A simple python GUI program to for hand labeling of circle objects in images. This program features adding labels by drawing circles at mouse cursor with left button, and deleting labels by right clicking on existing labels. It also features a "undo" button, which reverts undesired edits. It also features loading existing labeling result from .csv files, which allows refining unperfect results from automatic detection algorithm.

The labeling data is a pandas.DataFrame with columns x, y, r. 

Edit
----

Jun 22, 2024: 

1. remove mode module -- the add/delete behavior can be separated by using different mouse buttons. Since our data management is no longer dependent on the mode, the mode module requires many more redundant operations and should be thus removed. 

2. use blit to make circle preview faster.

3. Fix the bug arising from repeatedly clicking "Draw data".
"""

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
import pdb

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
        self.colorButtonText = tk.StringVar()
        self.dataStatStringVar = tk.StringVar()
        self.cacheStringVar = tk.StringVar()
        self.workingDir = os.getcwd()
        self.history_list = []
        self.press = None

        self.data = pd.DataFrame()
        self.tmpArtist = None

    def create_widgets(self):
        
        # create the main frame for all the buttons
        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(side='left')

        # block title: DATA LOADING buttons
        loadLabel = tk.Label(self.buttonFrame, text='DATA LOADING', font=('Helvetica', 10, 'bold'))
        loadLabel.pack(fill='x')

        # load image button
        self.loadButton = tk.Button(self.buttonFrame, text='Load image', command=self.imgOpenDialog)
        self.loadButton.pack(fill='x')

        # load data button
        self.loadDataButton = tk.Button(self.buttonFrame, text='Load data', command=self.dataOpenDialog)
        self.loadDataButton.pack(fill='x')

        # draw data button
        self.drawDataButton = tk.Button(self.buttonFrame, text='Draw data', command=self.drawData)
        self.drawDataButton.pack(fill='x')
        
        
        # DATA SAVING buttons block

        # vertical spacer
        spaceFrame1 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame1.pack()

        # block title: data saving 
        saveLabel = tk.Label(self.buttonFrame, text='DATA SAVING', font=('Helvetica', 10, 'bold'))
        saveLabel.pack(fill='x')

        # save data button
        self.saveDataButton = tk.Button(self.buttonFrame, text='Save data', command=self.saveDataButtonCallback)
        self.saveDataButton.pack(fill='x')

        # save figure button
        self.saveFigButton = tk.Button(self.buttonFrame, text='Save figure', command=self.saveFigButtonCallback)
        self.saveFigButton.pack(fill='x')
        
        
        # Utility buttons block

        # vertical spacer
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()

        # title of the block: utilities
        saveLabel = tk.Label(self.buttonFrame, text='UTILITIES', font=('Helvetica', 10, 'bold'))
        saveLabel.pack(fill='x')

        # backward button
        self.backwardButton = tk.Button(self.buttonFrame, text='Backward', state='disabled', command=self.backwardButtonCallback)
        self.backwardButton.pack(fill='x')       
        
        # Status block, tracking status of background data

        # vertical spacer
        spaceFrame2 = tk.Frame(self.buttonFrame, height=30)
        spaceFrame2.pack()

        # block title: status
        statLabel = tk.Label(self.buttonFrame, text='STATUS', font=('Helvetica', 10, 'bold'))
        statLabel.pack(fill='x')

        # number of data points label
        self.dataStatLabel = tk.Label(self.buttonFrame, textvariable=self.dataStatStringVar)
        self.dataStatLabel.pack(fill='x')

        # number of cached points label
        self.cacheLabel = tk.Label(self.buttonFrame, textvariable=self.cacheStringVar)
        self.cacheLabel.pack(fill='x')

        # 
        self.updateStatus()
    
    def initCanvas(self):
        # Use matplotlib.backend to generate GUI widget
        # initialize the canvas with self.fig
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='left')

        # connect all the mouse events handler 

        # delete on_pick event
        self.canvas.mpl_connect('pick_event', self.mouseDeleteCallback)

        # tracking on_press event
        self.canvas.mpl_connect('button_press_event', self.mouseTrackPressCallback)

        # tracking on_motion event
        self.canvas.mpl_connect("motion_notify_event", self.mouseMoveCallback)
        
        # tracking on_release event
        self.canvas.mpl_connect('button_release_event', self.mouseTrackReleaseCallback)

        # change cursor
        # self.canvas.get_tk_widget().config(cursor='')
    
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
        wmax = np.floor(0.92 * user32.GetSystemMetrics(0))
        hmax = np.floor(0.92 * user32.GetSystemMetrics(1))
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

        except Exception as e:
            TMB.showerror('File type error', f"Error reading file: {e}")
        
        # if there exists any patch, remove it
        self.ax.patches.clear()

        # create and add artists to axes
        for i, row in self.data.iterrows():
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

        self.updateStatus()

    def drawData(self):      
        self.canvas.draw()

    def mouseDeleteCallback(self, event):
        """ If an artist is picked with RIGHT (3) click, remove it from both canvas and data table"""

        # only proceed if right button is pressed
        if event.mouseevent.button != 3:
            return

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
        """ Record the coords of LEFT (1) button press. """

        # only proceed if left button is pressed
        if event.button != 1:
            return

        # get the x y data at the click as the first point of the diameter
        self.press = event.xdata, event.ydata

        # create blit background 
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
    
    def mouseMoveCallback(self, event):
        """ Preview the circle drawing when LEFT (1) button is pressed. """

        # proceed only if left button has been pressed 
        if self.press == None or event.button != 1:
            return
        
        # read starting and ending coords
        x1, y1 = self.press
        x2, y2 = event.xdata, event.ydata

        # calculate circle center and radius
        x = (x1 + x2) / 2 
        y = (y1 + y2) / 2
        r = ((x1 - x2)**2 + (y1 - y2)**2)**.5 / 2

        # when moving mouse, a new circle will be created, so the old one should be removed
        if self.tmpArtist:
            self.tmpArtist.remove()

        # restore blit background
        self.canvas.restore_region(self.background)
        
        # draw the temporary circle
        self.tmpArtist = mpatch.Circle((x, y), r, fill=False, color="g")
        self.ax.add_patch(self.tmpArtist)

        self.canvas.draw()

    def mouseTrackReleaseCallback(self, event):
        """ Draw circle when LEFT (1) button is released. """

        # only proceed when left button is released
        if event.button != 1:
            return

        # set the index of the new patch
        # if self.data is empty, set the index as 0
        # otherwise, set the index as the maximum of current index +1
        if self.data.index.empty:
            add_ind = 0
        else:
            add_ind = self.data.index.max() + 1

        # generate the circle patch
        artist = self.tmpArtist

        # make the final artist pickable
        artist.set_picker(True)

        # assign a url to this artist as add_ind
        artist.set_url(add_ind)

        # remove the temporary artist
        self.tmpArtist.remove()
        self.tmpArtist = None

        self.ax.add_patch(artist)
        self.canvas.draw()

        # get artist center and radius
        x, y, r = artist.center[0], artist.center[1], artist.radius

        # print action
        print("Add an ellipse at ({0:.1f}, {1:.1f})".format(x, y))

        # write new circle data as a new entry in self.data
        self.data = pd.concat([self.data, pd.DataFrame(data={"x": x, "y": y, "r": r}, index=[add_ind])])

        # append the added artist to history_list, in case we want to revert the change
        self.history_list.append((artist, "add"))

        # set backward button to active
        self.backwardButton.config(state='normal')

        # update data status display
        self.updateStatus()

        # set self.press to None to deactivate the on_motion callbacks
        self.press = None

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
