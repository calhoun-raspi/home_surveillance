# import the necessary packages
from pyimagesearch.tempimage import TempImage
from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import numpy as np
import imutils
import json
import httplib
import time
import cv2

HOST = "127.0.0.1"
baseUrl = "api.parse.com"

# set color detection sensitivity
sensitivity = 15
# pixel detection parameters
lower_color_base = [0,0,255-sensitivity]
upper_color_base = [255,sensitivity,255]
# set a pixel number threshold
pixel_threshold = 10000

# @TODO: need to set up push notifications, either by figuring out how to do it in python or opening up a port to a C program.... This way, the website can push data to update the usage of dropbox and we can deal with that accordingly.

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
args = vars(ap.parse_args())
 
# filter warnings, load the configuration and initialize the Dropbox
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None

if conf["use_dropbox"]:
	# connect to dropbox and start the session authorization process
	flow = DropboxOAuth2FlowNoRedirect(conf["dropbox_key"], conf["dropbox_secret"])
	print "[INFO] Authorize this application: {}".format(flow.start())
	authCode = raw_input("Enter auth code here: ").strip()
 
	# finish the authorization and grab the Dropbox client
	(accessToken, userID) = flow.finish(authCode)
	client = DropboxClient(accessToken)
	print "[SUCCESS] dropbox account linked"

#create subtractor (no shadow - MOG, shadow - MOG2)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
fgbg = cv2.BackgroundSubtractorMOG()

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))
 
# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print "[INFO] warming up..."
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

# capture frames from the camera
for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image and initialize
	# the timestamp and occupied/unoccupied text
	frame = f.array
	timestamp = datetime.datetime.now()
	text = "Unoccupied"
 	
	# resize the frame
	frame = imutils.resize(frame, width=500)

	# capture a color sample (in hue, saturation, value space) of the frame for later object detection
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	# hard code color profile to detect (for now)
	lower_color = np.array(lower_color_base, dtype=np.uint8)
	upper_color = np.array(upper_color_base, dtype=np.uint8)
	# threshold the color
	mask = cv2.inRange(hsv, lower_color, upper_color)
	# Bitwise AND the mask and the original image
	resolve = cv2.bitwise_and(frame, frame, mask= mask)

	# convert frame to grayscale, and blur it for motion detection
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	#create fg mask
	fgmask = fgbg.apply(frame)
	fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
 
	# if the average frame is None, initialize it
	if avg is None:
		print "[INFO] starting background model..."
		avg = gray.copy().astype("float")
		rawCapture.truncate(0)
		continue
 
	# accumulate the weighted average between the current frame and
	# previous frames, then compute the difference between the current
	# frame and running average
	cv2.accumulateWeighted(gray, avg, 0.5)
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

	# threshold the delta image, dilate the thresholded image to fill
	# in holes, then find contours on thresholded image
	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
 
	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < conf["min_area"]:
			continue
 
		# compute the bounding box for the contour
		(x, y, w, h) = cv2.boundingRect(c)
		# count number of colored pixels
		count_pix = cv2.countNonZero(mask)
		# draw box on the frame, and update the text
		if count_pix >= pixel_threshold:
			cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
			text = "Occupied and detected" #could enumerate somewhere down the line to make more streamlined
		else:
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			text = "Occupied"
		
 
	# draw the text and timestamp on the frame
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)

	# check to see if the room is occupied
	if text == "Occupied" or text == "Occupied and detected":
		# check to see if enough time has passed between uploads
		if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
			# increment the motion counter
			motionCounter += 1
 
			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				# check to see if dropbox sohuld be used
				if conf["use_dropbox"]:
					# write the image to temporary file
					t = TempImage()
					cv2.imwrite(t.path, frame)
 
					# upload the image to Dropbox and cleanup the tempory image
					print "[UPLOAD] {}".format(ts)
					path = "{base_path}/{timestamp}.jpg".format(
						base_path=conf["dropbox_base_path"], timestamp=ts)
					client.put_file(path, open(t.path, "rb"))
					t.cleanup()
 
				# update the last uploaded timestamp and reset the motion
				# counter
				lastUploaded = timestamp
				motionCounter = 0
				print timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
				#make attempt to update on Parse the status of the motion detection
				connection = httplib.HTTPSConnection(baseUrl, 443)
				connection.connect()
				#change back to 'PUT' if handling specific object ID
				#put the timestamp in as a string?
				connection.request('POST', '/1/classes/Detect', json.dumps({
						"timestamp": timestamp.strftime("%A %d %B %Y %I:%M:%S%p"),
						"toDropBox": conf["use_dropbox"],
						"foundtarget": text == "Occupied and detected"
					}), {
						"X-Parse-Application-Id": "ajdBM8hNORYRg6VjxOnV1eZCCghujg7m12uKFzyI",
						"X-Parse-REST-API-Key": "27ck1BPviHwlEaINFOL08jh5zv1LFyY5CLOfvZvX",
						"Content-Type": "application/json"
					})
				results = json.loads(connection.getresponse().read())
				print results
 
	# otherwise, the room is not occupied
	else:
		motionCounter = 0

	# check to see if the frames should be displayed to screen
	if conf["show_video"]:
		# display the security feed
		cv2.imshow("Security Feed", frame)
		cv2.imshow("FG Mask",fgmask)
		#cv2.imshow('mask',mask)
		cv2.imshow('Resolved White',resolve)
		key = cv2.waitKey(1) & 0xFF
 
		# if the `q` key is pressed, break from the lop
		if key == ord("q"):
			break
 
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
