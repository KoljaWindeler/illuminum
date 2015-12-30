import RPi.GPIO as GPIO
import time
import threading
import p

m2m_state = ["idle","alert","disabled,idle","disabled,movement","no pir","error"]
det_state = ["off","on,single","on,permanent","error"]

class Sensor:
	def __init__(self):
		self.last_triggered = 0
		self.timeout = 5
		self.state = 5
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
		p.rint("TRIGGER detection set to "+str(det_state[_detection]),"l")

#******************************************************#
class runner(threading.Thread):
	def __init__(self):
		self.alive = False
		self.s = Sensor()	# initialize one object of the class LED to have all vars set.


	def run(self,config):
		self.alive = True
		try:
			# sensor offline
			if(not(config.with_pir)):
				p.rint("TRIGGER: configured without PIR","l")
				self.s.state = 5

			# basic config 
			busy=1
			GPIO.setmode(GPIO.BOARD)
			GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			p.rint("TRIGGER: thread started","l")
			while self.alive:
		
				# cpu spacing
				if(busy==0):
					time.sleep(0.01)
				busy=0

				# try to get the pin state
				try:
					gpio_state=GPIO.input(7)
				except:
					p.rint("TRIGGER: Trouble reading GPIO, trying to reconfigure","d")
					break

				# set detection on / off
				if(self.s.state_change_event):
					self.s.state=-1 #to be refreshed by the part below	
					self.s.state_change_event=0
					self.s.last_triggered=0 # make sure the refresh happens fast

				# react on pin state change				
				if(gpio_state != self.s.state and self.s.last_triggered+self.s.timeout<time.time()):
					self.s.last_triggered=time.time()
					self.s.state=gpio_state
					busy=1

					p.rint("TRIGGER Switch to state '"+m2m_state[self.s.state]+"' with detection '"+det_state[self.s.detection]+"'","t")

					# call everyone who subscribed to our update list
					for callb in self.s.callback_action:
						if(not(type(callb) is str) and config.with_pir): # only call callbacks if we are configured with PIR
							try:
								callb("state_change",(self.s.state,self.s.detection))
							except:
								print("TRIGGER callback crashed")

			# while
		except:
			print("TRIGGER CRASHED")
		self.is_stop = True

		
	def stop(self):
		if(self.alive):
			self.alive = False
			self.is_stop = False
		else:
			self.is_stop = True 
#******************************************************#
r = runner()

def start(config):
	threading.Thread(target = r.run, args = ([config]) ).start()

def stop():
	r.stop()
	while(not(r.is_stop)):
		time.sleep(0.1)

def restart(config):
	stop()
	start(config)

def set_detection(_detection):
	r.s.set_detection(_detection)

def subscribe_callback(_fun):
	r.s.subscribe_callback(_fun)
