"""
manTrack.py
===========

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

Sep 16, 2024:

1. Rewrite the code to use pyqtgraph instead of matplotlib. This allows for more interactive plotting and better performance.

2. Rename to manTrack.py, use as the main program for manual tracking.

Sep 18, 2024: show file name.

Mar 08, 2025: Package as a module to simplify the setup process. 
"""

import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import pandas as pd
import numpy as np
from skimage import io
from pathlib import Path

class CircleAnnotationApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.createVars()

    def initUI(self):
        self.setWindowTitle('Circle Annotation Tool')
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        self.mainWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.mainWidget)
        self.layout = QtWidgets.QHBoxLayout(self.mainWidget)

        # Create control panel
        self.controlPanel = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.controlPanel, 1)

        # Create plot area with CustomViewBox
        self.plotWidget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plotWidget, 4)
        self.plotItem = self.plotWidget.addPlot(viewBox=CustomViewBox(self))
        self.plotItem.invertY(True)
        self.plotItem.setAspectLocked(True)

        # Add buttons to control panel
        self.loadImageButton = QtWidgets.QPushButton('Load Image')
        self.loadImageButton.clicked.connect(self.loadImage)
        self.controlPanel.addWidget(self.loadImageButton)

        self.loadDataButton = QtWidgets.QPushButton('Load Data')
        self.loadDataButton.clicked.connect(self.loadData)
        self.controlPanel.addWidget(self.loadDataButton)

        self.saveDataButton = QtWidgets.QPushButton('Save Data')
        self.saveDataButton.clicked.connect(self.saveData)
        self.controlPanel.addWidget(self.saveDataButton)

        self.undoButton = QtWidgets.QPushButton('Undo')
        self.undoButton.clicked.connect(self.undo)
        self.undoButton.setEnabled(False)
        self.controlPanel.addWidget(self.undoButton)

        self.resetZoomButton = QtWidgets.QPushButton('Reset Zoom')
        self.resetZoomButton.clicked.connect(self.resetZoom)
        self.controlPanel.addWidget(self.resetZoomButton)

        # Status labels
        self.dataStatLabel = QtWidgets.QLabel('Data points: 0')
        self.controlPanel.addWidget(self.dataStatLabel)

        self.cacheLabel = QtWidgets.QLabel('Cached points: 0')
        self.controlPanel.addWidget(self.cacheLabel)

        self.plotItemsLabel = QtWidgets.QLabel('Plot items: 0')
        self.controlPanel.addWidget(self.plotItemsLabel)

        self.circlesLabel = QtWidgets.QLabel('Circles: 0')
        self.controlPanel.addWidget(self.circlesLabel)

        self.fileNameLabel = QtWidgets.QLabel('No file loaded', self)
        self.controlPanel.addWidget(self.fileNameLabel)

        # Connect plot events
        self.plotItem.scene().sigMouseMoved.connect(self.onMouseMove)
        self.plotItem.scene().sigMouseClicked.connect(self.onMousePress)

    def createVars(self):
        self.data = pd.DataFrame(columns=['x', 'y', 'r'])
        self.history_list = []
        self.currentCircle = None
        self.imageItem = None
        self.circles = []

    def loadImage(self):
        img_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Image", "", "Image Files (*.png *.jpg *.tif)")
        if img_path:
            img = io.imread(img_path)
            img = np.fliplr(img)  # Flip the image left-to-right
            img = np.rot90(img)  # Rotate the image by 90 degrees
            self.imageItem = pg.ImageItem(img)
            self.plotItem.addItem(self.imageItem)
            self.plotItem.setAspectLocked(True)
            self.plotItem.autoRange()
            self.fileNameLabel.setText(f'Loaded file: {Path(img_path).name}')

    def loadData(self):
        data_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Data", "", "CSV Files (*.csv);;Excel Files (*.xls *.xlsx)")
        if data_path:
            if data_path.endswith('.csv'):
                self.data = pd.read_csv(data_path)
            else:
                self.data = pd.read_excel(data_path)
            self.updateCircles()

    def saveData(self):
        data_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv)")
        if data_path:
            self.data.to_csv(data_path, index=False)

    def undo(self):
        if self.history_list:
            action, circle = self.history_list.pop()
            if action == 'add':
                self.data = self.data.drop(circle['index'])
                # remove the circle from the plot
           
                self.plotItem.removeItem(circle['item'])
            elif action == 'delete':
                new_row = pd.DataFrame({'x': [circle['data']['x']], 'y': [circle['data']['y']], 'r': [circle['data']['r']]})
                self.data = pd.concat([self.data, new_row], ignore_index=True)
                self.plotItem.addItem(circle['item'])
            self.updateStatus()
            self.undoButton.setEnabled(bool(self.history_list))

    def resetZoom(self):
        self.plotItem.autoRange()

    def onMousePress(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            pos = event.scenePos()
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            x, y = mousePoint.x(), mousePoint.y()
            self.currentCircle = {'x': x, 'y': y, 'r': 0}
            self.x0 = x
            self.y0 = y
        elif event.button() == QtCore.Qt.RightButton:
            pos = event.scenePos()
            items = self.plotItem.scene().items(pos)
            for item in items:
                if isinstance(item, QtWidgets.QGraphicsEllipseItem):
                    self.removeCircle(item)
                    break

    def onMouseRelease(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.currentCircle is not None:
            # Remove the temporary circle item
            if 'item' in self.currentCircle:
                self.plotItem.removeItem(self.currentCircle['item'])
            self.addCircle(self.currentCircle)
            self.currentCircle = None
        # QtCore.pyqtRemoveInputHook()
        # pdb.set_trace()

    def onMouseMove(self, pos):
        if self.currentCircle is not None:
            mousePoint = self.plotItem.vb.mapSceneToView(pos)
            x, y = mousePoint.x(), mousePoint.y()
            r = np.sqrt((x - self.currentCircle['x'])**2 + (y - self.currentCircle['y'])**2)
            if 'item' in self.currentCircle:
                self.plotItem.removeItem(self.currentCircle['item'])
            self.currentCircle['x'] = (x + self.x0) / 2
            self.currentCircle['y'] = (y + self.y0) / 2
            self.currentCircle['r'] = r
            self.currentCircle['item'] = self.createCircleItem(self.currentCircle, color="g")
            self.plotItem.addItem(self.currentCircle['item'])

    def addCircle(self, circle):
        index = self.data.index.max() + 1
        circle['index'] = index
        circle['item'] = self.createCircleItem(circle, color="g")
        new_row = pd.DataFrame({'x': [circle['x']], 'y': [circle['y']], 'r': [circle['r']]}, index=[index])
        self.data = pd.concat([self.data, new_row])
        self.plotItem.addItem(circle['item'])
        self.history_list.append(('add', circle))
        self.undoButton.setEnabled(True)
        self.updateStatus()

    def removeCircle(self, item):
        for index, row in self.data.iterrows():
            if row['x'] == item.rect().x() + row['r'] and row['y'] == item.rect().y() + row['r']:
                self.data = self.data.drop(index)
                self.plotItem.removeItem(item)
                self.history_list.append(('delete', {'data': row, 'item': item}))
                self.updateStatus()
                self.undoButton.setEnabled(True)
                break

    def createCircleItem(self, circle, color="r"):
        pen = pg.mkPen(color=color, width=2)
        ellipse = QtWidgets.QGraphicsEllipseItem(circle['x'] - circle['r'], circle['y'] - circle['r'], 2 * circle['r'], 2 * circle['r'])
        ellipse.setPen(pen)
        return ellipse

    def updateCircles(self):
        self.circles = []
        for index, row in self.data.iterrows():
            circle = self.createCircleItem({'x': row['x'], 'y': row['y'], 'r': row['r']})
            self.plotItem.addItem(circle)
            self.circles.append(circle)
        self.updateStatus()

    def updateStatus(self):
        self.dataStatLabel.setText(f'Data points: {len(self.data)}')
        self.cacheLabel.setText(f'Cached points: {len(self.history_list)}')
        self.plotItemsLabel.setText(f'Plot items: {len(self.plotItem.items)}')
        self.circlesLabel.setText(f'Circles: {len(self.circles)}')

class CustomViewBox(pg.ViewBox):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.mouseMode = self.RectMode  # Start with no specific mouse mode
        self.setMouseMode(self.mouseMode)  # Default mode

    def setMouseMode(self, mode):
        self.mouseMode = mode

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.setMouseMode(self.PanMode)  # Enable panning with middle mouse button
        elif event.button() == QtCore.Qt.LeftButton:
            self.setMouseMode(self.RectMode)
            self.parent.onMousePress(event)
        elif event.button() == QtCore.Qt.RightButton:
            self.setMouseMode(self.RectMode)
            self.parent.onMousePress(event)
        # Prevent default behavior in rect mode
        if self.mouseMode == self.RectMode:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.setMouseMode(self.RectMode)  # Disable panning after releasing middle mouse button
        elif event.button() == QtCore.Qt.LeftButton:
            self.parent.onMouseRelease(event)
        elif event.button() == QtCore.Qt.RightButton:
            event.accept()
        # Prevent default behavior in rect mode
        if self.mouseMode == self.RectMode:
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MiddleButton:
            super().mouseMoveEvent(event)  # Default panning behavior
        elif event.buttons() == QtCore.Qt.LeftButton:
            pos = event.scenePos()
            self.parent.onMouseMove(pos)
def run():
    app = QtWidgets.QApplication(sys.argv)
    ex = CircleAnnotationApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()