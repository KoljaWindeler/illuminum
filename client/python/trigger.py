import RPi.GPIO as GPIO
import subprocess
import time,datetime
import threading
import os
import io

TIMING_DEBUG=1
STEP_DEBUG=0
m2m_state = ["idle","alert","disabled,idle","disabled,movement","error"]
det_state = ["off","on,single","on,permanent","error"]
img_q=[]

sensor_timeout=3
last_sensor_event=0
webcam_interval=0
change_det_event=0
#change_res_event=0
last_webcam_ts=0
callback_action=[""]
detection=0 # set to 1 for default, 0=off,1=send just the first 5 shoots if alert, 2=send all shoots as long as pin is HIGH
alias=""

high_res=0
webcam_capture_remaining=0
path=""

# this is how the photos travel:
# the server will tell us via "set interval" how often we should make a photo (at most)

# our main loop (start_trigger), will try to snap a picture with this interval.
# after SNAPPING the picture, the main loop will try to append it to img_q but will wait if there is more then 1
# picture in the queue

# the save_queue (different thread) will try to save the pictures (jpeg compressed) and will call the 
# the call backs for the clients thread to append the file. the client thread will return 1 if there is more then one img in his queue

# PERFORMANCE: snapping 	


#******************************************************#
def start():
		threading.Thread(target = start_trigger, args = ()).start()
#******************************************************#
def start_trigger():
	global change_det_event
	while True:

		#setup GPIO using Board numbering
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

		global last_webcam_ts
		global webcam_capture_remaining
		global webcam_interval
		global detection
		global img_q
		global alias
		global high_res
		global path
		state=-1 # to be refreshed
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

			# set detection on / off
			if(change_det_event):
				busy=1
				state=-1 #to be refreshed by the part below
				change_det_event=0
				
			# react on pin state change
			if(gpio_state != state and last_sensor_event<time.time()+sensor_timeout):
				last_sensor_event=time.time()
				state=gpio_state
				busy=1
				if(state == 1 and detection!=0): #alarm conditions
					start = time.time()
					webcam_capture_remaining=5
					high_res=1

				print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to state '"+m2m_state[state]+"' with detection '"+det_state[detection]+"'")

				for callb in callback_action:
					if(not(type(callb) is str)):
						callb("state_change",(state,detection))

			elif(gpio_state == 1 and detection == 2): # the "send all photos until low mode"
				busy=1
				if(time.time()>last_webcam_ts+1):
					webcam_capture_remaining=1

			
			# interval photos
			if(webcam_interval>0):
				high_res=0
				webcam_capture_remaining=1


			# capture photos!
			if(webcam_capture_remaining>0):
				busy=1
				add="SNAP"
				if(state==1 and detection>=1):
					path=str(int(time.time()*100) % 10000)+'alert'+str(webcam_capture_remaining)+'.jpg';
					add="ALERT"
				else:
					path=str(int(time.time()*100) % 10000)+'snap'+str(webcam_capture_remaining)+'.jpg';
						

		GPIO.cleanup()

def get_photo_state():
	global webcam_capture_remaining
	global high_res
	global path	

	webcam_capture_remaining_old=webcam_capture_remaining
	webcam_capture_remaining=max(webcam_capture_remaining-1,0)
	return ((webcam_capture_remaining_old,path,high_res))

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

