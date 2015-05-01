import subprocess
import threading
import time
import RPi.GPIO as GPIO
from neopixel import *

LED_DEBUG=0

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

		self.o_rd = 0		# old red
		self.o_gd = 0		# old green
		self.o_bd = 0		# old blue
		self.c_rd = 0		# old red
		self.c_gd = 0		# old green
		self.c_bd = 0		# old blue

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
	strip.show()

	
	while True:
		if(l.state==1):
			if(time.time()>=l.last_ts+l.ms_step/1000):
				l.last_ts=time.time()
				differ_r=l.s_r-l.t_r
				differ_g=l.s_g-l.t_g
				differ_b=l.s_b-l.t_b
				differ_time=(l.t_t-l.s_t)
				if(differ_time>0):
					ratio=(time.time()-l.s_t)/(l.t_t-l.s_t)
				else:
					ratio=1
				if(ratio<1):
					if(LED_DEBUG):
						print(".", end="")
					l.c_r=int(l.s_r-ratio*differ_r)
					l.c_g=int(l.s_g-ratio*differ_g)
					l.c_b=int(l.s_b-ratio*differ_b)

				else:
					l.c_r=int(l.t_r)
					l.c_g=int(l.t_g)
					l.c_b=int(l.t_b)
					l.state=0 #done
					if(LED_DEBUG):
						print("LED stop at "+str(time.time())+" "+str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b))
	
				
				l.c_r=max(min(255,l.c_r),0)
				l.c_g=max(min(255,l.c_g),0)
				l.c_b=max(min(255,l.c_b),0)

				#print(str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b))

				strip.setPixelColor(0,Color(l.c_r,l.c_g,l.c_b))
				strip.show()
				time.sleep(0.8*l.ms_step/1000)

		else:
			time.sleep(0.01)



#******************************************************#
def return_to_old(ms):
	global l
	dimm_to(l.o_rd,l.o_gd,l.o_bd,ms)

def dimm_to(r,g,b,ms):
	global l
	intens=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,27,28,29,30,31,32,33,34,35,36,38,39,40,41,43,44,45,47,48,50,51,53,55,57,58,60,62,64,66,68,70,73,75,77,80,82,85,88,91,93,96,99,103,106,109,113,116,120,124,128,132,136,140,145,150,154,159,164,170,175,181,186,192,198,205,211,218,225,232,239,247,255]
	r=min(len(intens)-1,r)
	g=min(len(intens)-1,g)
	b=min(len(intens)-1,b)
	l.t_r=intens[r]
	l.t_g=intens[g]
	l.t_b=intens[b]
	max_diff=max([abs(l.t_g-l.c_g),abs(l.t_r-l.c_r),abs(l.t_b-l.c_b)])
	if(max_diff>0):
		#save current color as old
		l.o_rd=l.c_rd
		l.o_gd=l.c_gd
		l.o_bd=l.c_bd

		l.c_rd=r
		l.c_gd=g
		l.c_bd=b


		l.s_t=time.time()
		l.t_t=l.s_t+ms/1000
		l.state=1 #dimm
		l.ĺast_ts=0
		l.ms_step=ms/max_diff
		#print("ms:"+str(ms)+" ms_step:"+str(l.ms_step))
		l.s_r = l.c_r
		l.s_g = l.c_g
		l.s_b = l.c_b
		if(LED_DEBUG):
			print("start at "+str(time.time())+" to "+str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b)+" -> "+str(l.t_r)+"/"+str(l.t_g)+"/"+str(l.t_b)+" within "+str(ms))
	#else:
	#	print("no reason")
