import RPi.GPIO as GPIO
import subprocess
import time
import threading

import pygame
import pygame.camera

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

#WIDTH=1280
#HEIGHT=720
WIDTH=640
HEIGHT=480
TIMING_DEBUG=0

try:
	print("[A "+time.strftime("%H:%M:%S")+"] -> Starting Camera Interface")
	pygame.camera.init()
	cam = pygame.camera.Camera("/dev/video0",(WIDTH,HEIGHT))
	cam.start()
except:
	print("Could not start the Camera!")

#img = cam.get_image()
#pygame.image.save(img,"test"+str(a)+".jpg")


#******************************************************#
def start():
        threading.Thread(target = start_trigger, args = ()).start()
#******************************************************#
def start_trigger():
	#setup GPIO using Board numbering
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	global last_webcam_ts
	global webcam_interval
	global detection
	last_detection=detection
	state=-1 # to be refreshed
	webcam_capture=0
	webcam_capture_remaining=0

	while True:
		gpio_state=GPIO.input(7)
		if(gpio_state != state and detection==1):
			if(gpio_state == 1):
				print("[A "+time.strftime("%H:%M:%S")+"] -> ALERT")
				for callb in callback_action:
					callb("state_change",1) #alert
				start = time.time()
				webcam_capture_remaining=5
			else:
				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to idle state")
				for callb in callback_action:
					callb("state_change",0) #idle

			state=GPIO.input(7)
		
		if(detection!=last_detection):
			print("detection change -> loop")
			if(detection==0):
				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to offline state")
				for callb in callback_action:
					callb("state_change",2) # detection disabled
			else:
				state=-1 #to be refreshed by the part above
			last_detection=detection
		
		if(webcam_interval!=0):
			if(time.time()>last_webcam_ts+webcam_interval):
				path='snap.jpg'
				webcam_capture=1
				last_webcam_ts=time.time()
				print("taking a snap")

		if(webcam_capture_remaining>0):
			path='alert'+str(webcam_capture_remaining)+'.jpg';
			webcam_capture=1
			webcam_capture_remaining-=1

		if(webcam_capture==1):
			webcam_capture=0
			pic_start=time.time()

			#pygame img
			if(TIMING_DEBUG):
				pic_t = time.time()

			img = cam.get_image()

			#pillow
			if(TIMING_DEBUG):
				print("Snapping took "+str(time.time()-pic_t))
				pic_t = time.time()
			
			pil_string_image = pygame.image.tostring(img, "RGBA",False)
			img = Image.fromstring("RGBA",(WIDTH,HEIGHT),pil_string_image)
			
			draw=ImageDraw.Draw(img)
			f=ImageFont.load_default()
			draw.text((0, 0),path+" "+time.strftime("%H:%M:%S"),(10,10,10),font=f)

			if(TIMING_DEBUG):
				print("Processing took "+str(time.time()-pic_t))
				pic_t = time.time()

			img.save(path)

			if(TIMING_DEBUG):
				print("Saving took "+str(time.time()-pic_t))
				pic_t = time.time()

			print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" taken")
			for callb in callback_action:
				callb("uploading",(path,pic_start))

			if(TIMING_DEBUG):
				print("Spooling took "+str(time.time()-pic_t))

	GPIO.cleanup()

def subscribe_callback(fun,method):
	if callback_action[0]==subscribe_callback:
		callback_action[0]=fun
	else:
		callback_action.append(fun)

def set_detection(state):
	global detection
	if(str(state)=="1"):
		detection=1
		print("detection set to 1")
	else:
		print("detection set to 0")
		detection=0

def set_interval(interval):
	global webcam_interval
	if(interval!=0):
		webcam_interval=interval
	

webcam_interval=0
last_webcam_ts=time.time()
callback_action=[subscribe_callback]
detection=1
