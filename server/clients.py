#A info container for each camera client
m2m_state = ["idle","alert","disabled,idle","disabled,movement","no pir","error"]
det_state = ["off","on,single","on,permanent","error"]


class m2m_clients: 
	def __init__(self, addr):
		try:
			self.ip = addr.getpeername()[0]  	# the IP adress
			self.port = addr.getpeername()[1]	# the client port
		except:
			pass
		self.conn=addr						# this is the socket
		self.openfile="" 					# the filename of the open file
		self.buffer=""						# ?
		self.fp=""							# the filepointer to the open file
		self.mid=-1							# the Machine ID (unique identifier per camera device)
		self.logged_in=0					# 1 if log-in OK
		self.last_comm=0					# timestamp of the last incoming msg
		self.comm_timeout=11*60					# max time with incoming msg
		self.m2v=[]							# list of all active viewer subscribers. those will get a message for e.g. idle -> motion detected
		self.m2m=[]							# list of all active M2M! viewer subscribers. those will get a message for e.g. idle -> motion detected
		self.area=" "						# a location like "in front of the main entrace"
		self.area_id=-1						# a location like 3
		self.account=" "					# the accout the device belongs to .. something like JKW even if there are two logins (kolja,caro) to the ACCOUNT
		self.webcam=[]						# list of type webcam_viewer who are watching the webcam
		self.state=-1						# state of the cam, 0=idle, 1=alert, 2=detection disabled, idle, 3=detection disabled, movement
		self.challange=""					# challange for the login
		self.alert=alert_event()			# event structure
		self.alias = ""						# it might be easiser to give each device a nickname
		self.latitude = -1					# latitude
		self.longitude = -1					# longitude
		self.detection = -1					# detection state 0=off,1=on,2=on + heavy-fire
		self.detection_on_mode=1			# can be 1 or 2 and will be copied to detection on "switch on". Should come from database. it is the same for all boxes in the same area on the same account
		self.brightness_pos = 0				# position for the brightness slider for the ws
		self.color_pos = 0					# position for the color slider for the ws
		self.debug_ts=0						# each process has to update this ts to show that he is alive
		self.sendq = []						# the messages to be send
		self.alarm_ws = 1					# shall the photos of this m2m be forwarded to the connected WS in case of an alert
		self.frame_dist = 0.5					# distance between frames, 2fps
		self.resolution = "HD"					# 720p
		self.alarm_while_streaming = 0				# bad power supply
		self.v_short = "-"					# version nr
		self.v_hash = "-"					# hash of git state
		self.v_sec = "-"					# manual sec key
		self.external_state = 0					# state of the external pin
		self.with_lights = "0"					# neo pixel = 1, pwm = 2 , i2c = 3, nothing = 0
		self.with_pir = "0"					# is motione detection supported
		self.with_cam = "0"					# is a camera attached
		self.with_ext = "0"					# is a relay attached
		self.m2m_monitor = 0					# 1=this m2m device shall get status updates from all other m2m devices on this account and area
		

# dies ist der WEBSOCKET client
class ws_clients:
	def __init__(self, port, ip):
		self.ip = str(ip)					# the IP adress of the viewr	
		self.port = str(port)					# the client port
		self.uuid = ""						# IMEI/?
		self.logged_in=0					# 1 if log-in ok
		self.last_comm=0					# timestamp of the last incoming msg
		self.v2m=[]							# list of all active subscribers. those will get a message for e.g. alert->sharp
		self.login=" "						# the login that has been used to connect to the DB
		self.account=" "					# the account the login belongs to .. something like JKW even if there are two logins (kolja,caro) to the account. multiple login for one account
		self.snd_q_len=0					# messages in queue for this ws
		self.challange=""					# challange for the login
		self.location=""
		self.ws=None
		self.webcam_countdown=99				# remaining webcam frames
		self.alarm_view=0					# if we should send the client alarm view without request (used in the service)
		self.email=""						# email adresse for evidence pictures
		self.debug_ts=0						# each process has to update this ts to show that he is alive
		self.alive=1						# set to 0 to end session

class webcam_viewer:
	def __init__(self,cli):
		self.ws = cli 				# this shall hold the websocket client
		self.interval = 0			# the intervall as in
		self.ts = 0					# the timestamp of the last refresh

class alert_event:
	def __init__(self):
		self.ts = 0							# timestamp of the first recogition of the alert
		self.files = []						# list of filenames for that event
		self.notification_send = 0			# 0 or 1
		self.collecting = 0					# 0 or 1
		self.notification_send_ts = 0		# is the location send ? -1 means send it asap
		self.files_expected = 5				# wait for 5 pictures till you send a mail
		self.file_max_timeout_ms = 5000		# wait up to 5sec on pictures and send the mail if they don't appere
		self.comm_path = 1					# +1 = via mail, +2 = via WS
		self.email = ["kkoolljjaa@gmail.com"]	# list of all receivers
		self.last_upload = 0
		self.id=0
