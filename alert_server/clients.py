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
		self.id=-1				# the ID (unique identifier per camera device)
		self.logged_in=0			# 1 if log-in OK
		self.last_comm=0			# timestamp of the last incoming msg
		self.m2v=[]				# list of all active viewer subscribers. those will get a message for e.g. idle -> motion detected
		self.area=" "				# a location like "in front of the main entrace"
		self.user_id=" "			# the USER ID the device belongs to .. something like JKW even if there are two logins (kolja,caro) to the USER
		self.state=0				# what state is the cam in? 0=idle


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
		self.user_id=" "			# the USER ID the login belongs to .. something like JKW even if there are two logins (kolja,caro) to the USER. multiple login for one user_id


