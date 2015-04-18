import RPi.GPIO as GPIO
import subprocess
import time
import threading

#******************************************************#
def start():
        threading.Thread(target = start_trigger, args = ()).start()
#******************************************************#
def start_trigger():
	#setup GPIO using Board numbering
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	state=1;
	webcam_capture=0
	webcam_capture_remaining=0

	while True:
		if(GPIO.input(7) != state):
			if(state == 0):
				print("pin went high")
				for callb in callback_action:
					callb("state_change","alert")
				start = time.time()
				webcam_capture_remaining=5
			else:
				print("pin went low")
				for callb in callback_action:
					callb("state_change","idle")

			state=GPIO.input(7)

		if(webcam_capture_remaining>0):
			path='alert'+str(webcam_capture_remaining)+'.jpg';
			webcam_capture=1
			webcam_capture_remaining-=1
		else:
			webcam_capture=0

		if(webcam_capture==1):
			s = subprocess.Popen(['fswebcam', '-r 1280x720 -S10 --tempstamp "%d-%m-%Y %H:%M:%S (%Z)" ', path],stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]			
			print('->file ready')
			for callb in callback_action:
				callb("uploading",path)
			print('->updated informing done')
			print("-->Call took "+str(time.time()-start))

	GPIO.cleanup()

def subscribe_callback(fun,method):
	if callback_action[0]==subscribe_callback:
		callback_action[0]=fun
	else:
		callback_action.append(fun)


callback_action=[subscribe_callback]
