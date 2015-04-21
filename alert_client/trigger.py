import RPi.GPIO as GPIO
import subprocess
import time
import threading

import pygame
import pygame.camera

try:
	print("[A "+time.strftime("%H:%M:%S")+"] -> Starting Camera Interface")
	pygame.camera.init()
	cam = pygame.camera.Camera("/dev/video0",(1280,720))
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

	global detection
	last_detection=detection
	state=1
	webcam_capture=0
	webcam_capture_remaining=0

	while True:
		if(GPIO.input(7) != state and detection==1):
			if(state == 0):
				print("[A "+time.strftime("%H:%M:%S")+"] -> ALERT")
				for callb in callback_action:
					callb("state_change","alert")
				start = time.time()
				webcam_capture_remaining=5
			else:
				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to idle state")
				for callb in callback_action:
					callb("state_change","idle")

			state=GPIO.input(7)
		
		if(detection!=last_detection):
			print("detection change -> loop")
			if(detection==0):
				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to offline state")
				for callb in callback_action:
					callb("state_change","offline")
			else:
				state=-1 #to be refreshed by the part above
			last_detection=detection
			

		if(webcam_capture_remaining>0):
			path='alert'+str(webcam_capture_remaining)+'.jpg';
			webcam_capture=1
			webcam_capture_remaining-=1
		else:
			webcam_capture=0

		if(webcam_capture==1):
			img = cam.get_image()
			pygame.image.save(img,path)

			#s = subprocess.Popen(['fswebcam', '-r 1280x720 -S10 --tempstamp "%d-%m-%Y %H:%M:%S (%Z)" ', path],stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]			
			print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" taken")
			for callb in callback_action:
				callb("uploading",path)

	GPIO.cleanup()

def subscribe_callback(fun,method):
	if callback_action[0]==subscribe_callback:
		callback_action[0]=fun
	else:
		callback_action.append(fun)

def set_detection(state):
	global detection
	if(state=="on"):
		detection=1
		print("detection set to 1")
	else:
		print("detection set to 0")
		detection=0

callback_action=[subscribe_callback]
detection=1
