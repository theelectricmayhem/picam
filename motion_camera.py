
from picamera.array import PiRGBArray
from picamera import PiCamera, exc
from numpy import zeros, uint8
import cv2
import datetime


class MotionCamera:
    def __init__(self, frame_width=640, frame_height=480, resize_width=512, resize_height=288, rotation=0,
                 frames_per_second=16, delta_threshold=5, minimum_motion_percent=0.25, minimum_motion_frames=3):
        self.FRAME_WIDTH = frame_width
        self.FRAME_HEIGHT = frame_height
        self.RESIZE_WIDTH = resize_width
        self.RESIZE_HEIGHT = resize_height
        self.ROTATION = rotation
        self.FPS = frames_per_second
        self.DELTA_THRESHOLD = delta_threshold
        self.MIN_MOTION_AREA = int(frame_width * frame_height * minimum_motion_percent)
        print("MIN_MOTION_AREA: ", self.MIN_MOTION_AREA)
        self.MIN_MOTION_FRAMES = minimum_motion_frames
        self.camera = None
        self.init_camera()
        # self.camera = PiCamera(resolution=(frame_width, frame_height), framerate=frames_per_second)
        # self.camera.rotation = rotation
        self.raw_capture = PiRGBArray(self.camera, size=self.camera.resolution)
        self.frame = zeros((self.FRAME_WIDTH, self.FRAME_HEIGHT, 3), uint8)
        self.resized = []
        self.blurred = []
        self.background = None
        self.motion_frames = 0
        self.contours = []
        self.rectangles = []
        self.save_count = 0
        self.motion_center = 0

    def init_camera(self):
        try:
            self.camera = PiCamera(resolution=(self.FRAME_WIDTH, self.FRAME_HEIGHT), framerate=self.FPS)
            self.camera.rotation = self.ROTATION
        except exc.PiCameraError as error:
            return error
        return

    def grabFrame(self):
        self.raw_capture.truncate(0)
        try:
            self.camera.capture(self.raw_capture, format="bgr", use_video_port=True)
        except exc.PiCameraError as error:
            return error
        self.frame = self.raw_capture.array
        return

    def initBackground(self):
        try:
            self.grabFrame()
        except exc.PiCameraError as error:
            return error
        self.resized = cv2.resize(self.frame, (self.RESIZE_WIDTH, self.RESIZE_HEIGHT), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(self.resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (25, 25), 0)
        self.blurred = gray
        self.background = gray.copy().astype("float")
        # print("background initialized")
        return

    def singleMotionDetector(self):
        return

    def detectMotion(self):
        self.rectangles = []
        self.raw_capture.truncate(0)

        try:
            self.camera.capture(self.raw_capture, format="bgr", use_video_port=True)
        except exc.PiCameraRuntimeError as error:
            return error
        except exc.PiCameraValueError as error:
            return error

        self.frame = self.raw_capture.array
        self.resized = cv2.resize(self.frame, (self.RESIZE_WIDTH, self.RESIZE_HEIGHT), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(self.resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.background is None:
            # print("[INFO] starting background model...")
            self.background = gray.copy().astype("float")
            return

        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        cv2.accumulateWeighted(gray, self.background, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.background))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frame_delta, self.DELTA_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        self.contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = self.contours[0]  # Just grab the first one for simplicity

        motion = False

        # loop over the contours
        for c in self.contours:

            if cv2.contourArea(c) < self.MIN_MOTION_AREA:  # if the contour is too small, ignore it
                continue
            motion = True   # if it's not too small, then we have enough motion to count it

            # compute the bounding box for the contour
            rect = cv2.boundingRect(c)
            self.rectangles.append(rect)
            # (x, y, w, h) = rect
            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        self.raw_capture.truncate(0)

        # Update the number of motion frames observed
        if motion:
            # increment motion_frames, cap at 2 times MIN_MOTION_FRAMES
            if self.motion_frames >= (2 * self.MIN_MOTION_FRAMES):
                self.motion_frames = 2 * self.MIN_MOTION_FRAMES
            else:
                self.motion_frames += 1
        else:  # no motion, decrement the counter
            if self.motion_frames > 0:
                self.motion_frames -= 1
            else:
                self.motion_frames = 0

        return

    def drawContours(self):
        cv2.drawContours(self.resized, self.contours, -1, (255, 0, 255), 1)

    def drawRectangles(self):
        for rect in self.rectangles:
            cv2.rectangle(self.resized, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (255, 0, 255), 1)
        return

    def saveFrame(self, resize=False, path="./images/", filename_format=""):
        timestamp = datetime.datetime.now()

        if filename_format == "":
            filename = timestamp.strftime("%Y%m%d-%H.%M.%S.%f") + '.jpg'
        else:
            filename = timestamp.strftime(filename_format) + '.jpg'

        if resize:
            cv2.imwrite(path + filename, self.resized)
        else:
            cv2.imwrite(path + filename, self.frame)

        self.save_count = self.save_count + 1
        return

    def addTimestamp(self, resize=False):
        timestamp = datetime.datetime.now()
        text = timestamp.strftime("%Y %m %d %H:%M:%S:%f")
        if resize:
            cv2.putText(self.resized, text, org=(10, self.frame.shape[0] - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5, color=(0, 0, 255))
        else:
            cv2.putText(self.frame, text, org=(10, self.frame.shape[0] - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=1, color=(0, 0, 255))
        return

    def __del__(self):
        # print("Motion frames saved: ", self.save_count)
        if self.camera:
            self.camera.close()
        return


