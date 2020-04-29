# import the necessary packages
import logging as log
import motion_camera
import persec
import argparse
import json
import time
import cv2
import os
import gpio_handler
import sys

# make the file location the current working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", default="conf.json", required=False, help="path to the JSON configuration f")
args = vars(ap.parse_args())

# load the configuration file
conf = json.load(open(args["conf"]))

# set up logging
log.basicConfig(level=log.INFO, format='%(asctime)s  %(filename)s :%(levelname)s: %(message)s')
log.info("picam.py starting...")

# set up the GPIO for the door switch
log.info("Initializing GPIO...")
gpio = gpio_handler.GPIOHandler()
gpio.setPullUp(conf["door_switch_pin"])

# Tracking for number of frames read per second
frame_counter = persec.PerSec("Frames Evaluated")
error_counter = persec.PerSec("Errors Encountered")
save_counter = persec.PerSec("Frames Saved")

# initialize the camera
motion = None
log.info("Initializing camera...")
try:
    motion = motion_camera.MotionCamera(frame_width=tuple(conf["resolution"])[0],
                                        frame_height=tuple(conf["resolution"])[1],
                                        resize_width=tuple(conf["resize"])[0],
                                        resize_height=tuple(conf["resize"])[1],
                                        rotation=conf["rotation"],
                                        frames_per_second=conf["fps"],
                                        delta_threshold=conf["delta_thresh"],
                                        minimum_motion_percent=conf["min_motion_percent"],
                                        minimum_motion_frames=conf["min_motion_frames"])
except Exception as error:
    log.error(type(error))
    exit()

# allow the camera to warmup
log.info("Camera warming up...")
time.sleep(conf["camera_warmup_time"])
log.info("Starting main loop...")

while True:
    # If the door is open, wait until it is closed
    if gpio.pinStatus(conf["door_switch_pin"]) != 0:
        continue

    return_value = motion.detectMotion()
    if return_value:
        # Something went wrong with the camera interface
        log.error(type(return_value))
        error_counter.update()
        log.error("Attempting to reinitialize camera...")
        try:        # try to close out the camera interface
            motion.camera.close()
        except Exception as error:  # didn't work.  Time to die
            log.error(type(return_value))
            log.critical("Unable to close camera interface.  Exiting.")
            sys.exit()

        try:  # try to initialize a new camera interface
            motion.init_camera()
        except Exception as error:  # didn't work.  Time to die
            log.error(type(return_value))
            log.critical("Unable to initialize a new camera interface.  Exiting.")
            sys.exit()

        log.error("New camera interface up and running")
        continue
    frame_counter.update()

    if motion.motion_frames >= conf["min_motion_frames"]:
        # seen enough motion, capture the frame
        motion.addTimestamp()
        motion.saveFrame()
        save_counter.update()

    # check to see if the frames should be displayed to screen
    if conf["show_video"]:
        # display the security feed
        motion.drawContours()
        cv2.imshow("Front Door", motion.resized)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key is pressed, break from the loop
        if key == ord("q"):
            motion.__del__()
            break
