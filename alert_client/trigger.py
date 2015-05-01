import RPi.GPIO as GPIO
import subprocess
import time
import threading
import os
import io

import pygame
import pygame.camera

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

WIDTH=1280
HEIGHT=720
#WIDTH=640
#HEIGHT=480
TIMING_DEBUG=0
MS=1
m2m_state = ["idle","alert","disabled,idle","disabled,movement","error"]

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
		#f=ImageFont.load_default()
		#f=ImageFont.truetype("futureforces.ttf", 30)
		f=ImageFont.truetype("Sans.ttf", 20)


		global last_webcam_ts
		global webcam_interval
		global detection
		last_detection=detection
		state=-1 # to be refreshed
		webcam_capture_remaining=0
		busy=1
		webcam_ok=1

		while webcam_ok:
			# cpu spacing
			if(busy==0):
				time.sleep(0.1)
			busy=0
		
			# try to get the pin state
			try:
				gpio_state=GPIO.input(7)
			except:
				print("Trouble reading GPIO, restarting")
				break

			# changing the resolution - depr.
			if(change_res_event==1):
				print("changing resolution ("+str(cam_width)+"/"+str(cam_height)+")")
				change_res_event=0
				cam.stop()
				cam=pygame.camera.Camera("/dev/video0",(cam_width,cam_height))
				cam.start()
				
			# react on pin state change
			if(gpio_state != state):
				busy=1
				if(gpio_state == 1):
					if(detection==0):
						ex_state=3
					else:
						ex_state=1
						start = time.time()
						webcam_capture_remaining=5

				else:
					if(detection==0):
						ex_state=2
					else:
						ex_state=0

				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to state '"+m2m_state[ex_state]+"'")

				for callb in callback_action:
					callb("state_change",ex_state) 
	
				state=gpio_state

			elif(gpio_state == 1 and detection == 2): # the "send all photos until low mode"
				busy=1
				if(time.time()>last_webcam_ts+1):
					webcam_capture_remaining=1

		
			# set detection on / off
			if(detection!=last_detection):
				busy=1
				state=-1 #to be refreshed by the part above
				last_detection=detection
			
			# interval photos
			if(webcam_interval!=0):
				if(time.time()>last_webcam_ts+webcam_interval):
					webcam_capture_remaining=1
					#print("taking a snap")

			# capture photos!
			if(webcam_capture_remaining>0):
				busy=1
				l_last_webcam_ts=time.time()
				img_q=[]
				td=[]
				td.append((time.time(),"start"))

				# take as many shoots as in webcam_capture_remaining, place in buffer
				for i in range(0,webcam_capture_remaining):
					try:
						if(last_webcam_ts+5<=time.time()): # camera buffers two? frames, clear buffer
							cam.get_image()
							cam.get_image()
						img = cam.get_image()
					except:
						print("trouble to get a picture from the cam, restarting")
						webcam_ok=0
						break
	
					# to time dispaying
					td.append((time.time(),"snapping"))

					# saving to file
					if(state==1):
						path='alert'+str(i)+'.jpg';
					else:
						path='snap'+str(i)+'.jpg';
				
					# add the timestamp
					pil_string_image = pygame.image.tostring(img, "RGBA",False)
					img = Image.fromstring("RGBA",(cam_width,cam_height),pil_string_image)
				
					draw=ImageDraw.Draw(img)
					draw.text((6, 1),path+" /  "+time.strftime("%H:%M:%S"),(0,0,0),font=f)
					draw.text((5, 0),path+" /  "+time.strftime("%H:%M:%S"),(250,250,250),font=f)

					# timing debug
					td.append((time.time(),"processing"))

					# appending to save later
					img_q.append((img,path))

				# saveing
				for i in range(0,webcam_capture_remaining):
					#dequeueing
					img_de=img_q[0]
					img_q.remove(img_de)

					img=img_de[0]
					path=img_de[1]

					if(MS):
						img.save(path,"jpeg")
					else:
						# saving to stream
						b = io.BytesIO() 
						img.save(b, 'jpeg')
						img_bytes = b.getvalue()

					# timinig
					td.append((time.time(),"saving"))


					print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" taken")
					for callb in callback_action:
						if(MS):
							callb("uploading",(path,td))
						else:
							callb("uploading_str",(img_bytes,td))

				webcam_capture_remaining=0
				last_webcam_ts=l_last_webcam_ts

		GPIO.cleanup()

def subscribe_callback(fun,method):
	if callback_action[0]==subscribe_callback:
		callback_action[0]=fun
	else:
		callback_action.append(fun)

def set_detection(state):
	global detection
	detection=state
	print("[T "+time.strftime("%H:%M:%S")+"] detection set to "+str(state))

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
last_webcam_ts=0
callback_action=[subscribe_callback]
detection=0 # set to 1 for default, 0=off,1=send just the first 5 shoots if alert, 2=send all shoots as long as pin is HIGH
