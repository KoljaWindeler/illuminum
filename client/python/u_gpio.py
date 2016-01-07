import time
import p

rpi_support  = 1
fsys_support = 1

# import rpi gpio if posible
try:
	import RPi.GPIO as GPIO
except:
	rpi_support = 0

# import fsys if posible
try:
	import asdf as GPIO 
except:
	fsys_support = 0


class u_gpio:

	def __init__(self):
		self.PIN_PIR 		= 1
		self.PIN_MOVEMENT 	= 2
		self.PIN_DETECTION 	= 3
		self.PIN_USER 		= 4
		self.PIN_CAM 		= 5
	

	def setup(self):
		if(rpi_support):
			p.rint("configuring raspberry pins","g")
			GPIO.setwarnings(False)
			GPIO.setmode(GPIO.BOARD)

			self.PIN_PIR 		= 7
			self.PIN_MOVEMENT 	= 11	
			self.PIN_DETECTION 	= 13
			self.PIN_USER 		= 15
			self.PIN_CAM 		= 16

			GPIO.setup(self.PIN_PIR, 		GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(self.PIN_MOVEMENT, 		GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(self.PIN_DETECTION, 		GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(self.PIN_USER, 		GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			GPIO.setup(self.PIN_CAM, 		GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

	def set(self,pin,level):
		if(level==0):
			if(rpi_support):
				p.rint("setting pin "+str(pin)+" weak low","g")
				GPIO.setup(pin,	GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		
		else:
			if(rpi_support):
				p.rint("setting pin "+str(pin)+" high","g")
				GPIO.setup(pin, GPIO.OUT)
				GPIO.output(pin,1)

	def get(self,pin):
		if(rpi_support):
			return GPIO.input(pin)
		return 0
