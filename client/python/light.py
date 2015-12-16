import subprocess
import threading
import time
import RPi.GPIO as GPIO
import importlib

LED_DEBUG=0
with_neo=1
with_pwm=1

# import neopixel if posible
try:
	from neopixel import *
except:
	with_neo=0
	print("running without neopixel support")

# import pwm if posible
try:
	import wiringpi2 as wiringpi 
except:
	with_pwm=0
	print("running without pwm support")


class led:
	def __init__(self):
		self.s_r = 0		# start red
		self.s_g = 0		# start red
		self.s_b = 0		# start red
		self.s_t = 0		# start time

		self.c_r = 0		# current red 0-255, currently send to the pin
		self.c_g = 0		# current green 0-255, currently send to the pin
		self.c_b = 0		# current blue 0-255, currently send to the pin

		self.t_r = 0		# target red 0-255 when ever we call dimm_to
		self.t_g = 0		# target green 0-255 when ever we call dimm_to
		self.t_b = 0		# target blue 0-255 when ever we call dimm_to
		self.t_t = 0		# target time

		self.o_rd = 0		# place to save the old red (in 0-100), used to run "return_to_old()"
		self.o_gd = 0		# place to save the old green (in 0-100), used to run "return_to_old()"
		self.o_bd = 0		# place to save the old blue (in 0-100), used to run "return_to_old()"

		self.c_rd = 0		# place to save the current red (in 0-100),
		self.c_gd = 0		# place to save the current green (in 0-100)
		self.c_bd = 0		# place to save the current blue (in 0-100)

		self.d_r = 0		# storage for default red
		self.d_g = 0		# storage for default green
		self.d_b = 0		# storage for default blue

		self.ms_step = 0	# wait between two dimms
		self.state = 0		# not dimming
		self.last_ts = 0	# ts of last action

l = led()					# initialize one object of the class LED to have all vars set.

# LED strip configuration:
LED_COUNT      = 8      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor

light_dimming_q=[]
#******************************************************#
def start():
	# start a sub thread, runs the function start_light
	threading.Thread(target = start_light, args = ()).start()
#******************************************************#
def start_light():
	global l # use the object from above
	# Create NeoPixel object with appropriate configuration.
	if(with_neo):
		strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
		# Intialize the library (must be called once before other functions).
		strip.begin()
		strip.show()
	if(with_pwm):
		wiringpi.wiringPiSetupGpio()  
		wiringpi.pinMode(18,2)		


	while True:											# loop forever

		### ------------ check if we have something to do ------------ ###
		if(len(light_dimming_q) > 0):
			for data in light_dimming_q:
				if(data[0]<=time.time()):
					light_action=data
					light_dimming_q.remove(data)
					if(light_action[1]==-1 and light_action[2]==-1 and light_action[3]==-1):
						return_to_old(light_action[4])
					else:
						dimm_to(light_action[1],light_action[2],light_action[3],light_action[4])
		### ------------ check if we have something to do ------------ ###

		if(l.state==1):									# state= 1 means dimming is active
			if(time.time()>=l.last_ts+l.ms_step/1000):	# last_ts holds time of last event, ms_step the time between two dimm steps, if that sum is smaller than NOW - we have work
				l.last_ts=time.time()					# refresh last_ts to now
				differ_r=l.s_r-l.t_r					# caluclate the difference of each color between the start and the end color
				differ_g=l.s_g-l.t_g
				differ_b=l.s_b-l.t_b
				differ_time=(l.t_t-l.s_t)				# calulate the total time between the start and end (this should be the same as the "dimm time" specified by the user)
				if(differ_time>0):						# if the user set instant switch, this time will be 0. avoid division by zero
					ratio=(time.time()-l.s_t)/(l.t_t-l.s_t)	# ratio of the time that has passed, should be 0..1
				else:
					ratio=1
				if(ratio<1):							# if ratio is below 1 we are still in the middle of the dimming
					if(LED_DEBUG):
						print(".", end="")
					l.c_r=int(l.s_r-ratio*differ_r)		# refresh the r,g,b parts to the current dimm ratio (minus since we did a "l.s_r - l.t_r")
					l.c_g=int(l.s_g-ratio*differ_g)
					l.c_b=int(l.s_b-ratio*differ_b)

				else:									# ratio is bigger than one, time has passed, set it to target color
					l.c_r=int(l.t_r)
					l.c_g=int(l.t_g)
					l.c_b=int(l.t_b)
					l.state=0 							# stop further dimming
					if(LED_DEBUG):
						print("LED stop at "+str(time.time())+" "+str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b))


				l.c_r=max(min(255,l.c_r),0)				# avoid that we set a value bigger then 255 or smaller then 0
				l.c_g=max(min(255,l.c_g),0)
				l.c_b=max(min(255,l.c_b),0)

				#print(str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b))

				#strip.setPixelColor(0,Color(255,0,0))		# set value
				#strip.setPixelColor(1,Color(0,255,0))		# set value
				#strip.setPixelColor(2,Color(0,0,255))		# set value
				#strip.setPixelColor(3,Color(l.c_r,l.c_g,l.c_b))		# set value
				# neo pixel
				if(with_neo):
					for i in range(0,LED_COUNT):
						strip.setPixelColor(i,Color(l.c_r,l.c_g,l.c_b))		# set value
					strip.show()
				# pwm controll on pin 18
				if(with_pwm):
					wiringpi.pwmWrite(18, l.c_r*4)
					#rint(str(l.c_r*4))
				time.sleep(0.8*l.ms_step/1000) # we can wait here a little while because we know that nothing will happen for us earlier than that anyway

		else:
			time.sleep(0.01) # sleep to avoid 100% cpu



#******************************************************#
def return_to_old(ms):
	global l
	dimm_to(l.o_rd,l.o_gd,l.o_bd,ms)

def dimm_to(r,g,b,ms):
	global l
	intens=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,27,28,29,30,31,32,33,34,35,36,38,39,40,41,43,44,45,47,48,50,51,53,55,57,58,60,62,64,66,68,70,73,75,77,80,82,85,88,91,93,96,99,103,106,109,113,116,120,124,128,132,136,140,145,150,154,159,164,170,175,181,186,192,198,205,211,218,225,232,239,247,255]

	r=max(min(len(intens)-1,r),0) 			# just to make sure that we don't take an element outside the array 0-100
	g=max(min(len(intens)-1,g),0)
	b=max(min(len(intens)-1,b),0)

	l.t_r=intens[r]							# convert percentage to half-logarithmical brightness
	l.t_g=intens[g]
	l.t_b=intens[b]

	max_diff=max([abs(l.t_g-l.c_g),abs(l.t_r-l.c_r),abs(l.t_b-l.c_b)]) # find out what color has to do the most steps, this will determine the time between our single steps

	if(max_diff>0):							# just go on, if at least one has to change the color by at least one step
		l.o_rd=l.c_rd						# save current color as old
		l.o_gd=l.c_gd
		l.o_bd=l.c_bd

		l.c_rd=r							# target 0-100 color in the structure
		l.c_gd=g
		l.c_bd=b


		l.s_t=time.time()					# copy the starttime
		l.t_t=l.s_t+ms/1000					# set start time as starttime + time to dimm
		l.state=1 							# state 1 means dimming
		l.ĺast_ts=0							# last_ts=0 will result in instant execution of the first dimming step in the loop above
		l.ms_step=ms/max_diff				# calc the time between the dimming steps as total time / max steps
		#print("ms:"+str(ms)+" ms_step:"+str(l.ms_step))
		l.s_r = l.c_r						# set start color as current color
		l.s_g = l.c_g
		l.s_b = l.c_b
		if(LED_DEBUG):
			print("start at "+str(time.time())+" to "+str(l.c_r)+"/"+str(l.c_g)+"/"+str(l.c_b)+" -> "+str(l.t_r)+"/"+str(l.t_g)+"/"+str(l.t_b)+" within "+str(ms))
	#else:
	#	print("no reason")

def clear_q():
	for l in light_dimming_q:
		light_dimming_q.remove(l)
	return 0

def add_q_entry(when,r,g,b,duration_ms):
	light_dimming_q.append((when,r,g,b,duration_ms))
	return 0

def set_old_color(r,g,b,):
	l.o_rd=r
	l.o_gd=g
	l.o_bd=b
