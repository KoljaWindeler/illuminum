import time
try:
	import quick2wire.i2c as i2c
except:
	print("Could not load the quickwire i2c lib, stopping")
	exit(0)

# upper line:		5V,	0 PWM,		1 PWM,		2 PWM,			3 PWM,			GND
# lower line		5V,	4 ADC,digital,	5 CHIP pinP7,	6 digital, ws2812,	7 digital, ws2812,	GND
# small smd pad  top next to avr:	Pin 8, digital, ws2812
# big smd pad  top next to terminal: 	Pin 9, digital, ws2812
# big smd pad  bottom next to terminal: Pin10, digital, ws2812
#######################################################################################################
#######################################################################################################
class Color:
	def __init__(self,red,green, blue):
		self.red=red
		self.green=green
		self.blue=blue
	def dimm(self, factor):
		self.red = int(self.red/factor)
		self.green = int(self.green/factor)
		self.blue = int(self.blue/factor)
	def copy(self, new):
		self.red = new.red
		self.green = new.green
		self.blue = new.blue
#######################################################################################################
#######################################################################################################	
	
class connection:
	# some constants
	START_BYTE 	= 0xCE
	CMD_SET  	= 0xF0
	CMD_CONFIG	= 0xF1
	CMD_GET		= 0xF2
	CMD_RESET	= 0xF3
	CMD_DIMM	= 0xF4
	CMD_PWM_FREQ 	= 0xF5
	CMD_TRIGGER_AFTER_SLEEP  = 0xF6

	MODE_PWM		= 0x01
	MODE_ANALOG_INPUT	= 0x02
	MODE_SINGLE_COLOR_WS2812= 0x03
	MODE_MULTI_COLOR_WS2812	= 0x04
	MODE_DIGITAL_INPUT	= 0x05
	MODE_DIGITAL_OUTPUT     = 0x06
	
	delay = 0.0 #10
	setup_delay = 0.0#100
	
######################################## constructor ##################################################
	def __init__(self, bus="", address="", warnings=1):
		if(bus==""):	
			# create connection
			self.bus = i2c.I2CMaster(1)
		else:
			self.bus = bus
		if(address==""):
			self.address = 0x04
		else:
			self.address = address
		self.warnings=warnings
		self.reset_config() # reset controller and vars
################################# prepare configuration and reset controller ##########################
	def reset_config(self):
		# reset avr and give some time for reboot
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_RESET))
		time.sleep(1)
		self.modes = [None] * 15
		self.ws2812count = [0] * 15
		return 0
################################# print warnings ######################################################
	def warn(self,text):
		if(self.warnings):
			print("Arduino bridge warning: "+text)
#######################################################################################################
######################################## SETUP #########################################################
################################### digital output ####################################################
	def setup_digital_output(self,pin):
		if(pin==5):
			self.warn("Digital output not supported on pin 5")
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_CONFIG, pin, self.MODE_DIGITAL_OUTPUT))	
		time.sleep(self.setup_delay)
		self.modes[pin]=self.MODE_DIGITAL_OUTPUT
		return 0
################################### pwm output ########################################################
	def setup_pwm_output(self,pin):
		# only pins 0-3,7,9
		if(pin>3 and pin!=7 and pin!=9):
			self.warn("PWM output only supported on pins 0,1,2,3,7,9")
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_CONFIG, pin, self.MODE_PWM))	
		time.sleep(self.setup_delay)
		self.modes[pin]=self.MODE_PWM
		return 0
################################## ws2812 control #####################################################
	def setup_ws2812_common_color_output(self,pin,count):
		return self.setup_ws2812_output(pin,count,self.MODE_SINGLE_COLOR_WS2812)
	def setup_ws2812_unique_color_output(self,pin,count,mode=MODE_SINGLE_COLOR_WS2812):
		return self.setup_ws2812_output(pin,count,self.MODE_MULTI_COLOR_WS2812)
	def setup_ws2812_output(self,pin,count,mode=MODE_SINGLE_COLOR_WS2812):
		# only pins 6-10
		if(pin==4 or pin==5 or pin==8 or pin==10 or pin==13 or pin==14):
			self.warn("ws2812 only supported on pins (0,1,2,3),6,7,9,11,12")
			return -1
		if(mode!=self.MODE_SINGLE_COLOR_WS2812 and mode!=self.MODE_MULTI_COLOR_WS2812):
			self.warn("invalid mode for ws2812 output")
			return -1
		if(count<=0):
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_CONFIG,  pin, mode, count))
		time.sleep(self.setup_delay)
		self.modes[pin]=mode
		self.ws2812count[pin]=count
		return 0
######################################## digital input ################################################
	def setup_digital_input(self,pin):
		# only pins 4,6,7
		if(pin!=4 and pin<6 and pin>10):
			self.warn("Digital output only supported on pins 4,6-12")
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_CONFIG, pin, self.MODE_DIGITAL_INPUT))	
		time.sleep(self.setup_delay)
		self.modes[pin]=self.MODE_DIGITAL_INPUT
		return 0
######################################### analog input ################################################
	def setup_analog_input(self,pin):
		# only pins 4
		if(pin!=4 and pin!=8 and pin!=10):
			self.warn("Analog input only supported on pins 4,8 and 10")
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_CONFIG, pin, self.MODE_ANALOG_INPUT))	
		time.sleep(self.setup_delay)
		self.modes[pin]=self.MODE_ANALOG_INPUT
		return 0
######################################### PWM frequency ################################################
	def setup_pwm_freq(self, pin, freq):
		# timer 0
		#[2]: 31250, 3906, 488, 122, 30,  // 1,8,64,256,1024 // untested pwm channel p2
		#[3]: 31250, 3906, 488, 122, 30,  // 1,8,64,256,1024 // untested pwm channel p3

		# timer 1
		#[1]: 15625, 1953, 244, 61, 15 // 1,2,3,4,5 // untested pwm channel p1
		#[0]: 15625, 1953, 244, 61, 15 // 1,2,3,4,5 // untested pwm channel p0

		# timer 2
		#[7]: 15625, 1953, 488, 244, 122, 61, 15 // 1,8,32,64,128,256,1024 // 1,2,3,4,5,6,7 // motor left tested
		#[9]: 15625, 1953, 488, 244, 122, 61, 15 // 1,8,32,64,128,256,1024 // 1,2,3,4,5,6,7 // motor right tested
		a_freq = []
		a_freq.append([15625,1953,244,61,15])
		a_freq.append([15625,1953,244,61,15])
		a_freq.append([31250,3906,488,122,30])
		a_freq.append([31250,3906,488,122,30])
		a_freq.append([])
		a_freq.append([])
		a_freq.append([])
		a_freq.append([15625,1953,488,244,122,61,15])
		a_freq.append([])
		a_freq.append([15625,1953,488,244,122,61,15])


		if(pin > len(a_freq) or pin <0):
			self.warn("pin not available for pwm manipulation")
			return -1
		elif(freq in a_freq[pin]):
			divisor = (a_freq[pin].index(freq))+1
		else:
			self.warn("Frequency not available. For this pin the following freq are possible: "+str(a_freq[pin]))
			return -1
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_PWM_FREQ, pin, divisor))
#######################################################################################################
######################################## SETUP #########################################################
#######################################################################################################


#######################################################################################################
######################################## USAGE ########################################################
####################################### set pin high or low ##############################################
	def digitalWrite(self,pin,value):
		if(self.modes[pin]!=self.MODE_PWM and self.modes[pin]!=self.MODE_ANALOG_INPUT and self.modes[pin]!=self.MODE_DIGITAL_OUTPUT and self.modes[pin]!=self.MODE_DIGITAL_INPUT):
			self.warn("pin "+str(pin)+" not configured for digital output, pwm output or analog input")
			self.warn("Please configure the pin accordingly")
			return -1
			
		if(value!=0 and value!=1):
			self.warn("Digital write only accepts input value 0 or 1")
			return -1
			
		if(self.modes[pin]==self.MODE_PWM):
			self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_SET, pin, 255*value))
		else:
			self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_SET, pin, value))
		time.sleep(self.delay)
		return 0
##################################### write analog value ##############################################
	def analogWrite(self,pin,value):
		return self.setPWM(pin,value)
	def setPWM(self,pin,value):
		if(self.modes[pin]!=self.MODE_PWM):
			self.warn("pin "+str(pin)+" not configured for pwm output")
			self.warn("Please configure the pin accordingly")
			return -1
		if(value<0 or value>255):
			self.warn("only values between 0 and 255 are valid")
			return -1
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_SET, pin, value))
		time.sleep(self.delay)
		return 0
	def dimmTo(self,pin,value,interval):
		if(self.modes[pin]!=self.MODE_PWM):
			self.warn("pin "+str(pin)+" not configured for pwm output")
			self.warn("Please configure the pin accordingly")
			return -1
		if(value<0 or value>100):
			self.warn("only values between 0 and 100 are valid, I will translate it to 0-255")
			return -1
		if(interval<1):
			self.warn("interval is defined in ms, value has to be >=1)")
			return -1
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_DIMM, pin, value, int(interval)))
		time.sleep(self.delay)
##################################### read digital value ##############################################
	def digitalRead(self,pin):
		if(self.modes[pin]!=self.MODE_DIGITAL_INPUT and self.modes[pin]!=self.MODE_ANALOG_INPUT ):
			self.warn("pin "+str(pin)+" not configured for digital input")
			self.warn("Please configure the pin accordingly")
			return -1
		if(self.modes[pin]==self.MODE_DIGITAL_INPUT):
			self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE,self.CMD_GET,pin))
			time.sleep(0.05)
			ret = self.bus.transaction(i2c.reading(self.address, 1))[0][0]
			time.sleep(self.delay)
			return ret
		else:
			if(analogRead(pin,avoid_mode_warning=1)>100): # >0.5V
				return 1
			else:
				return 0
#################################### read analog value ################################################
	def analogRead(self, pin, avoid_mode_warning=0):
		if(self.modes[pin]!=self.MODE_ANALOG_INPUT and avoid_mode_warning==0):
			self.warn("pin "+str(pin)+" not configured for analog input")
			self.warn("Please configure the pin accordingly")
			return -1
			
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE,self.CMD_GET,pin))
		time.sleep(0.05)
		analog_low, analog_high = self.bus.transaction(i2c.reading(self.address, 2))[0]
		time.sleep(self.delay)
		analog_value = analog_high<<8 | analog_low;
		return analog_value
################################### set ws2812 value ##################################################
	def ws2812set(self,pin,colors):
		if(self.modes[pin]!=self.MODE_MULTI_COLOR_WS2812 and self.modes[pin]!=self.MODE_SINGLE_COLOR_WS2812):
			self.warn("pin "+str(pin)+" not configured for ws2812 output")
			self.warn("Please configure the pin accordingly")
			return -1
			
		if(self.modes[pin]==self.MODE_SINGLE_COLOR_WS2812):
			if(not(isinstance(colors, Color))):
				self.warn("color argument is not of type 'Color'")
				return -1
			self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_SET, pin, colors.red, colors.green, colors.blue))
			time.sleep(self.delay)

		else:
			type_check=0
			if(isinstance(colors, list)):
				if(isinstance(colors[0], Color)):
					type_check=1
			if(not(type_check)):
				self.warn("color argument is not a list of Color")
				return -1
			if(len(colors)!=self.ws2812count[pin]):
				self.warn("you submitted "+str(len(colors))+" Colors, but "+str(self.ws2812count[pin])+" are required")
				return -1
			# ok, lets transmit, we have to send blocks of 8 LEDs or less
			for ii in range(0,self.ws2812count[pin]//8+1):
				msg = []
				msg.append(self.START_BYTE)
				msg.append(self.CMD_SET)
				msg.append(pin)
				msg.append(ii*8)
				for i in range(0,min(self.ws2812count[pin]-ii*8,8)):
					msg.append(colors[i+ii*8].red)
					msg.append(colors[i+ii*8].green)
					msg.append(colors[i+ii*8].blue)
				self.bus.transaction(i2c.writing(self.address,msg))
				time.sleep(self.delay)
		return 0
#################################### trigger Pin after Sleep ################################################
	# this shall wake the CHIP up after [sleeptime] seconds have passed by holding the [pin] up [or down if inverse is true]
	# for [holdtime] seconds, SALSA II connects P8 to the poweron button of the CHIP if the jumper is closed
	# [0] START_BYTE
	# [1] CMD_TRIGGER_AFTER_SLEEP
	# [2] Pin to trigger 
	# [3] hold down length in seconds for the first push
	# [4] hold down length in seconds for the second push
	# [5] low active
	# [6] wait time in sec until first push
	# [7] sleep SECONDS high byte for 2nd push
	# [8] sleep SECONDS low byte for 2nd push
		
	def triggerAfterSleep(self, pin=8, holdtime_1st=8, holdtime_2nd=2, wait_1st=10, wait_2nd=100, inverse=True):
		if(holdtime_1st>255):
			holdtime_1st=255
		if(holdtime_2nd>255):
			holdtime_2nd=255
		if(wait_1st>65535):
			wait_1st = 65535
		if(wait_2nd>65535):
			wait_2nd = 65535

		inverse_bit = 0;
		if(inverse):
			inverse_bit = 1;
		self.bus.transaction(i2c.writing_bytes(self.address, self.START_BYTE, self.CMD_TRIGGER_AFTER_SLEEP, pin, holdtime_1st, holdtime_2nd, inverse_bit, int(wait_1st), int(wait_2nd/256), int(wait_2nd%256)))
		time.sleep(self.delay)
		return 0
		
#######################################################################################################
######################################## USAGE ########################################################
#######################################################################################################

