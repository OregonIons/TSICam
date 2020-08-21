Welcome to TSICam's documentation!
==================================

General Instructions
--------------------

This software provides ARTIQ support for the Thorlabs Scientific Imaging cameras.

.. note::
    The software is intended for use with Thorlabs' Scientific Imaging and Compact Scientific Imaging cameras only.

Installation
++++++++++++

Install the TSICam package to your environment using pip with git::

    $ python -m pip install git+https://github.com/ARTIQ-Controllers/TSICam

Install Revision G of the Scientific Camera Interface from `Thorlabs <https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam>`_ . The file is located under `Programming Interfaces -> Windows SDK and Doc. for Scientific Cameras`.

After installation, move the unzipped folder (called ``Scientific_Camera_Interfaces-Rev_G``) to the appropriate path (``C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support`` for Windows).

Then use pip to install the SDK to your environment::

    $ python -m pip install "C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific_Camera_Interfaces-Rev_G\Scientific Camera Interfaces\SDK\Python Compact Scientific Camera Toolkit\thorlabs_tsi_camera_python_sdk_package.zip"

Finally, the user must specify the Scientific Camera DLL folder path within ``TSICam\tsi_library.py``.

For Windows, the folder path is usually ``C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific_Camera_Interfaces-Rev_G\Scientific Camera Interfaces\SDK\Native Compact Camera Toolkit\dlls``. The software automatically selects the ``Native_32_lib`` or ``Native_64_lib`` folder, depending on your system.

TSICam Controller Usage Example
+++++++++++++++++++++++++++++++

First, run the TSICam controller::

    $ aqctl_TSICam --bind ::1 -p 3252 -d 09423 -e 0.02

.. note::
    Arguments ``-d`` and ``-e`` are optional.
    
    The camera's serial number can be given in the ``-d`` argument. If nothing is given, the sofware will automatically connect to the first available TSI camera.

    The exposure time in seconds can be given in the ``-e`` argument. If nothing is given, the expsoure will be set to the camera's minimum value.

Then, send commands via the ``sipyco_rpctool`` utility::

    $ sipyco_rpctool ::1 3252 list-targets
    Target(s):   camera
    $ sipyco_rpctool ::1 3252 call acq_single() # will acquire and return a single image
    $ sipyco_rpctool ::1 3252 call set_exposure(0.01) # will set the exposure to 10ms
    $ sipyco_rpctool ::1 3252 call get_exposure() # will return the current exposure time in seconds
    $ sipyco_rpctool ::1 3252 call close() # will close connection to the camera

API
---

.. automodule:: TSICam.driver
    :members:


ARTIQ Controller
----------------

.. argparse::
    :ref: TSICam.aqctl_TSICam.get_argparser
    :prog: aqctl_TSICam

Acknowledgements
----------------

The driver file was largely adapted from: `https://github.com/OxfordIonTrapGroup/mjolnir <https://github.com/OxfordIonTrapGroup/mjolnir>`_ .

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
