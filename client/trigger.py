import RPi.GPIO as GPIO
import subprocess
import time,datetime
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
TIMING_DEBUG=0
STEP_DEBUG=0
m2m_state = ["idle","alert","disabled,idle","disabled,movement","error"]
det_state = ["off","on,single","on,permanent","error"]
img_q=[]

webcam_interval=0
change_det_event=0
#change_res_event=0
cam_width=WIDTH
cam_height=HEIGHT
last_webcam_ts=0
callback_action=[""]
detection=0 # set to 1 for default, 0=off,1=send just the first 5 shoots if alert, 2=send all shoots as long as pin is HIGH
alias=""


# this is how the photos travel:
# the server will tell us via "set interval" how often we should make a photo (at most)

# our main loop (start_trigger), will try to snap a picture with this interval.
# after SNAPPING the picture, the main loop will try to append it to img_q but will wait if there is more then 1
# picture in the queue

# the save_queue (different thread) will try to save the pictures (jpeg compressed) and will call the 
# the call backs for the clients thread to append the file. the client thread will return 1 if there is more then one img in his queue

# PERFORMANCE: snapping 	


def save_queue():
	while(1):
		if(len(img_q)>0):
			img_de=img_q[0]
			img_q.remove(img_de)

			img=img_de[0]
			path=img_de[1]
			td=img_de[2]
			if(STEP_DEBUG):
				print("[A "+time.strftime("%H:%M:%S")+"] Step 2. dequeueing "+path+" from img_q to save it to file")
			
			td.append((time.time(),"dequeue to save"))
			
			img.save(path,"jpeg",quality=75)

			# timinig
			td.append((time.time(),"saving"))

			print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" saved")
			for callb in callback_action:
				while(callb("uploading",(path,td))): # the callback will return 1 if is more then one file in the queue
					if(STEP_DEBUG):
						print("[A "+time.strftime("%H:%M:%S")+"] Step 2.1. upload handle was not yet ready for "+path+", waiting 0.1sec")
					time.sleep(0.1) # give the upload process a little more cpu priority
				if(STEP_DEBUG):
					print("[A "+time.strftime("%H:%M:%S")+"] Step 3. passed image "+path+" to upload handle")
		else:
			time.sleep(0.1) # avoid cpu load
			
	
		

#******************************************************#
def start():
		threading.Thread(target = start_trigger, args = ()).start()
		threading.Thread(target = save_queue, args = ()).start()
#******************************************************#
def start_trigger():
	while True:
		global cam_width
		global cam_heigh
		global change_res_event
		global change_det_event
	
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
		global img_q
		global alias
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
			#if(change_res_event==1):
			#	print("changing resolution ("+str(cam_width)+"/"+str(cam_height)+")")
			#	change_res_event=0
			#	cam.stop()
			#	cam=pygame.camera.Camera("/dev/video0",(cam_width,cam_height))
			#	cam.start()

			# set detection on / off
			if(change_det_event):
				busy=1
				state=-1 #to be refreshed by the part above
				change_det_event=0
				
			# react on pin state change
			if(gpio_state != state):
				state=gpio_state
				busy=1
				if(state == 1 and detection!=0): #alarm conditions
					start = time.time()
					webcam_capture_remaining=5

				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to state '"+m2m_state[state]+"' with detection '"+det_state[detection]+"'")

				for callb in callback_action:
					callb("state_change",(state,detection))

			elif(gpio_state == 1 and detection == 2): # the "send all photos until low mode"
				busy=1
				if(time.time()>last_webcam_ts+1):
					webcam_capture_remaining=1

			
			# interval photos
			if(webcam_interval>0):
				if(time.time()>last_webcam_ts+webcam_interval):
					webcam_capture_remaining=1
					#print("taking a snap")


			# capture photos!
			if(webcam_capture_remaining>0):
				busy=1
				l_last_webcam_ts=time.time()
				#img_q=[]
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
					add="SNAP"
					if(state==1 and detection>=1):
						path=str(int(time.time()*100) % 10000)+'alert'+str(i)+'.jpg';
						add="ALERT"
					else:
						path=str(int(time.time()*100) % 10000)+'snap'+str(i)+'.jpg';
						
					print("[A "+time.strftime("%H:%M:%S")+"] Picture taken "+path)
				
					# add the timestamp
					pil_string_image = pygame.image.tostring(img, "RGBA",False)
					img = Image.fromstring("RGBA",(cam_width,cam_height),pil_string_image)
				
					draw=ImageDraw.Draw(img)
					td.append((time.time(),"loading"))
					#draw.text((6, 1),path+" /  "+time.strftime("%H:%M:%S"),(0,0,0),font=f)
					#draw.text((5, 0),path+" /  "+time.strftime("%H:%M:%S"),(250,250,250),font=f)
					now=datetime.datetime.now().strftime("%H:%M:%S.%f")
					now=now[0:10]
					
					
					draw.text((6, 1),alias[0:20]+" /  "+add+" /  "+now,(0,0,0),font=f)
					draw.text((5, 0),alias[0:20]+" /  "+add+" /  "+now,(250,250,250),font=f)

					# timing debug
					td.append((time.time(),"processing"))

					# appending to save later
					while(len(img_q)>0): # only go on if there is no other file in the queue, but there will be still another file in saving process
						if(STEP_DEBUG):
							print("[A "+time.strftime("%H:%M:%S")+"] Step 1. We've snapped "+path+" to fast. there is more then one frame in the saving q, waiting 100ms")
						# this will cycle approximatly 3-4 times on a rpi 1 if user intervall is set to 0
						time.sleep(0.1)
					td.append((time.time(),"queue "+str(len(img_q)))) # tells us how many UNTOUCHED images are in the queue, there will be one more in the saving process 
					img_q.append((img,path,td))
						
				webcam_capture_remaining=0
				last_webcam_ts=l_last_webcam_ts

		GPIO.cleanup()

def subscribe_callback(fun,method):
	if callback_action[0]=="":
		callback_action[0]=fun
	else:
		callback_action.append(fun)

def set_detection(state):
	global change_det_event
	global detection
	change_det_event=1
	detection=state
	print("[T "+time.strftime("%H:%M:%S")+"] detection set to "+str(state))

def set_alias(new_alias):
	global alias
	alias=new_alias

def get_interval():
	global webcam_interval
	return webcam_interval

def set_interval(interval):
	global webcam_interval
	webcam_interval=interval
	#if(interval>0):
	#	change_res((1280,720))
		#change_res((640,480))
	#else:
	#	change_res((1280,720))
	
#def change_res(res):
#	global change_res_event
#	global cam_width
#	global cam_height
#	if(cam_width!=res[0] or cam_height!=res[1]):
#		change_res_event=1
#		cam_width=res[0]
#		cam_height=res[1]


##########################################

