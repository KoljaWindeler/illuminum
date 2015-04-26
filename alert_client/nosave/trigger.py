import RPi.GPIO as GPIO
import subprocess
import time
import threading
import os

import pygame
import pygame.camera

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

WIDTH=1280
HEIGHT=720
#WIDTH=640
#HEIGHT=480
TIMING_DEBUG=1



#******************************************************#
def start():
        threading.Thread(target = start_trigger, args = ()).start()
#******************************************************#
def start_trigger():
	while True:
		global cam_width
		global cam_heigh
		global change_res_event
	
		try:
			print("[A "+time.strftime("%H:%M:%S")+"] -> Starting Camera Interface ("+str(cam_width)+"/"+str(cam_height)+")")
			os.system('v4l2-ctl -d 0 -c focus_auto=1')
			os.system('v4l2-ctl -d 0 -c contrast=1')
			os.system('v4l2-ctl -d 0 -c saturation=83')
			os.system('v4l2-ctl -d 0 -c sharpness=25')
			os.system('v4l2-ctl -d 0 -c brightness=130')
			os.system('v4l2-ctl -d 0 -c white_balance_temperature_auto=1')
			pygame.camera.init()
			cam = pygame.camera.Camera("/dev/video0",(cam_width,cam_height))
			cam.start()
		except:
			print("Could not start the Camera!")

		#setup GPIO using Board numbering
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		#font
		f=ImageFont.load_default()


		global last_webcam_ts
		global webcam_interval
		global detection
		last_detection=detection
		state=-1 # to be refreshed
		webcam_capture=0
		webcam_capture_remaining=0
		busy=1

		while True:
			# cpu spacing
			if(busy==0):
				time.sleep(0.1)
			busy=0
		
			try:
				gpio_state=GPIO.input(7)
			except:
				print("Trouble reading GPIO, restarting")
				break

			if(change_res_event==1):
				print("changing resolution ("+str(cam_width)+"/"+str(cam_height)+")")
				change_res_event=0
				cam.stop()
				cam=pygame.camera.Camera("/dev/video0",(cam_width,cam_height))
				cam.start()
				
			if(gpio_state != state and detection==1):
				busy=1
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
				busy=1
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
					#print("taking a snap")

			if(webcam_capture_remaining>0):
				path='alert'+str(webcam_capture_remaining)+'.jpg';
				webcam_capture=1
				webcam_capture_remaining-=1

			if(webcam_capture==1):
				busy=1
				webcam_capture=0
				last_webcam_ts=time.time()
				pic_start=time.time()
	
				#pygame img
				if(TIMING_DEBUG):
					pic_t = time.time()

				try:
					img = cam.get_image()
				except:
					print("trouble to get a picture from the cam, restarting")
					break
	
				#pillow
				if(TIMING_DEBUG):
					print("Snapping took "+str(time.time()-pic_t))
					pic_t = time.time()
			
				pil_string_image = pygame.image.tostring(img, "RGBA",False)
				img = Image.fromstring("RGBA",(cam_width,cam_height),pil_string_image)
				
				draw=ImageDraw.Draw(img)
				draw.text((0, 0),path+" "+time.strftime("%H:%M:%S"),(10,10,10),font=f)

				if(TIMING_DEBUG):
					print("Processing took "+str(time.time()-pic_t))
					pic_t = time.time()

				img_str=img.tostring()
				#img.save(path)

				if(TIMING_DEBUG):
					print("Saving took "+str(time.time()-pic_t))
					pic_t = time.time()

				print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" taken")
				for callb in callback_action:
					#callb("uploading",(path,pic_start))
					callb("uploading_str",(img_str,pic_start,path))

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
	webcam_interval=interval
	if(interval>0):
		change_res((1280,720))
		#change_res((640,480))
	else:
		change_res((1280,720))
	
def change_res(res):
	global change_res_event
	global cam_width
	global cam_height
	if(cam_width!=res[0] or cam_height!=res[1]):
		change_res_event=1
		cam_width=res[0]
		cam_height=res[1]


##########################################
webcam_interval=0
change_res_event=0
cam_width=WIDTH
cam_height=HEIGHT
last_webcam_ts=time.time()
callback_action=[subscribe_callback]
detection=0 # set to 1 for default
