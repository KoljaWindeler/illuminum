import RPi.GPIO as GPIO
import time
import threading

m2m_state = ["idle","alert","disabled,idle","disabled,movement","error"]
det_state = ["off","on,single","on,permanent","error"]


class Sensor:
	def __init__(self):
		self.last_triggered = 0
		self.timeout = 5
		self.state = -1
		self.detection = 0
		self.state_change_event = 0
		self.callback_action=[""]

	def subscribe_callback(self,fun):
		if self.callback_action[0]=="":
			self.callback_action[0]=fun
		else:
			self.callback_action.append(fun)

	def set_detection(self,_detection):
		self.state_change_event=1
		self.detection=_detection
		print("[T "+time.strftime("%H:%M:%S")+"] detection set to "+str(det_state[_detection]))

s = Sensor()					# initialize one object of the class LED to have all vars set.

#******************************************************#
def start():
	threading.Thread(target = start_trigger, args = ()).start()

#******************************************************#
def start_trigger():
	global s

	while 1:
		busy=1
		#setup GPIO using Board numbering
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

		while 1:
			# cpu spacing
			if(busy==0):
				time.sleep(0.01)
			busy=0

			# try to get the pin state
			try:
				gpio_state=GPIO.input(7)
			except:
				print("Trouble reading GPIO, trying to reconfigure")
				break

			# set detection on / off
			if(s.state_change_event):
				s.state=-1 #to be refreshed by the part below
				s.state_change_event=0
				s.last_triggered=0 # make sure the refresh happens fast

			# react on pin state change
			if(gpio_state != s.state and s.last_triggered+s.timeout<time.time()):
				s.last_triggered=time.time()
				s.state=gpio_state
				busy=1

				#print("[A "+time.strftime("%H:%M:%S")+"] -> Switch to state '"+m2m_state[s.state]+"' with detection '"+det_state[s.detection]+"'")

				# call everyone who subscribed to our update list
				for callb in s.callback_action:
					if(not(type(callb) is str)):
						callb("state_change",(s.state,s.detection))

		GPIO.cleanup()
