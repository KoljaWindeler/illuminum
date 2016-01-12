import time
import p

rpi_support  = 1
fsys_support = 1

# import rpi gpio if posible
try:
	import RPi.GPIO as GPIO
except:
	rpi_support = 0

# import fsys for CHIP if posible
# XIO-P0   408    13
# XIO-P1   409    14
# XIO-P2   410    15
# XIO-P3   411    16
# XIO-P4   412    17
# XIO-P5   413    18
# XIO-P6   414    19
# XIO-P7   415    20
if(rpi_support):
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

		elif(fsys_support):
			p.rint("configuring fsys pins","g")

			self.PIN_PIR 		= 408
			self.PIN_MOVEMENT 	= 409	
			self.PIN_DETECTION 	= 410
			self.PIN_USER 		= 411
			self.PIN_CAM 		= 412

			self.fsys_export(self.PIN_PIR)
			self.fsys_export(self.PIN_MOVEMENT)
			self.fsys_export(self.PIN_DETECTION)
			self.fsys_export(self.PIN_USER)
			self.fsys_export(self.PIN_CAM)


	def set(self,pin,level):
		if(rpi_support):
			if(level==0):
				p.rint("setting pin "+str(pin)+" weak low","g")
				GPIO.setup(pin,	GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
			else:
				p.rint("setting pin "+str(pin)+" high","g")
				GPIO.setup(pin, GPIO.OUT)
				GPIO.output(pin,1)
		elif(fsys_support and pin>=408 and pin<=415):
			try:
				gpiopin = "gpio%s" % (str(pin))
				f = open("/sys/class/gpio/"+gpiopin+"/direction","w")
				f.write("out")
				f.close()
				f = open("/sys/class/gpio/"+gpiopin+"/value","w")
				if(level==0):
					f.write("0")
				else:
					f.write("1")
				f.close()
			except:
				p.warn("failed to write to pin "+str(pin))


	def get(self,pin):
		if(rpi_support):
			return int(GPIO.input(pin))
		elif(fsys_support and pin>=408 and pin<=415):
			try:
				gpiopin = "gpio%s" % (str(pin))
				f = open("/sys/class/gpio/"+gpiopin+"/direction","w")
				f.write("in")
				f.close()
				f = open("/sys/class/gpio/"+gpiopin+"/value","r")
				val=f.read()
				f.close()
				#rint("read from pin "+str(pin)+" returned "+str(int(val)))
				return int(val)
			except:
				p.warn("failed to read from pin "+str(pin))
		return int(0)

	def fsys_export(self,pin):
		if(pin<408 or pin>415):
			p.warn("fsys export error, pin "+str(pin)+" out of range (408-415)")
		else:
			try:
				f = open("/sys/class/gpio/export","w")
				f.write(str(pin))
				f.close()
			except:
				p.warn("Failed to set pin "+str(pin)+" as output")

