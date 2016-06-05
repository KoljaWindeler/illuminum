import subprocess
import threading
import time
import p

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

		self.o_rd = 0		# place to save the old red (in 0-255), used to run "return_to_old()"
		self.o_gd = 0		# place to save the old green (in 0-255), used to run "return_to_old()"
		self.o_bd = 0		# place to save the old blue (in 0-255), used to run "return_to_old()"
		self.o_lifetime = 0	# placeholder until when this color is valid

		self.c_rd = 0		# place to save the current red (in 0-100),
		self.c_gd = 0		# place to save the current green (in 0-100)
		self.c_bd = 0		# place to save the current blue (in 0-100)

		self.d_r = 0		# storage for default red
		self.d_g = 0		# storage for default green
		self.d_b = 0		# storage for default blue

		self.ms_step = 0	# wait between two dimms
		self.state = 0		# not dimming
		self.last_ts = 0	# ts of last action

LED_DEBUG=0
neo_support=1
pwm_support=1
i2c_support=1

# import neopixel if posible
try:
	from neopixel import *
except:
	neo_support=0
# import pwm if posible
try:
	import wiringpi2 as wiringpi 
except:
	pwm_support=0
# import i2c if posible
try:
	import quick2wire.i2c as i2c
except:
	i2c_support=0


#####################################################
class illumination(threading.Thread):
	def __init__(self,pwm_support,neo_support,i2c_support):
		# LED strip configuration:
		self.neo_LED_COUNT      = 8      # Number of LED pixels.
		self.neo_LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
		self.neo_LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
		self.neo_LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
		self.neo_LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
		self.neo_LED_INVERT     = False   # True to invert the signal (when using NPN transistor

		self.l = led()			# initialize one object of the class LED to have all vars set.
		self.light_dimming_q=[]
		self.neo_support = neo_support
		self.i2c_support = i2c_support
		self.pwm_support = pwm_support
		self.neo_loaded=0
		self.i2c_loaded=0
		self.alive = False

	#******************************************************#
	def run(self,config):		
		self.config = config

		while(1):
			p.rint("LIGHT, thread started","l")
			self.alive = True


			# Create NeoPixel object with appropriate configuration.
			if(str(self.config.with_lights) == "1"):
				p.rint("LIGHT, configured with NEO usage","l")
				if(self.neo_support and self.neo_loaded!=1):
					p.rint("LIGHT, neopixel supported, starting","l")
					strip = Adafruit_NeoPixel(self.neo_LED_COUNT, self.neo_LED_PIN, self.neo_LED_FREQ_HZ, self.neo_LED_DMA, self.neo_LED_INVERT, self.neo_LED_BRIGHTNESS)
					# Intialize the library (must be called once before other functions).
					strip.begin()
					strip.show()
					self.neo_loaded = 1 	# avoid loading it twice
				elif(self.neo_support):
					p.rint("LIGHT, neopixel already loaded","l")
				else:
					p.rint("LIGHT, ERROR neopixel not supported","l")
			elif(str(self.config.with_lights) == "2"):
				p.rint("LIGHT, configured with PWM usage","l")
				if(self.pwm_support):
					p.rint("LIGHT, PWM supported, starting","l")
					wiringpi.wiringPiSetupPhys()
					wiringpi.pinMode(12,2)
				else:
					p.rint("LIGHT, ERROR PWM not supported","l")
			elif(str(self.config.with_lights) == "3"  and self.i2c_loaded!=1):
				p.rint("LIGHT, configured with i2c usage","l")
				if(self.i2c_support):
					p.rint("LIGHT, i2c supported, starting","l")
					bus = i2c.I2CMaster(1)
					self.i2c_loaded = 1
				else:
					p.rint("LIGHT, ERROR PWM not supported","l")
			else:
				p.rint("LIGHT, started without pwm and neo","l")

			while self.alive:
				### ------------ check if we have something to do ------------ ###
				if(len(self.light_dimming_q) > 0):
					for data in self.light_dimming_q:
						if(data[0]<=time.time()):
							light_action=data
							self.light_dimming_q.remove(data)
							if(light_action[1]==-1 and light_action[2]==-1 and light_action[3]==-1):
								self.return_to_old(light_action[4])
							else:
								self.dimm_to(light_action[1],light_action[2],light_action[3],light_action[4])
				### ------------ check if we have something to do ------------ ###

				if(self.l.state==1):						# state= 1 means dimming is active
					if(time.time()>=self.l.last_ts+self.l.ms_step/1000):	# last_ts holds time of last event, ms_step the time between two dimm steps, 
											# if that sum is smaller than NOW - we have work
						self.l.last_ts=time.time()			# refresh last_ts to now
						differ_r=self.l.s_r-self.l.t_r			# caluclate the difference of each color between the start and the end color
						differ_g=self.l.s_g-self.l.t_g
						differ_b=self.l.s_b-self.l.t_b
						differ_time=(self.l.t_t-self.l.s_t)		# calulate the total time between the start and end 
											#(this should be the same as the "dimm time" specified by the user)
						if(differ_time>0):			# if the user set instant switch, this time will be 0. avoid division by zero
							ratio=(time.time()-self.l.s_t)/(self.l.t_t-self.l.s_t)	# ratio of the time that has passed, should be 0..1
						else:
							ratio=1
						if(ratio<1):				# if ratio is below 1 we are still in the middle of the dimming
							if(LED_DEBUG):
								print(".", end="")
							self.l.c_r=int(self.l.s_r-ratio*differ_r)	# refresh the r,g,b parts to the current dimm ratio (minus since we did a "self.l.s_r - self.l.t_r")
							self.l.c_g=int(self.l.s_g-ratio*differ_g)
							self.l.c_b=int(self.l.s_b-ratio*differ_b)

						else:					# ratio is bigger than one, time has passed, set it to target color
							self.l.c_r=int(self.l.t_r)
							self.l.c_g=int(self.l.t_g)
							self.l.c_b=int(self.l.t_b)
							self.l.state=0 			# stop further dimming
							if(LED_DEBUG):
								print("LED stop at "+str(time.time())+" "+str(self.l.c_r)+"/"+str(self.l.c_g)+"/"+str(self.l.c_b))


						self.l.c_r=max(min(255,self.l.c_r),0)		# avoid that we set a value bigger then 255 or smaller then 0
						self.l.c_g=max(min(255,self.l.c_g),0)
						self.l.c_b=max(min(255,self.l.c_b),0)

						# neo pixel
						if(str(self.config.with_lights) == "1" and self.neo_support):
							for i in range(0,self.neo_LED_COUNT):
								strip.setPixelColor(i,Color(self.l.c_r,self.l.c_g,self.l.c_b))		# set value
							strip.show()
						# neo pixel
						# pwm controll on pin 12
						elif(str(self.config.with_lights) == "2" and self.pwm_support):
							wiringpi.pwmWrite(12, self.l.c_r*4)
						# pwm controll on pin 12
						# i2c controll
						elif(str(self.config.with_lights) == "3" and self.i2c_support):
							try:
								address = 0x04
								pin_r = 0x03
								pin_g = 0x04
								pin_b = 0x05
								bus.transaction(i2c.writing_bytes(address, 0x09, pin_r, 0x09, 0x01, 0x09, self.l.c_r))
								bus.transaction(i2c.writing_bytes(address, 0x09, pin_g, 0x09, 0x01, 0x09, self.l.c_g))
								bus.transaction(i2c.writing_bytes(address, 0x09, pin_b, 0x09, 0x01, 0x09, self.l.c_b))
							except:
								print("LIGHT i2c bus transaction crashed")
						# i2c controll

						# we can wait here a little while because we know that nothing will happen for us earlier than that anyway
						time.sleep(0.8*self.l.ms_step/1000) 		

				else:
					time.sleep(0.01) # sleep to avoid 100% cpu
				# while
		p.rint("LIGHT, thread stopped","l")
		
	#******************************************************#
	def reload_config(self,config):
		self.config = config
		self.alive = False

	#******************************************************#
	def return_to_old(self,ms):
		if(self.l.o_lifetime>time.time()):
			p.rint("LIGHT return_to_old, goto backup color cause lifetime is "+str(self.l.o_lifetime-time.time()),"r")
			self.add_q_entry(time.time(),self.l.o_rd,self.l.o_gd,self.l.o_bd,ms)	# first move back to old color as it is still valid
			self.add_q_entry(self.l.o_lifetime,0,0,0,ms)				# remember to turn off at some point
		else:
			p.rint("LIGHT return_to_old, goto 0/0/0 lifetime is over","r")
			self.add_q_entry(time.time(),0,0,0,ms)					# return to nothing, as the old color is not valid, turn off

	#******************************************************#
	def dimm_to(self,r,g,b,ms):
		p.rint("LIGHT, dimming to "+str(r)+"/"+str(g)+"/"+str(b),"r")
		# selection is 0-255 based, but it really means 0-100%
		######## calculate target value 0-255 (half-log) out of the input value 0-255 (linear) #######
		_r=r/2.55
		_g=g/2.55
		_b=b/2.55

		intens=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,27,28,29,30,31,32,33,34,35,36,38,39,40,41,43,44,45,47,48,50,51,53,55,57,58,60,62,64,66,68,70,73,75,77,80,82,85,88,91,93,96,99,103,106,109,113,116,120,124,128,132,136,140,145,150,154,159,164,170,175,181,186,192,198,205,211,218,225,232,239,247,255]

		_r=int(max(min(len(intens)-1,_r),0)) 			# just to make sure that we don't take an element outside the array 0-100
		_g=int(max(min(len(intens)-1,_g),0))
		_b=int(max(min(len(intens)-1,_b),0))

		self.l.t_r=intens[_r]							# convert percentage to half-logarithmical brightness
		self.l.t_g=intens[_g]
		self.l.t_b=intens[_b]
		######## calculate target value 0-255 (half-log) out of the input value 0-255 (linear) #######

		max_diff=max([abs(self.l.t_g-self.l.c_g),abs(self.l.t_r-self.l.c_r),abs(self.l.t_b-self.l.c_b)]) # find out what color has to do the most steps, this will determine the time between our single steps

		if(max_diff>0):							# just go on, if at least one has to change the color by at least one step
			self.l.o_rd=self.l.c_rd						# save current color as old
			self.l.o_gd=self.l.c_gd
			self.l.o_bd=self.l.c_bd

			self.l.c_rd=r						# current target linear 0-255 color in the structure
			self.l.c_gd=g
			self.l.c_bd=b


			self.l.s_t=time.time()					# copy the starttime
			self.l.t_t=self.l.s_t+ms/1000					# set start time as starttime + time to dimm

			self.l.state=1 							# state 1 means dimming
			self.l.ĺast_ts=0							# last_ts=0 will result in instant execution of the first dimming step in the loop above
			self.l.ms_step=ms/max_diff				# calc the time between the dimming steps as total time / max steps
			#print("ms:"+str(ms)+" ms_step:"+str(self.l.ms_step))
			self.l.s_r = self.l.c_r						# set start color as current color
			self.l.s_g = self.l.c_g
			self.l.s_b = self.l.c_b
			p.rint("LIGHT start at "+str(time.time())+" to "+str(self.l.c_r)+"/"+str(self.l.c_g)+"/"+str(self.l.c_b)+" -> "+str(self.l.t_r)+"/"+str(self.l.t_g)+"/"+str(self.l.t_b)+" within "+str(ms),"r")
		#else:
		#	print("no reason")
	#******************************************************#
	def clear_q(self):
		for l in self.light_dimming_q:
			self.light_dimming_q.remove(l)
		return 0
	#******************************************************#
	def add_q_entry(self,when,r,g,b,duration_ms):
		self.light_dimming_q.append((when,r,g,b,duration_ms))
		return 0
	#******************************************************#
	def set_color(self,r,g,b):
		self.l.d_r=r
		self.l.d_g=g
		self.l.d_b=b
	#******************************************************#
	def get_color(self):
		return((self.l.d_r,self.l.d_g,self.l.d_b))
	#******************************************************#
	def set_old_color(self,r,g,b,lifetime):
		p.rint("LIGHT setting old color "+str(r)+"/"+str(g)+"/"+str(b)+" in "+str(lifetime-time.time())+" sec","r")
		self.l.o_rd=r
		self.l.o_gd=g
		self.l.o_bd=b
		self.l.o_lifetime = lifetime
	#******************************************************#
#####################################################

runner = illumination(pwm_support,neo_support,i2c_support)
t=""
def start(config):
	t=threading.Thread(target = runner.run, args = ([config]))
	t.start()
	#print("start preusdo")

def stop():
	runner.stop()
	#t.join()
	a=0
	while(not(runner.is_stop) and a<100):
		time.sleep(0.1)
		a=a+1
	if(not(runner.is_stop)):
		print("could not stop the thread")

def restart(config):
	if(runner.alive):
		#rint("runner was alive, running reload_config")
		runner.reload_config(config)
	else:
		#rint("runner was NOT alive, running start")
		start(config)

def set_old_color(r,g,b,lifetime):
	runner.set_old_color(r,g,b, lifetime) # lifetime is a timestamp

def add_q_entry(when,r,g,b,duration_ms):
	p.rint("LIGHT, add_q_entry: setting color "+str(r)+"/"+str(g)+"/"+str(b)+" in "+str(when-time.time())+" sec from now","r")
	runner.add_q_entry(when,r,g,b,duration_ms)

def clear_q():
	runner.clear_q()

def dimm_to(r,g,b,ms):
	runner.dimm_to(r,g,b,ms)

def return_to_old(ms):
	runner.return_to_old(ms)

def set_color(r,g,b):
	runner.set_color(r,g,b)

def get_delay_off():
	delay_off = 5*60 # usually 5 min
	off_time = get_time()+delay_off
	if(off_time > 22*60*60 or (off_time%86400) < 6*60*60): # switch off after 22h and before 6
		delay_off = 30 # just 30 sec
	return delay_off

def get_time():
	return time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
