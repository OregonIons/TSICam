#!/usr/bin/env python3

import argparse
import logging

from sipyco.pc_rpc import simple_server_loop
from sipyco import common_args

from TSICam import driver

logger = logging.getLogger(__name__)

class Cam():
    """
    Class for providing simple functionality of camera remotely.

    A Cam instance can be initialised using the desired serial number.
    If no serial number is specified, it connects to first listed camera.
    """

    def __init__(self, sn):
        self._connect(sn)

    def _connect(self, sn):
        self.camera = driver.TSICam(sn)

    def acq_single(self):
        """Acquires and returns a single image."""
        image = self.camera.acquire_single_image()
        return image

    def set_exposure(self, exp):
        """Sets the exposure in seconds."""
        logger.debug("Setting exposure to " + str(exp) + " seconds...")
        self.camera.set_exposure_time(exp)
        logger.info("Exposure set to " + str(exp) + " seconds")

    def get_exposure(self):
        """Returns the exposure in seconds."""
        logger.debug("Getting exposure...")
        exp = self.camera.get_exposure_params()[0] / 1000
        logger.info("Exposure is " + str(exp) + " seconds")
        return exp

    def close(self):
        """Closes connection to camera."""
        logger.debug("Closing connection to camera...")
        self.camera.close()
        logger.info("Connection to camera is closed")


def get_argparser():
    parser = argparse.ArgumentParser(description="""Thorlabs Camera controller.

    Use this controller for Thorlabs Scientific Imaging cameras.""")
    common_args.simple_network_args(parser, 3252)
    parser.add_argument("-d", "--device", default=None,
                        help="Camera serial number. Connects to first available camera if not used.")
    parser.add_argument("-e", "--exposure", default=None,
                        help="Exposure time in seconds. Defaults to minimum if not used.")
    common_args.verbosity_args(parser)
    return parser

def main():
    args = get_argparser().parse_args()
    common_args.init_logger_from_args(args)

    cam = Cam(args.device)
    if args.exposure:
        cam.set_exposure(float(args.exposure))
    
    try:
        logger.info("Camera open. Serving...")
        simple_server_loop({"camera": cam}, common_args.bind_address_from_args(args), args.port)
    finally:
        cam.close()

if __name__ == "__main__":
    main()