from TSICam import camera
import time
import logging

logger = logging.getLogger(__name__)

class TSICam(camera.Camera):
    """Class for extending the functionality of the Camera class to provide a simple function
    for acquiring an image.
    """

    def __init__(self, SerNo):
        super().__init__(sn=SerNo)

    def acquire_single_image(self):
        """Triggers a single image acquisition. Returns image as numpy array.
        """
        logger.info("Capturing image...")
        self.single_acquisition()
        im = self.get_image()
        while im is None:
            time.sleep(0.1)
            im = self.get_image()
        logger.info("Image captured")
        return im
