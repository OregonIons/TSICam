# TSICam
ARTIQ support for Thorlabs Scientific Imaging cameras.

## Requirements
This package requires installation of Thorlabs Scientific Camera Interface.

It is recommended that the user install Revision G of the Scientific Camera Interface from [Thorlabs](https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam). The file is located under `Programming Interfaces -> Windows SDK and Doc. for Scientific Cameras`.

After installation, move the unzipped folder (called `Scientific_Camera_Interfaces-Rev_G`) to the appropriate path (`C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support` for Windows).

Then use pip to install the SDK to your environment:

`python -m pip install "C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific_Camera_Interfaces-Rev_G\Scientific Camera Interfaces\SDK\Python Compact Scientific Camera Toolkit\thorlabs_tsi_camera_python_sdk_package.zip"`

**Finally, the user must specify the Scientific Camera DLL folder path within the configure_path() function in the file `TSICam\tsi_library.py`.**

The folder path is usually `C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific_Camera_Interfaces-Rev_G\Scientific Camera Interfaces\SDK\Native Compact Camera Toolkit\dlls`. The software automatically selects the Native_32_lib or Native_64_lib folder, depending on your system.
