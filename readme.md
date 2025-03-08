# manTrack

A python GUI software that makes modifying particle tracking data easier. It allows (i) adding a particle by drawing on the image and (ii) removing a particle by clicking on the image.

## Installation

Download this repository to `/your/local/path`. Run the source `.py` code in the `src/` folder using

```console
pip install git+https://github.com/ZLoverty/manTrack.git
```

## Usage

Once installed, manTrack can be called from the command line by

```console
mantrack
```

You can download an image (.jpg) and a data file (.csv) [here](https://drive.google.com/uc?export=download&id=1Ab8dnfNad1QvCRg3-iIH7z-K973zvsUt) to test the software. 

### Load image and data

Click "Load" button to load an image, and "Load data" button to load preliminary particle tracking data (.csv file).

### Draw particles on image

Click "Draw data" button to plot particles on top of the image. 

### Delete particle

Click "Delete mode" to enter delete mode, then click on the particle on the image panel to remove it.

Note: at this point, the delete is only saved temporarily. Once you confirm the removal, click the "Merge data" button and use "Save data" button to save the modified particle tracking data as .csv file. 

![delete](/img/delete.gif)

### Track particle

Here by "track", I mean adding particle data to current data file. To do this, click "Track mode" button to enter track mode, then in the image panel, hold mouse left button at one end of an ellipse long axis and release at the other end. A new ellipse will be drawn and data will be recorded temporarily.
Similar to delete mode, you need to use "Merge data" to confirm the modification to the data from file.

![tracking](/img/tracking.gif)

### Mono/color plot

By default, all the particles are drawn in green color. I provide another representation, where the orientations of the ellipses are denoted by color. You can switch between color/mono plot by clicking "Color/Mono plot" button.

![color](/img/color.gif)