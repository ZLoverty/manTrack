manTrack
========

A python GUI software that makes modifying circle detection data easier. It allows (i) adding a circle by pressing and dragging and (ii) removing a circle by right-clicking.

Installation
------------
You can install the package via pip:

.. code-block:: bash

    pip install git+https://github.com/ZLoverty/manTrack.git

Usage
-----
To use the software, you can run the following command in your terminal:

.. code-block:: bash

    mantrack

You will see a window like this:

.. image:: ../../img/manTrack_doc_img.png
   :width: 600px
   :align: center


You need to load your image first, then load your preliminary circle detection data. In the draw area, you will see your image overlayed with the detected circles. You can then modify / correct the data by drawing and deleting. It is possible use middle button to zoom in and out. You can save the modified data by clicking the save button.

.. automodule:: manTrack