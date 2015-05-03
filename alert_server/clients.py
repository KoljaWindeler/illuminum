#A info container for each camera client
m2m_state = ["idle","alert","disabled,idle","disabled,movement","error"]


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
		self.webcam=[]				# list of webcam_viewer who are watching the webcam
		self.state=-1				# state of the cam, 0=idle, 1=alert, 2=detection disabled, idle, 3=detection disabled, movement
		self.challange=""			# challange for the login
		self.alert=alert_event()	# event structure
		self.alias = ""				# it might be easiser to give each device a nickname

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
		self.snd_q_len=0			# messages in queue for this ws


class webcam_viewer:
	def __init__(self,cli):
		self.ws = cli 				# this shall hold the websocket client
		self.interval = 0			# the intervall as in
		self.ts = 0				# the timestamp of the last refresh

class alert_event:
	def __init__(self):
		self.ts = 0				# timestamp of the first recogition of the alert
		self.files = []				# list of filenames for that event
		self.notification_send_ts = 0		# is the location send ? -1 means send it asap
		self.files_expected = 5			# wait for 5 pictures till you send a mail
		self.file_max_timeout_ms = 5000		# wait up to 5sec on pictures and send the mail if they don't appere
		self.comm_path = 1			# +1 = via mail, +2 = via WS
		self.email = ["kkoolljjaa@gmail.com"]	# list of all receivers
		self.last_upload = 0
