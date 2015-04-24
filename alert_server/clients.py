#A info container for each camera client
class m2m_clients: 
	def __init__(self, addr):
		self.ip = addr.getpeername()[0]  	# the IP adress
		self.port = addr.getpeername()[1]	# the client port
		self.conn=addr				# this is the socket
		self.description = "This shape has not been described yet"
		self.author = "Nobody has claimed to make this shape yet"
		self.openfile="" 			# the filename of the open file
		self.buffer=""				# ?
		self.fp=""				# the filepointer to the open file
		self.mid=-1				# the Machine ID (unique identifier per camera device)
		self.logged_in=0			# 1 if log-in OK
		self.last_comm=0			# timestamp of the last incoming msg
		self.m2v=[]				# list of all active viewer subscribers. those will get a message for e.g. idle -> motion detected
		self.area=" "				# a location like "in front of the main entrace"
		self.account=" "			# the accout the device belongs to .. something like JKW even if there are two logins (kolja,caro) to the ACCOUNT
		self.state=0				# what state is the cam in? 0=idle
		self.webcam=[]				# list of webcam_viewer who are watching the webcam
		self.state=-1				# state of the cam, 0=idle, 1=alert, 2=detection disabled

# dies ist der WEBSOCKET client
class ws_clients:
	def __init__(self, addr):
		self.ip = addr.getpeername()[0] 	# the IP adress of the viewr	
		self.port = addr.getpeername()[1]	# the client port
		self.conn=addr				# this is the socket
		self.description = "This shape has not been described yet"
		self.author = "Nobody has claimed to make this shape yet"
		self.logged_in=0			# 1 if log-in ok
		self.last_comm=0			# timestamp of the last incoming msg
		self.v2m=[]				# list of all active subscribers. those will get a message for e.g. alert->sharp
		self.login=" "				# the login that has been used to connect to the DB
		self.accunt=" "				# the account the login belongs to .. something like JKW even if there are two logins (kolja,caro) to the account. multiple login for one account


class webcam_viewer:
	def __init__(self,cli):
		self.ws = cli 				# this shall hold the websocket client
		self.interval = 0			# the intervall as in
		self.ts = 0				# the timestamp of the last refresh
