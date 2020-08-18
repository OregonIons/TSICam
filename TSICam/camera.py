from TSICam import tsi_library
import numpy as np
import ctypes
import collections
import time
import functools
import logging
from threading import Thread

logger = logging.getLogger(__name__)

class Camera:
    """
    Class for interfacing with a single Thorlabs Scientific Imaging (TSI) camera.

    A Camera instance can be initialised using the desired serial number.
    If no serial number is specified, it connects to first listed camera.

    The `get_image` function returns images from a frame buffer; in order to
    to have images in the buffer, either `start_acquisition` (which acquires
    images continuously) or `single_acquisition` must be called.

    Callbacks can be registered such that for every new frame acquired, the
    function is called, with the numpy array forming the image as the sole
    argument.
    """

    # Servo polling period in seconds
    _POLL_PERIOD = 0.05

    def __init__(self, sn=None, framebuffer_len=100):
        self.quit = False
        self.dead = False
        self.connected = False

        self.acquisition_enabled = False

        self.auto_exposure = False
        self.exposure = None
        self.exposure_min = None
        self.exposure_max = None
        self.exposure_inc = None

        self.frame_rate = 3.0 # set frame rate to 3fps

        self._frame_buffer = collections.deque([], framebuffer_len)
        self._frame_call_list = []

        # connect to camera library
        self._library_init()
        if sn is None:
            try:
                self._connect(self.c._cam_list[0])
            except Exception as e:
                self._library_cleanup()
                raise
        else:
            try:
                self._connect(sn)
            except Exception as e:
                self._library_cleanup()
                raise

        logger.debug("Starting image acquisition thread")
        t = Thread(target=self._acquisition_thread, daemon=True)
        t.start()

    def _library_init(self):
        self.c = tsi_library.TSI_Library()

    def _library_cleanup(self):
        del self.c

    def _connect(self, sn=None):
        id_ = 0
        for i in range(len(self.c._cam_list)):
            camera = self.c._cam_list[i]
            serial_no = camera
            if str(sn) in serial_no:
                if id_:
                    raise ValueError(
                        "Multiple substring matches for {}".format(sn))
                id_ = camera
        if sn is not None and id_ == 0:
            raise ValueError("Camera {} not found".format(sn))
        self.c.connect(id_)
        self._get_sensor_info()
        self._get_exposure_params()
        self._get_aoi()
        self._get_aoi_absolute()
        self.get_serial_no()

        self.connected = True # a camera is connected

    def _disconnect(self):
        self.c.disconnect()
        self.connected = False

    def _reconnect(self):
        self._disconnect()
        self._library_cleanup()
        self._library_init()
        self._connect(self._serial_no)

    def _acquisition_thread(self):
        while self.quit is False:
            if self.acquisition_enabled:
                try:
                    # print("waiting", flush=True)
                    im = self.c.acquire(native=True)
                    im = np.transpose(im)
                    # from here on in, the first axis of im is the x axis
                    # print("acquired!", flush=True)
                except:
                    logger.exception("Exception occurred, reconnecting")
                    self._reconnect()
                else:
                    im = self._crop_to_aoi(im)
                    self._frame_buffer.append(im.copy(order="C"))
                    for f in self._frame_call_list:
                        f(im)

                    # print("enabled {}".format(self.acquisition_enabled), flush=True)
                    # Update the exposure if necessary
                    if self.auto_exposure:
                        # print("try auto", flush=True)
                        self.handle_auto_exposure(im)

            # print("sleeping", flush=True)
            time.sleep(self._POLL_PERIOD)
            # print("slept", flush=True)
                
        self.dead = True

    def start_acquisition(self, single=False):
        """Turn on auto acquire"""

        def acquire_single_cb(_):
            """image is passed to callback and not used"""
            self.stop_acquisition()
            self.deregister_callback(acquire_single_cb)

        if single:
            self.register_callback(acquire_single_cb)

        self.acquisition_enabled = True

    def single_acquisition(self):
        """Single acquisition. Turns on auto acquire, and then turns it off after one acquisition."""
        self.start_acquisition(single=True)

    def stop_acquisition(self):
        """Turn off auto acquire"""
        self.acquisition_enabled = False

    def get_serial_no(self):
        """Return camera serial number"""
        info = self._get_cam_info()
        self._serial_no = info["SerNo"]
        return self._serial_no

    def _get_cam_info(self):
        cam_info = {"SerNo": self.c._sn, "Model": self.c._model}
        return cam_info

    def get_pixel_width(self):
        """Returns pixel width in microns. Only applicable to tsi cameras."""
        return self.c.get_pixel_width()

    def _get_frame_rate_params(self):
        self.frame_rate_min, self.frame_rate_max, \
            self.frame_rate_inc =  self.c.get_frame_rate_limits()

    def get_frame_rate_params(self):
        """Return current frame rate, minimum, maximum and increment values."""
        self._get_frame_rate_params()
        return self.frame_rate, self.frame_rate_min, self.frame_rate_max, self.frame_rate_inc

    def _get_exposure_params(self):
        self.exposure = self.c.get_exposure()
        self.exposure_min, self.exposure_max, \
            self.exposure_inc = self.c.get_exposure_limits()

    def get_exposure_params(self):
        """Return current exposure, minimum, maximum and increment values"""
        self._get_exposure_params()
        return self.exposure, self.exposure_min, self.exposure_max, self.exposure_inc

    def set_exposure_time(self, exposure_time):
        """Set the CCD exposure time in seconds."""
        time_ms = exposure_time * 1000
        self.set_exposure_ms(time_ms)

    def set_exposure_ms(self, exposure_time):
        """Set the camera exposure time in ms"""
        self.c.set_exposure(exposure_time)
        self.exposure = exposure_time

    def set_auto_exposure(self, auto_exposure):
        """Enable/disable auto exposure"""
        self.auto_exposure = auto_exposure

    def handle_auto_exposure(self, image):
        """Reads the most recent image and updates exposure"""
        # print("got to exposure handler", flush=True)
        pixel_max = np.amax(image)

        # print("autoexpose", flush=True)
        if pixel_max > auto_exposure_max_threshold:
            exposure = np.maximum(self.exposure*0.9, self.exposure_min)
            # if exposure == self.exposure:
                # print("warning: min exposure reached", flush=True)
            # print("reducing exposure", flush=True)
            self.set_exposure_ms(exposure)

        elif pixel_max < auto_exposure_min_threshold:
            exposure = np.minimum(self.exposure*1.1, self.exposure_max)
            # if exposure == self.exposure:
                # print("warning: max exposure reached", flush=True)
            # print("increasing exposure", flush=True)
            self.set_exposure_ms(exposure)

    def set_image_region(self, hStart, hEnd, vStart, vEnd, **kwargs):
        """Set the CCD region to read out.
        The region is 0 indexed and inclusive, so the valid ranges for hStart
        is 0 ... self.ccd_width - 1 etc."""
        if kwargs:
            print("binning is not supported")
        self.aoi_x = self._clip_to_grid(int(hStart), 0, self.ccd_width, 4)
        self.aoi_y = self._clip_to_grid(int(vStart), 0, self.ccd_height, 2)
        self.aoi_width = self._clip_to_grid(int(1+hEnd-hStart), 32,
                                            int(self.ccd_width-hStart), 4)
        self.aoi_height = self._clip_to_grid(int(1+vEnd-vStart), 4,
                                             int(self.ccd_height-vStart), 2)

        self._set_aoi(self.aoi_x, self.aoi_y, self.aoi_height, self.aoi_width)
        # exposure settings will change
        self._get_exposure_params()

    def _clip_to_grid(self, in_val, min_, max_, grid):
        out_val = np.clip(in_val, min_, max_)
        # integer maths does the rounding
        out_val = out_val // grid * grid
        return out_val

    def _set_aoi(self, posx, posy, width, height, absolute=True):
        """Set Area Of Interest according to Thorlabs spec
        If absolute is True, the memory location of the aoi within the image
        matches its actual position
        """
        self.c.set_roi(posx, posy, width, height)

    def _get_aoi(self):
        """Gets the aoi parameters, sets internal values and returns them"""
        rectAOI = self.c.get_roi()
        self.aoi_x = rectAOI.upper_left_x_pixels
        self.aoi_y = rectAOI.upper_left_y_pixels
        self.aoi_width = rectAOI.lower_right_x_pixels - rectAOI.upper_left_x_pixels
        self.aoi_height = rectAOI.lower_right_y_pixels - rectAOI.upper_left_y_pixels

        return self.aoi_x, self.aoi_y, self.aoi_width, self.aoi_height

    def _get_aoi_absolute(self):
        self.aoi_absolute = (self.c.get_sensor_size() == self.c.get_image_size())
        return self.aoi_absolute

    def _crop_to_aoi(self, image):
        """crop the image to the size of the aoi"""
        if self.aoi_width == self.ccd_width \
                and self.aoi_height == self.ccd_height:
            # shortcut for when the aoi is the whole sensor
            return image

        x_start = self.aoi_x if self.aoi_absolute else 0
        y_start = self.aoi_y if self.aoi_absolute else 0
        x_end = self.aoi_width + x_start
        y_end = self.aoi_height + y_start
        return image[x_start:x_end, y_start:y_end]

    def _get_sensor_info(self):
        self.ccd_width, self.ccd_height = self.c.get_sensor_size()
    
    def register_callback(self, f):
        """Register a function to be called from the acquisition thread for each
        new image"""
        self._frame_call_list.append(f)

    def deregister_callback(self, f):
        """Deregister a function to be called from the acquisition thread."""
        if f in self._frame_call_list:
            self._frame_call_list.remove(f)

    def get_image(self):
        """Returns the oldest image in the buffer as a numpy array, or None if
        no new images"""
        if len(self._frame_buffer) == 0:
            return None
        return self._frame_buffer.popleft()

    def get_all_images(self):
        """Returns all of the images in the buffer as an array of numpy arrays,
        or None if no new images"""
        if len(self._frame_buffer):
            ims = []
            while len(self._frame_buffer) > 0:
                ims.append(self._frame_buffer.popleft())
        else:
            ims = None
        return ims

    def ping(self):
        return True

    def close(self):
        """Disconnects from camera and cleans up library."""
        self.quit = True
        while not self.dead:
            time.sleep(0.01)
        self._disconnect()
        self._library_cleanup()

    def __del__(self):
        try:
            self.close()
        except AttributeError:
            # The library was already cleaned up
            pass
