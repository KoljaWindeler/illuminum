import RPi.GPIO as GPIO
import subprocess
import time,datetime
import threading
import os
import io

WIDTH=1280
HEIGHT=720
TIMING_DEBUG=1
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


#******************************************************#
def start():
		threading.Thread(target = start_trigger, args = ()).start()
#******************************************************#
def start_trigger():
	global change_det_event
	while True:

		#setup GPIO using Board numbering
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
				if(time.time()>last_webcam_ts+0.1):
				#if(time.time()>last_webcam_ts+webcam_interval):
					webcam_capture_remaining=1
					#print("taking a snap")
					#webcam_interval=0 -> will turn of after one picture


			# capture photos!
			if(webcam_capture_remaining>0):
				busy=1
				l_last_webcam_ts=time.time()
				#img_q=[]
				td=[]
				td.append((time.time(),"start"))

				# take as many shoots as in webcam_capture_remaining, place in buffer
				for i in range(0,webcam_capture_remaining):
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
				
					td.append((time.time(),"loading"))

					print("[A "+time.strftime("%H:%M:%S")+"] -> Pic "+path+" saved")
					for callb in callback_action:
						# todo, if is not a function, skip
						while(callb("uploading",(path,td))): # the callback will return 1 if is more then one file in the queue
							if(STEP_DEBUG):
								print("[A "+time.strftime("%H:%M:%S")+"] Step 2.1. upload handle was not yet ready for "+path+", waiting 0.1sec")
							time.sleep(0.1) # give the upload process a little more cpu priority
						if(STEP_DEBUG):
							print("[A "+time.strftime("%H:%M:%S")+"] Step 3. passed image "+path+" to upload handle")

						
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

