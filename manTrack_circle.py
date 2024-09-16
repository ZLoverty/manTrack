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

4. Cross cursor when labeling.

Jun 23, 2024:

1. Enable zooming and panning with middle button.

2. Reorganize the mouse button callbacks: e.g. all the presses can be grouped in the same callback function on_press.

3. Enable keyboard shortcuts for undo and reset zoom.

July 12, 2024:

1. Load canvas and axes on start to avoid error.
"""

import tkinter as tk
import tkinter.filedialog as TFD
import tkinter.messagebox as TMB
from matplotlib.figure import Figure
from skimage import io
from matplotlib import colors
import matplotlib.patches as mpatch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ctypes
import os
import numpy as np
import pandas as pd
import pdb
import matplotlib
matplotlib.use('TkAgg')
from pathlib import Path

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
        self.pan_start = None

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

        # undo button
        self.backwardButton = tk.Button(self.buttonFrame, text='Undo (\u232B)', state='disabled', command=self.backwardButtonCallback)
        self.backwardButton.pack(fill='x')

        # reset zoom button
        self.resetButton = tk.Button(self.buttonFrame, text='Reset zoom (\u2423)', command=self.resetButtonCallback)
        self.resetButton.pack(fill='x')  
        
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
        self.initCanvas()
        self.updateStatus()
    
    def initCanvas(self):
        # Use matplotlib.backend to generate GUI widget
        # initialize the canvas with self.fig
        self.fig = Figure(figsize=(8,6), dpi=200)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side='left', fill='both', expand=True)

        # connect all the mouse events handler 

        # delete on_pick event
        self.canvas.mpl_connect('pick_event', self.on_pick)

        # tracking on_press event
        self.canvas.mpl_connect('button_press_event', self.on_press)

        # tracking on_motion event
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        
        # tracking on_release event
        self.canvas.mpl_connect('button_release_event', self.on_release)

        # scrolling zoom event
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # key press event
        self.canvas.mpl_connect("key_press_event", self.on_key)
    
        # create blit background 
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    
    """
    Callbacks
    """

    def imgOpenDialog(self):
      
        # Open file dialog and get image path, include many image formats
        img_path = TFD.askopenfilename(filetypes=[("TIFF files", "*.tif"), ("JPEG files", "*.jpg"), ("PNG files", "*.png")])
        if not img_path:  # If no file is selected
            return

        img_path = Path(img_path)

        self.workingDir = img_path.parent

        # Read image
        img = io.imread(img_path)
        self.img = img
        self.ax.imshow(img, cmap='gray')
        self.ax.axis("off")

        # Get original limits for resetting
        self.ori_xlim = self.ax.get_xlim()
        self.ori_ylim = self.ax.get_ylim()

        # Initialize canvas and update status block
        self.canvas.draw()
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
        for patch in self.ax.patches:
            patch.remove()

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
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def on_press(self, event):
        """ If an artist is picked with RIGHT (3) click, remove it from both canvas and data table"""

        # if left button is pressed, start the hand labeling circle drawing
        if event.button == 1:

            # get the x y data at the click as the first point of the diameter
            self.press = event.xdata, event.ydata

            # change cursor to cross
            self.canvas.get_tk_widget().config(cursor='crosshair')

            # cache background
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)

        # if middle mouse button is pressed, start the panning mode by setting self.pan_start
        elif event.button == 2:

            # set pan_start
            self.pan_start = (event.xdata, event.ydata)

            # change cursor to hand
            self.canvas.get_tk_widget().config(cursor='hand2')


    def on_pick(self, event):
        """ PickEvent callback, remove patch picked with right click. """

        # if right button is pressed, remove the picked patch
        if event.mouseevent.button == 3:

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

    def on_motion(self, event):
        """ Preview the circle drawing when LEFT (1) button is pressed. """

        # proceed only if left button has been pressed 
        if self.press is not None and event.button == 1 and event.inaxes == self.ax:   
            
            # restore background
            self.canvas.restore_region(self.background)         
        
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
            
            # draw the temporary circle
            self.tmpArtist = mpatch.Circle((x, y), r, fill=False, color="g")
            self.ax.add_patch(self.tmpArtist)
            self.ax.draw_artist(self.tmpArtist)

            self.canvas.blit(self.ax.bbox)
        
        elif self.pan_start is not None and event.inaxes == self.ax:
            
            # restore background
            # self.canvas.restore_region(self.background)   

            # set new axis lims
            dx = event.xdata - self.pan_start[0]
            dy = event.ydata - self.pan_start[1]
            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()

            self.ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
            self.ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)

            self.canvas.draw_idle()
        
    def on_release(self, event):
        """ Draw circle when LEFT (1) button is released. """
        if self.event_in_axes(event):
            # only proceed when left button is released
            if event.button == 1:
                # set the index of the new patch: if self.data is empty, set the index as 0; otherwise, set the index as the maximum of current index +1.
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

                # draw new patch
                self.ax.add_patch(artist)
                
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

                # set self.press to None to deactivate the on_motion callbacks
                self.press = None

                # update canvas
                self.canvas.draw_idle()
        
            # if middle button is release, stop panning by setting self.pan_start as None
            elif event.button == 2:
                self.pan_start = None

                # update canvas
                self.canvas.draw_idle()

            # change cursor back to normal
            self.canvas.get_tk_widget().config(cursor='arrow')

            # update data status display
            self.updateStatus()

    def on_scroll(self, event):
        """ Zoom in and zoom out with scrolling. """

        base_scale = 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * (relx)])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * (rely)])

        # self.ax.draw_artist(self.axesImage)
        # for patch in self.ax.patches:
        #     self.ax.draw_artist(patch)
        
        self.canvas.draw_idle()

    def event_in_axes(self, event):
        return self.ax.contains(event)[0]

    def resetButtonCallback(self):
        """ Reset the zoom to original values. Show whole image. """
        self.ax.set_xlim(self.ori_xlim)
        self.ax.set_ylim(self.ori_ylim)
        self.canvas.draw()

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

        # update canvas and status block
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

    

    def updateStatus(self):
        self.dataStatStringVar.set(f'Data points: {len(self.data)}')
        self.cacheStringVar.set(f'Cached points: {len(self.history_list)}')

    def on_key(self, event):
        """ Keyboard shortcuts for undo (backspace) and reset zoom (space bar). """
        if event.key == "backspace":
            self.backwardButtonCallback()
        elif event.key == " ":
            self.resetButtonCallback()


root = tk.Tk()
app = mplApp(master=root)
app.pack()
app.mainloop()
