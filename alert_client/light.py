import subprocess
import threading
import time
import RPi.GPIO as GPIO
from neopixel import *

class led: 
	def __init__(self):
		self.s_r = 0		# start red
		self.s_g = 0		# start red
		self.s_b = 0		# start red
		self.s_t = 0		# start time

		self.c_r = 0		# start red
		self.c_g = 0		# start red
		self.c_b = 0		# start red

		self.t_r = 0		# start red
		self.t_g = 0		# start red
		self.t_b = 0		# start red
		self.t_t = 0		# target time

		self.ms_step = 0	# wait between two dimms
		self.state = 0		# not dimming
		self.last_ts = 0	# ts of last action

l = led()

# LED strip configuration:
LED_COUNT      = 1      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor 


#******************************************************#
def start():
	threading.Thread(target = start_light, args = ()).start()
#******************************************************#
def start_light():
	global l
	# Create NeoPixel object with appropriate configuration.
	strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
	# Intialize the library (must be called once before other functions).
	strip.begin()
	strip.setPixelColor(0,Color(255,125,5))
	strip.show()

	
	while True:
		if(l.state==1):
			if(time.time()>=l.last_ts+l.ms_step/1000):
				l.last_ts=time.time()
				differ_r=l.s_r-l.t_r
				differ_g=l.s_g-l.t_g
				differ_b=l.s_b-l.t_b
				ratio=(time.time()-l.s_t)/(l.t_t-l.s_t)
				if(ratio<1):
					l.c_r=int(l.s_r-ratio*differ_r)
					l.c_g=int(l.s_g-ratio*differ_g)
					l.c_b=int(l.s_b-ratio*differ_b)

				else:
					l.c_r=int(l.t_r)
					l.c_g=int(l.t_g)
					l.c_b=int(l.t_b)
					l.state=0 #done
					#print("LED stop at "+str(time.time()))
	
				
				l.c_r=max(min(255,l.c_r),0)
				l.c_g=max(min(255,l.c_g),0)
				l.c_b=max(min(255,l.c_b),0)

				#print(str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b))

				strip.setPixelColor(0,Color(l.c_r,l.c_g,l.c_b))
				strip.show()
				time.sleep(0.8*l.ms_step/1000)

		else:
			time.sleep(0.2)
					

#******************************************************#
def dimm_to(r,g,b,ms):
	global l
	l.t_r=r
	l.t_g=g
	l.t_b=b
	l.s_t=time.time()
	l.t_t=l.s_t+ms/1000
	l.state=1 #dimm
	l.ĺast_ts=0
	l.ms_step=ms/max([abs(l.t_g-l.c_g),abs(l.t_r-l.c_r),abs(l.t_b-l.c_b)])
	#print("ms:"+str(ms)+" ms_step:"+str(l.ms_step))
	l.s_r = l.c_r
	l.s_g = l.c_g
	l.s_b = l.c_b
	#print("start at "+str(time.time()))
