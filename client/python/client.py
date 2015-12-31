###################### import libs #######################
import OpenSSL
import RPi.GPIO as GPIO
import socket
import time
import json, base64, datetime, string, random
import hashlib, select, trigger, uuid, os, sys, subprocess
import light, p
###################### import libs #######################

###################### try import login #######################
register_mode=0
if(os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"login.py"))):
	from login import *
	l = login()					# login
	m2m_pw=l.pw
	p.rint("STARTUP, login.py found, password loaded","l")
else:
	register_mode=1
	p.rint("STARTUP, no login.py found, running in register mode","l")
###################### try import login #######################

###################### sleep to avoid cpu usage #######################
class CPUsaver:
	def __init__(self):
		self.state = 1  	# 1=I am busy
		self.wait = 0.01	# 10 ms wait
	def save_power(self):
		if(self.state != 1):
			time.sleep(self.wait)
		self.state = 0
	def set(self):
		self.state = 1
###################### sleep to avoid cpu usage #######################

###################### config properties #######################
class config:
	def __init__(self):
		self.with_cam=0
		self.with_neo=0
		self.with_pwm=0
		self.with_pir=0
		self.with_ext=0

	def check(self):
		if(self.with_neo and self.with_pwm):
			p.rint("STARTUP, pwm AND neo activated but only one possible","l")
			p.rint("STARTUP, falling back to neo support","l")
			self.with_pwm=0

###################### config properties #######################

###################### webcam properties #######################
class WebCam:
	def __init__(self):
		self.interval = 0
		self.quality = "HD" # HD=high, VGA=low
		self.last_picture_taken_ts = 0
		self.webview_active = 0
		self.alarm_interval = 1 # 1fps, if faster network gets in trouble with multiple cams
		self.alarm_pictures_remaining = 0
		self.alarm_in_alarm_state = 0
		self.alarm_while_streaming = 0
###################### webcam properties #######################

###################### connection properties #######################
class WebSocketConnection:
	def __init__(self):
		self.recv_buffer = ""
		self.sock = ""
		self.last_transfer = 0
		self.logged_in = 0			# avoiding that we send stuff without being logged in
		self.hb_out = 0
		self.hb_out_ts = 0
		self.msg_q = []
		self.unacknowledged_msg = []
		self.ack_request_ts = 0		# used to save the time when the last message, requesting a ACK was send

		self.max_msg_size = 10024000 # 10 MB?
		self.server_ip = "illuminum.de"
		self.server_port = 9875
		if(os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"experimental"))):
			self.server_port = 9775
			p.rint("!!!!!!!!! RUNNING ON EXPERIMENTAL PORT !!!!!!!!!!!","l")
		self.server_timeout = 15
		self.max_outstanding_acks = 2
###################### connection properties #######################

###################### debugging #######################
class Debugging:
	def __init__(self):
		self.active_since_ts = 0
		self.frames_uploaded_since_active = 0
		self.last_pic_taken_ts = 0
###################### debugging #######################

###################### koljas cams are running on ro-filesystems #######################
def rw(): #remounts the filesystem read-write
	subprocess.Popen(["mount","-o","remount,rw", "/"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()
###################### koljas cams are running on ro-filesystems #######################

#******************************************************#
def pin_config():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)

	GPIO.setup(PIN_MOVEMENT, GPIO.OUT)
	GPIO.setup(PIN_DETECTION, GPIO.OUT)
	GPIO.setup(PIN_USER, GPIO.OUT)
	GPIO.setup(PIN_CAM, GPIO.OUT)

	GPIO.output(PIN_MOVEMENT,0)
	GPIO.output(PIN_DETECTION,0)
	GPIO.output(PIN_USER,0)
	GPIO.output(PIN_CAM,0)

#******************************************************#
def trigger_handle(event, data):
	global cam
	global con
	global register_mode

	if(event == "state_change"):
		_state = data[0]
		_detection = data[1]
		#rint("setting in client.py "+str(_state)+" /  "+str(_detection))

		if(register_mode==0):
			p.rint("Switch to state '"+trigger.m2m_state[_state]+"' with detection '"+trigger.det_state[_detection]+"'","v")

		msg = {}
		msg["cmd"] = event
		msg["state"] = _state
		msg["detection"] = _detection

		##### delete ALL old status msg, and place the current status in the queue #########
		for m in con.msg_q:
			if(msg["cmd"] == m["cmd"]):
				con.msg_q.remove(m)

		# avoid message on alarm if alarm_while_streaming=0 at various conditions
		send_msg=1
		if(_state>0 and _detection>0 and cam.alarm_while_streaming==0): 
			if(cam.webview_active==1):				# no alarm while streaming
				send_msg=0
			elif(time.time()-cam.last_picture_taken_ts<5):	# dead - time after streaming, 5 sec
				send_msg=0
		if(send_msg):
			# if we have a new status, check the complete queue if we have old unsend stati and remove them first, they aren't valid anymore
			for msg_i in con.msg_q:
				if(msg_i["cmd"]==msg["cmd"]):
					con.msg_q.remove(msg_i)
			con.msg_q.append(msg)
		##### delete ALL old status msg, and place the current status in the queue #########

		##### light dimming #########
		# if we change the state of the sensor, we should most likely change the light
		# clear all old dimming actions
		light.clear_q()
		# set new color
		if(_detection == 0 and _state == 1): # deactive and motion
			if(cam.webview_active == 0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(), light.runner.l.d_r, light.runner.l.d_g, light.runner.l.d_b, 4000) # 4 sec to dimm to default color - now
			else:
				(r,g,b) = light.runner.get_color()
				light.set_old_color(r,g,b,time.time()+light.get_delay_off()) # set the color to which we return as soon as the webfeed is closed
		elif(_detection == 0 and _state == 0): # deactive and no motion
			if(cam.webview_active == 0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time()+light.get_delay_off(), 0, 0, 0, 4000) # 4 sec to dimm to off - in 10 min from now
			else:
				(r,g,b) = light.runner.get_color()
				light.set_old_color(r,g,b,time.time()+light.get_delay_off()) # set the color to which we return as soon as the webfeed is closed
			#rint("[A "+time.strftime("%H:%M:%S")+"] setting lights off to "+str((datetime.datetime.fromtimestamp(int((time.time()+light.get_delay_off())))).strftime('%y_%m_%d %H:%M:%S')))
		elif(_detection == 1 and _state == 1): # alarm, go red, now
			if(cam.webview_active == 0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(), 100, 0, 0, 4000)
			else:
				light.set_old_color(100, 0, 0,time.time()+light.get_delay_off())# set the color to which we return as soon as the webfeed is closed
		elif(_detection == 1 and _state == 0): # off while nobody is there
			if(cam.webview_active == 0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(), 0, 0, 0, 4000)
			else:
				(r,g,b) = light.runner.get_color()
				light.set_old_color(r,g,b,time.time()+light.get_delay_off()) # set the color to which we return as soon as the webfeed is closed
		##### light dimming #########

		##### camera picture upload #########
		if(_state > 0 and _detection > 0): # alarm state
			if(cam.alarm_in_alarm_state == 0):
				cam.alarm_in_alarm_state = 1
				cam.alarm_pictures_remaining = 5
		else: # state==0 or detection==0, leave the picture remaining so we can finish uploading all 5 pictures per alarm
			cam.alarm_in_alarm_state = 0
		##### camera picture upload #########

		##### set the gpio pins #####
		g_state = 0
		if(_state > 0):
			g_state = 1
		GPIO.output(PIN_MOVEMENT,g_state)

		g_detection = 0
		if(_detection > 0):
			g_detection = 1
		GPIO.output(PIN_DETECTION,g_detection)
		##### set the gpio pins #####

#******************************************************#

#******************************************************#
def upload_picture(_con, res):
#	rint(str(time.time())+" --> this is upload_file")
#	if(STEP_DEBUG):
#		p.rint("Step 5. this is upload_file with "+str(len(_con.msg_q))+" msg in q")
	if(len(_con.msg_q) > 0):
		p.rint("skip picture, q full","d")
		return 1

	p.set_last_action("loading img")
	#if full frame read other file
	try:
		if res!="VGA":
			img = open("/dev/shm/mjpeg/cam_full.jpg", 'rb')
		else:
			img = open("/dev/shm/mjpeg/cam_prev.jpg", 'rb')
	except:
		img=open("ic_camera_black_48dp.png", 'rb')

	i = 0
	while True:
		# should realy read it in once, 10MB buffer
		strng = img.read(_con.max_msg_size-100)
		if not strng:
			#rint("could not read")
			break

		msg = {}
		msg["cmd"] = "wf"
		msg["fn"] = mid+"_"+str(int(time.time()*100) % 10000)+'.jpg'
		msg["data"] = base64.b64encode(strng).decode('utf-8')
		msg["sof"] = 0
		if(i == 0):
			msg["sof"] = 1
		msg["eof"] = 0
		msg["msg_id"] = i
		msg["ack"] = 1 #-1
		#msg["ts"]=td
		if(len(strng) != (_con.max_msg_size-100)):
			msg["eof"] = 1
		#rint('sending('+str(i)+') of '+path+'...')

		msg["td"] = ((time.time(), "send"), (time.time(), "send"))
		_con.msg_q.append(msg)
		#if(STEP_DEBUG):
		#	rint("[A "+time.strftime("%H:%M:%S")+"] Step 6  upload appended message")
		i = i+1

	p.set_last_action("loading img done")

	#rint(str(time.time())+' all messages for '+path+' are in buffer.. i guess')
	img.close()
	cam.last_picture_taken_ts = time.time()
	return 0
	# end of while

#******************************************************#
def connect(con):
	global register_mode
	p.rint("--> connecting to illuminum server ...","l")
	p.set_last_action("connecting")

	context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	c_socket = OpenSSL.SSL.Connection(context, s)
	try:
		c_socket.connect((con.server_ip, con.server_port))
	except:
		p.rint("Could not connect to server","l")
		p.rint("retrying in 3 sec","l")
		time.sleep(3)
		return -1

	p.rint("<-- connected to server. ","l")
	if(register_mode==0):
		p.rint("--> Starting log-in process","l")
	else:
		p.rint("--> Begin register process...","l")
	p.set_last_action("connecting done")

	#### prelogin
	msg = {}
	msg["mid"] = mid
	msg["cmd"] = "prelogin"
	con.msg_q.append(msg)
	#int("sending prelogin request")

	return c_socket


# generate a random password
#******************************************************#
def get_pw(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

# Parse the incoming msg and do something with it
#******************************************************#
def parse_incoming_msg(con):
	global register_mode, m2m_pw
	p.set_last_action("start recv")
	try:
		data = con.sock.recv(con.max_msg_size)
		if(len(data) == 0):
			p.rint("disconnect","l")
			client_socket = ""
			p.set_last_action("disconnected")

			return -1

		p.rint("received "+str(len(data))+" byte", "v")
		p.set_last_action("decoding")
		data_dec = data.decode("UTF-8")
		#rint("Data received:"+str(data))
	except:
		p.rint('client_socket.recv detected error',"d")
		return -1

	p.set_last_action("start parse")

	data_dec = con.recv_buffer+data_dec
	data_array = data_dec.split('}')	# might have multiple JSON messages in the buffer or just "{blab}_"

	for a in range(0, len(data_array)-1):
		data_array[a] += '}'	# add } again, as it got lost during "split"

		try:
			enc = json.loads(data_array[a])
		except:
			p.rint("json decode failed on:"+data_array[a],"l")
			p.set_last_action("decoding bad")

			return -2 # bad message, reconnect

		if(type(enc) is dict):
			con.last_transfer = time.time()
			#rint("json decoded msg")
			#rint(enc)
			# ack ok packets are always send alone, they carry the cmd to acknowledge, but the reason will be a separate msg
			if(enc.get("ack_ok", 0) == 1):
				#rint("this is an ack ok package "+str(len(con.unacknowledged_msg)))
				if(len(con.unacknowledged_msg) > 0):
					for ele in con.unacknowledged_msg:
						if(ele[0] == enc.get("cmd", 0)): # find the right entry
							con.unacknowledged_msg.remove(ele)
							break
					#rint("comm wait dec at "+str(time.time())+" --> "+str(len(con.unacknowledged_msg)))
				# recalc timestamp
				if(len(con.unacknowledged_msg) == 0):
					con.ack_request_ts = 0					# clear ts
				else:
					con.ack_request_ts = con.unacknowledged_msg[0][1]		# move to latest ts

			elif(enc.get("cmd") == "prelogin" and register_mode==0):
				p.rint("<-- encryption challange received","l")
				#### send login
				#rint("received challange "+enc.get("challange"))
				h = hashlib.md5()

				# hash the login with the challange
				h.update(str(m2m_pw+enc.get("challange")).encode("UTF-8"))
				#rint("total to code="+str(pw+enc.get("challange")))
				pw_c = h.hexdigest()
				#rint("result="+pw_c)
				path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","..",".git")
				v_sec=SEC_VERSION
				v_hash=str(subprocess.Popen(["sudo","-u","pi", "git", "--git-dir", path, "log", "--pretty=format:%h", "-n", "1"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())

				msg = {}
				msg["mid"] = mid
				msg["client_pw"] = pw_c
				msg["cmd"] = "login"
				msg["state"] = trigger.r.s.state
				msg["detection"] = trigger.r.s.detection
				msg["ts"] = time.strftime("%d.%m.%Y || %H:%M:%S")
				msg["ack"] = 1
				msg["v_sec"] = v_sec
				msg["v_hash"] = v_hash
				con.msg_q.append(msg)

			elif(enc.get("cmd") == "prelogin" and register_mode==1):

				# first time connection, create a password and send it to the server
				m2m_pw=str(get_pw())
				f_content='class login:\r\n	def __init__(self):\r\n		self.pw="'+m2m_pw+'"\n'

				file=open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"login.py"),"w")
				file.write(f_content)
				file.close()
				# try to get cam name from raspimjpeg config file
				alias="SecretCam"
				if(os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../gpucam/annotation.config"))):
					file=open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../gpucam/annotation.config"),"r")
					file_c=file.readlines()
					for line in file_c:
						if(line.find("annotation")==0 and line.find("%04d.%02d.%02d_%02d:%02d:%02d")>0):
							alias=line[len("annotation")+1:line.find("%04d.%02d.%02d_%02d:%02d:%02d")-1]
							break

				ws_login = input("Please enter your username: ")
				ws_pw = input("Hi "+ws_login+", please enter your userpassword: ")

				# encrypt the user pw just because we can ... i know we have a https connection but  hey .. 
				h = hashlib.md5()
				h.update(str(ws_pw).encode("UTF-8"))
				ws_pw_enc = h.hexdigest()

				h = hashlib.md5()
				h.update(str(ws_pw_enc+enc.get("challange")).encode("UTF-8"))
				ws_pw_ch_enc = h.hexdigest()

				msg = {}
				msg["mid"] = mid
				msg["login"] = ws_login
				msg["password"] = ws_pw_ch_enc
				msg["m2m_pw"]=m2m_pw
				msg["cmd"] = "register"
				msg["alias"] = alias
				con.msg_q.append(msg)

				#rint(msg)

			elif(enc.get("cmd") == "login"):
				if(enc.get("ok") == 1):
					con.logged_in = 1

					r = enc.get("mRed",0)
					g = enc.get("mGreen",0)
					b = enc.get("mBlue",0)
	
					light.runner.l.d_r = r
					light.runner.l.d_g = g
					light.runner.l.d_b = b

					p.rint("<-- received log-in OK","l")				
					p.rint("<-- setting detection to "+str(enc.get("detection")),"l")
					trigger.set_detection(int(enc.get("detection")))
				else:
					con.logged_in = 0
					p.rint("<-- ERROR log-in failed","l")
			elif(enc.get("cmd") == "m2m_hb"):
				con.hb_out = 0
				p.rint("<-- connection checked OK","l")
			elif(enc.get("cmd") == "set_detection"):
				p.rint("<-- received request to change detection state to "+str(enc.get("state")),"l")
				trigger.set_detection(enc.get("state"))
			elif(enc.get("cmd") == "wf"):
				ignore = 1
			elif(enc.get("cmd") == "set_color"):
				# avoid light output message, like to many many commands
				r = enc.get("r", 0)
				g = enc.get("g", 0)
				b = enc.get("b", 0)
				light.set_color(r,g,b)
				light.add_q_entry(time.time(), r, g, b, 500) # 4 sec to dimm to warm orange - now

			elif(enc.get("cmd") == "set_interval"):
				if(enc.get("interval", 0) == 0):
					cam.webview_active = 0
					GPIO.output(PIN_CAM,0)
					p.rint("<-- switching webcam off","l")
				else:
					cam.webview_active = 1
					GPIO.output(PIN_CAM,1)
					p.rint("<-- switching webcam on","l")
				cam.interval = (enc.get("interval", 0))
				cam.quality = (enc.get("qual", "HD"))
				if(enc.get("alarm_while_streaming","no_alarm")=="alarm"):
					cam.alarm_while_streaming = 1
				else:
					cam.alarm_while_streaming = 0
######### SPY MODE #########
				if(enc.get("interval",0)>0):
					(r,g,b) = light.runner.get_color()
					light.set_old_color(r,g,b,time.time()+light.get_delay_off()) # set the color to which we return as soon as the webfeed is closed
					light.add_q_entry(time.time(),0,255,0,1000) # 4 sec to dimm to off - in 10 min from now
				else:
					print("setting to -1,-1,-1")
					light.add_q_entry(time.time(),-1,-1,-1,1000) # 4 sec to dimm to off - in 10 min from now
######### SPY MODE #########
			elif(enc.get("cmd") == "register"):
				if(enc.get("ok",0) == 1):
					p.rint("<-- successful registered, sending sign in","l")
					register_mode=0
				else:
					p.rint("<-- registration was not successful, status: "+str(enc.get("ok"))+". Starting over","l")

				msg = {}
				msg["mid"] = mid
				msg["cmd"] = "prelogin"
				con.msg_q.append(msg)
	
			elif(enc.get("cmd") == "update_parameter"):
				p.rint("<-- Received Parameter update from server","l")
				if(enc.get("alarm_while_streaming","no_alarm")=="alarm"):
					cam.alarm_while_streaming = 1
				else:
					cam.alarm_while_streaming = 0
				cam.interval = (enc.get("interval", 0))
				cam.quality = (enc.get("qual", "HD"))

				# save old parameter
				old_with_cam = config.with_cam
				old_with_neo = config.with_neo
				old_with_pwm = config.with_pwm
				old_with_ext = config.with_ext
				old_with_pir = config.with_pir

				# save new parameter
				config.with_pir = int(enc.get("with_pir", "0"))
				config.with_neo = int(enc.get("with_neo", "0"))
				config.with_pwm = int(enc.get("with_pwm", "0"))
				config.with_ext = int(enc.get("with_ext", "0"))
				config.with_cam = int(enc.get("with_cam", "0"))

				# re-starting the light and trigger with new parameter, if different
				if(config.with_neo != old_with_neo or config.with_pwm != old_with_pwm):
					p.rint("=== (re)start light, as configuration has changed","l")
					light.restart(config)
					time.sleep(1)
				
				if(config.with_pir != old_with_pir):
					p.rint("=== (re)start trigger, as configuration has changed","l")
					trigger.restart(config)


			# get the git version
			elif(enc.get("cmd") == "get_version"):
				path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","..",".git")
				v_short=str(subprocess.Popen(["sudo","-u","pi", "git","--git-dir", path, "rev-list", "HEAD", "--count"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode()).replace("\n","")
				v_hash=str(subprocess.Popen(["sudo","-u","pi", "git","--git-dir", path,"log", "--pretty=format:%h", "-n", "1"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())

				p.rint("<-> version request received from server, returning "+str(v_hash),"l")

				msg = {}
				msg["mid"] = mid
				msg["cmd"] = enc.get("cmd")
				msg["v_short"] = v_short
				msg["v_hash"] = v_hash
				con.msg_q.append(msg)

			# run a git update
			elif(enc.get("cmd") == "git_update"):
				p.rint("<-- update request received from server","l")
				# remount root rw
				rw() 
				path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","..",".git")
				# run the update
				result=subprocess.Popen(["sudo","-u","pi", "git", "pull"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()
				ret_res=result[0].decode().replace("\n","")
				# get new version
				v_short=str(subprocess.Popen(["sudo","-u","pi", "git","--git-dir", path, "rev-list", "HEAD", "--count"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode()).replace("\n","")
				v_hash=str(subprocess.Popen(["sudo","-u","pi", "git","--git-dir", path,"log", "--pretty=format:%h", "-n", "1"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())

				msg = {}
				msg["mid"] = mid
				msg["cmd"] = enc.get("cmd")
				msg["v_short"] = v_short
				msg["v_hash"] = v_hash
				msg["cmd_result"] = ret_res
				con.msg_q.append(msg)

			# run a reboot
			elif(enc.get("cmd") == "reboot"):
				con.sock.shutdown()
				con.sock.close()
				print("<- ============================")
				print("<- ======== rebooting =========")
				print("<- ============================")
				result=str(subprocess.Popen("reboot",stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode()).replace("\n","")

				
			# set a pin 
			elif(enc.get("cmd") == "toggle_external_pin"):
				state = 0
				if(str(enc.get("state",0))=="1"):
					state = 1
				p.rint("<-- switching external pin to "+str(state),"l")
				GPIO.output(PIN_USER,state)

				msg = {}
				msg["mid"] = mid
				msg["cmd"] = enc.get("cmd")
				msg["ok"] = "1"
				con.msg_q.append(msg)

			# set alias
			elif(enc.get("cmd") == "set_alias"):
				alias = enc.get("alias","-")
				p.rint("<-- Trying to set a new name: "+str(alias),"l")
				msg = {}
				msg["mid"] = mid
				msg["cmd"] = enc.get("cmd")
				msg["ok"] = "-1"
			
				try:
					# remount root rw
					rw() 
					# run update
					path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","gpucam")
					if(os.path.isfile(os.path.join(path,"annotation.config"))):
						file=open(os.path.join(path,"annotation.config"),"w")
						file.write("annotation "+alias+" %04d.%02d.%02d_%02d:%02d:%02d \nanno_background false")
						file.close()
						subprocess.Popen(os.path.join(path,"generate_config.sh"),stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()
						msg["ok"] = "1"
						p.rint("--> Setting new alias, ok","l")
				except:
					import sys, traceback
					print("sys:")
					print(str(sys.exc_info()[0]))
					print(str(sys.exc_info()[1]))
					print(str(repr(traceback.format_tb(sys.exc_info()[2]))))
					print("--> setting new name failed")
				con.msg_q.append(msg)

			else:
				p.rint("<-- unsopported command received:"+enc.get("cmd"),"l")


		#end of "if"
	# end of "for"

	if(data_array[len(data_array)-1] == ""):
		#if data contained a full message and ended with closing tag, we a$
		con.recv_buffer = ""
	else:
		# but if we grabbed something like 1.5 messages, we should buffer $
		con.recv_buffer = data_array[len(data_array)-1]
		#rint("using buffer!")

	p.set_last_action("recv done")
	return 0
#********************************************************#

# manual version 
SEC_VERSION="20151229"


config = config()


p.rint("STARTUP, settings pins","l")
# init objects and vars
STEP_DEBUG = 0
TIMING_DEBUG = 1
PIN_MOVEMENT = 11
PIN_DETECTION = 13
PIN_USER = 15
PIN_CAM = 16
#start pin config
pin_config()

mid = str(uuid.getnode())

p.rint("STARTUP, creating webcam","l")
cam = WebCam() 				# webcam

p.rint("STARTUP, creating connection","l")
con = WebSocketConnection()	# connection

p.rint("STARTUP, creating debug","l")
d = Debugging()				# debug handle

p.rint("STARTUP, creating CPUsaver","l")
b = CPUsaver()


trigger.subscribe_callback(trigger_handle)

#only start listening to keyboard input if we are not in register mode
p.start(not(register_mode))

p.rint("===== STARTUP FINISHED, running main loop =====","l")
# Main programm
#******************************************************#

while 1:
	d.frames_uploaded_since_active = 0		# picture upload counter
	d.active_since_ts = 0	# picture first upload timer

	# start connection
	con.logged_in = 0
	con.sock = connect(con)

	while(con.sock != ""):
		b.save_power()	# sleep if nt busy

		p.set_con(con.logged_in, len(con.unacknowledged_msg), len(con.msg_q), con.ack_request_ts)

		#************* receiving start ******************#
		try:
			ready_to_read, ready_to_write, in_error = select.select([con.sock], [con.sock,], [], 0)
			#rint(str(len(ready_to_read))+"/"+str(len(ready_to_write))+"/"+str(len(in_error)))
		except:
			p.rint("select detected a broken connection, reconnecting","d")
			con.sock = ""
			break

			## react on msg in
		if(len(ready_to_read) > 0):
			b.set() # busy, avoid cpu sleep
			if(parse_incoming_msg(con) < 0):
				break
		#************* receiving end ******************#

		#************* timeout check start ******************#
		if(time.time()-con.last_transfer > 60*5 and con.last_transfer!=0 and con.hb_out == 0):
			b.set() # busy, avoid cpu sleep
			p.rint("<-> checking connection","l")
			msg = {}
			msg["cmd"] = "m2m_hb"
			con.msg_q.append(msg)
			con.hb_out = 1
			con.hb_out_ts = time.time()
		#************* timeout check end ******************#

		#************* sending start ******************#
		if(len(con.msg_q) > 5):
			p.rint("!!!!!!!!!!!!!!!!!!!!!! con.msg_q is very long: "+str(len(con.msg_q))+", comm wait: "+str(len(con.unacknowledged_msg))+", logged in: "+str(con.logged_in),"l")

		# we have a message waiting and either we have an empty unacknowledged_msg_queue or we are not logged in, or both!
		if(len(con.msg_q) > 0 and (len(con.unacknowledged_msg) < con.max_outstanding_acks or not(con.logged_in))):
			b.set() # busy, avoid cpu sleep
			msg = ""
			if(con.logged_in != 1):	 	# check if we have a login msg in the q
				for msg_i in con.msg_q:
					if(msg_i["cmd"] == "prelogin"):
						p.rint("--> requesting encryption challange","d")
						msg = msg_i
						con.msg_q.remove(msg_i)
					if(msg_i["cmd"] == "register"):
						p.rint("r--> equesting registration","d")
						msg = msg_i
						con.msg_q.remove(msg_i)
					if(msg_i["cmd"] == "login"):
						p.rint("--> sending encrypted login","d")
						msg = msg_i
						con.msg_q.remove(msg_i)

			else:	# in this case we have a message waiting and we are logged in and the unacknowledged_msg_queue is short / empty
				msg = con.msg_q[0]
				con.msg_q.remove(msg)

			if(msg != ""):
				#rint("A message is ready to send")
				p.set_last_action("json / encode / sendall")

				send_msg = json.dumps(msg)
				send_msg_enc = send_msg.encode("UTF-8")
				try:
					#rint("Wait to send at ",end="")
					#rint(time.time(),end="")
					con.sock.sendall(send_msg)
					#rint(" sent " at ",end="")
					#rint(time.time())
				except:
					con.sock = ""
					p.rint("ERROR while sending data, init reconnect","l")
					break

				p.set_last_action("send all done")


				if(msg.get("ack", 0) == 1): # we want an ack!
					con.unacknowledged_msg.append((msg.get("cmd"), time.time()))
					con.ack_request_ts = time.time()
					#rint("increased con.unacknowledged_msg to "+str(len(con.unacknowledged_msg))+" entries for cmd "+msg["cmd"])

				#rint("message send")
				if(msg.get("cmd", " ") == "wf"):
					if(msg.get("eof", 0) == 1):
						if(TIMING_DEBUG):
							if(time.time()-d.last_pic_taken_ts > 15):
								d.active_since_ts = 0
								p.rint("reset fps","d")

							d.last_pic_taken_ts = time.time()
							d.frames_uploaded_since_active = d.frames_uploaded_since_active+1

							if(d.active_since_ts == 0):
								d.active_since_ts = time.time()
								d.frames_uploaded_since_active = 0
							else:
								p.rint("uploading frame at "+str(d.frames_uploaded_since_active/(time.time()-d.active_since_ts))+" fps","d")
#								rint("Uploaded "+str(d.frames_uploaded_since_active)+" Frames in "+str((time.time()-d.active_since_ts))+" this is "+str(d.frames_uploaded_since_active*25/(time.time()-d.active_since_ts))+"kBps or "+str(d.frames_uploaded_since_active/(time.time()-d.active_since_ts))+"fps")
#							rint("\r\n\r\n")


		############## at this point we consider to upload a picture #####################
		if(len(con.msg_q) == 0 and con.logged_in == 1):
			if(cam.webview_active == 1 and cam.last_picture_taken_ts+cam.interval < time.time()):
				upload_picture(con, cam.quality)
				b.set() # busy, avoid cpu sleep
			elif(cam.alarm_pictures_remaining > 0 and cam.last_picture_taken_ts+cam.alarm_interval < time.time()):
				cam.alarm_pictures_remaining = max(0, cam.alarm_pictures_remaining-1)
				upload_picture(con, cam.quality)
				b.set() # busy, avoid cpu sleep
		############## at this point we consider to upload a picture #####################

		############## free us if there is a lost packet #####################
		if(len(con.unacknowledged_msg) > 0 and con.logged_in == 1):
			b.set() # busy, avoid cpu sleep
			if(len(con.msg_q) > 0 and con.ack_request_ts != 0 and con.ack_request_ts+con.server_timeout < time.time()):
				p.rint("ERROR server did not send ack","l")
				con.unacknowledged_msg = []
		############## free us if there is a lost packet #####################

		############## reconnect us if there is no response #####################
		if(con.hb_out == 1 and con.hb_out_ts+con.server_timeout < time.time()):
			b.set() # busy, avoid cpu sleep
			p.rint("server did not respond to hb,reconnecting","l")
			con.hb_out = 0
			break
		############## reconnect us if there is no response #####################

		#************* sending end ******************#
	p.rint("connection destroyed, reconnecting","l")
	p.set_last_action("connection destroyed")

	cam.webview_active = 0 # switch off the webstream, we wouldn't have ws beeing connected to us anyway after resign on
	cam.alarm_pictures_remaining = 0
