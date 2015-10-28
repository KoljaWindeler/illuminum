import OpenSSL
import socket,os,time,json,base64, datetime
import hashlib,select,trigger,uuid
import sys,light,debug
from binascii import unhexlify, hexlify
from login import *
from math import *

class WebCam:
	def __init__(self):
		self.interval = 0
		self.last_picture_taken_ts = 0

		self.webview_active = 0

		self.alarm_interval=0.34 # 3fps
		self.alarm_pictures_remaining = 0
		self.alarm_in_alarm_state=0

class WebSocketConnection:
	def __init__(self):
		self.recv_buffer=""
		self.sock = ""
		self.last_transfer=0
		self.logged_in=0			# avoiding that we send stuff without being logged in
		self.hb_out = 0
		self.msg_q=[]
		self.unacknowledged_msg=[]
		self.ack_request_ts=0		# used to save the time when the last message, requesting a ACK was send

		self.MAX_MSG_SIZE = 10024000 # 10 MB?
		self.SERVER_IP = "52.24.157.229"
		self.SERVER_PORT = 9875
		self.SERVER_TIMEOUT = 15
		self.MAX_OUTSTANDING_ACKS=2

class Debugging:
	def __init__(self):
		self.active_since_ts = 0
		self.frames_uploaded_since_active = 0
		self.last_pic_taken_ts=0


#******************************************************#
def trigger_handle(event,data):
	global cam
	global con

	if(event=="state_change"):
		_state=data[0]
		_detection=data[1]

		msg={}
		msg["cmd"]=event
		msg["state"]=_state
		msg["detection"]=_detection

		##### delete ALL old status msg, and place the current status in the queue #########
		for m in con.msg_q:
			if(msg["cmd"]==m["cmd"]):
				con.msg_q.remove(m)
		con.msg_q.append(msg)
		##### delete ALL old status msg, and place the current status in the queue #########

		##### light dimming #########
		# if we change the state of the sensor, we should most likely change the light
		# clear all old dimming actions
		light.clear_q()
		# set new color
		if(_detection==0 and _state==1): # deactive and motion
			if(cam.webview_active==0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(),light.l.d_r,light.l.d_g,light.l.d_b,4000) # 4 sec to dimm to default color - now
			else:
				light.set_old_color(light.l.d_r,light.l.d_g,light.l.d_b) # set the color to which we return as soon as the webfeed is closed
		elif(_detection==0 and _state==0): # deactive and no motion
			delay_off=5*60 # usually 5 min
			off_time=get_time()+delay_off
			if(off_time>22*60*60 or (off_time%86400)<6*60*60): # switch off after 22h and before 6
				delay_off=0
			if(cam.webview_active==0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time()+delay_off,0,0,0,4000) # 4 sec to dimm to off - in 10 min from now
			else:
				light.set_old_color(0,0,0) # set the color to which we return as soon as the webfeed is closed
			print("[A "+time.strftime("%H:%M:%S")+"] setting lights off to "+str((datetime.datetime.fromtimestamp(int((time.time()+delay_off)))).strftime('%y_%m_%d %H:%M:%S')))
		elif(_detection==1 and _state==1): # alarm, go red, now
			if(cam.webview_active==0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(),100,0,0,4000)
			else:
				light.set_old_color(100,0,0)# set the color to which we return as soon as the webfeed is closed
		elif(_detection==1 and _state==0): # off while nobody is there
			if(cam.webview_active==0): # only change color if the webcam is no running to avoid that we switch the light during movement, while the videofeed is running
				light.add_q_entry(time.time(),0,0,0,4000)
			else:
				light.set_old_color(0,0,0) # set the color to which we return as soon as the webfeed is closed
		##### light dimming #########

		##### camera picture upload #########
		if(_state>0 and _detection>0): # alarm state
			if(cam.alarm_in_alarm_state==0):
				cam.alarm_in_alarm_state=1
				cam.alarm_pictures_remaining=5
		else: # state==0 or detection==0, leave the picture remaining so we can finish uploading all 5 pictures per alarm
			cam.alarm_in_alarm_state=0
		##### camera picture upload #########
#******************************************************#
#******************************************************#
def get_time():
	return time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
#******************************************************#


#******************************************************#
def upload_picture(con,high_res):
#	rint(str(time.time())+" -> this is upload_file")
	if(STEP_DEBUG):
		print("[A "+time.strftime("%H:%M:%S")+"] Step 5. this is upload_file for "+path+" with "+str(len(con.msg_q))+" msg in q")
	if(len(con.msg_q)>0):
		print("skip picture, q full")
		return 1

	debug.set_last_action("loading img")
	#if full frame read other file
	if high_res:
		img = open("/dev/shm/mjpeg/cam_full.jpg",'rb')
	else:
		img = open("/dev/shm/mjpeg/cam_prev.jpg",'rb')
	i=0
	while True:
		# should realy read it in once, 10MB buffer
		strng = img.read(con.MAX_MSG_SIZE-100)
		if not strng:
			#print("could not read")
			break

		msg={}
		msg["cmd"]="wf"
		msg["fn"]=mid+"_"+str(int(time.time()*100) % 10000)+'.jpg';
		msg["data"]=base64.b64encode(strng).decode('utf-8')
		msg["sof"]=0
		if(i==0):
			msg["sof"]=1
		msg["eof"]=0
		msg["msg_id"]=i
		msg["ack"]=1 #-1
		#msg["ts"]=td
		if(len(strng)!=(con.MAX_MSG_SIZE-100)):
			msg["eof"]=1
		#print('sending('+str(i)+') of '+path+'...')

		msg["td"]=((time.time(),"send"),(time.time(),"send"))
		con.msg_q.append(msg)
		if(STEP_DEBUG):
			print("[A "+time.strftime("%H:%M:%S")+"] Step 6  upload appended message for "+path)
		i=i+1

	debug.set_last_action("loading img done")

	#print(str(time.time())+' all messages for '+path+' are in buffer.. i guess')
	img.close()
	cam.last_picture_taken_ts=time.time()
	return 0
	# end of while

#******************************************************#
def connect(con):
	print("[A "+time.strftime("%H:%M:%S")+"] -> connecting ...")
	debug.set_last_action("connecting")

	context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	c_socket = OpenSSL.SSL.Connection(context,s)
	try:
		c_socket.connect((con.SERVER_IP, con.SERVER_PORT))
	except:
		print("Could not connect to server")
		print("retrying in 3 sec")
		time.sleep(3)
		return -1

	print("[A "+time.strftime("%H:%M:%S")+"] -> connected. Loggin in...")
	debug.set_last_action("connecting done")

	#### prelogin
	msg={}
	msg["mid"]=mid
	msg["cmd"]="prelogin"
	con.msg_q.append(msg)
	#print("sending prelogin request")

	return c_socket

# Parse the incoming msg and do something with it
#******************************************************#
def parse_incoming_msg(con):
	debug.set_last_action("start recv")
	try:
		data = con.sock.recv(con.MAX_MSG_SIZE)
		if(len(data)==0):
			print("disconnect")
			client_socket=""
			debug.set_last_action("disconnected")	

			return -1
	
		debug.set_last_action("decoding")
		data_dec = data.decode("UTF-8")
		#print("Data received:"+str(data))
	except:
		print('client_socket.recv detected error')
		return -1

	debug.set_last_action("start parse")

	data_dec=con.recv_buffer+data_dec
	data_array=data_dec.split('}')	# might have multiple JSON messages in the buffer or just "{blab}_"

	for a in range(0,len(data_array)-1):
		data_array[a]+='}'	# add } again, as it got lost during "split"

		try:
			enc=json.loads(data_array[a])
		except:
			print("json decode failed on:"+data_array[a])
			debug.set_last_action("decoding bad")

			return -2 # bad message, reconnect

		if(type(enc) is dict):
			con.last_transfer=time.time()
			#print("json decoded msg")
			#print(enc)
			# ack ok packets are always send alone, they carry the cmd to acknowledge, but the reason will be a separate msg
			if(enc.get("ack_ok",0)==1):
				#rint("this is an ack ok package "+str(len(con.unacknowledged_msg)))
				if(len(con.unacknowledged_msg)>0):
					for ele in con.unacknowledged_msg:
						if(ele[0]==enc.get("cmd",0)): # find the right entry
							con.unacknowledged_msg.remove(ele)
					#rint("comm wait dec at "+str(time.time())+" -> "+str(len(con.unacknowledged_msg)))
				if(len(con.unacknowledged_msg)==0):
					con.ack_request_ts=0					# clear ts
				else:
					con.ack_request_ts=con.unacknowledged_msg[0][1]		# move to latest ts

			elif(enc.get("cmd")=="prelogin"):
				#### send login
				#print("received challange "+enc.get("challange"))
				h = hashlib.md5()
				l=login()					# login
				h.update(str(l.pw+enc.get("challange")).encode("UTF-8"))
				#print("total to code="+str(pw+enc.get("challange")))
				pw_c=h.hexdigest()
				#print("result="+pw_c)

				msg={}
				msg["mid"]=mid
				msg["client_pw"]=pw_c
				msg["cmd"]="login"
				msg["state"]=trigger.s.state
				msg["detection"]=trigger.s.detection
				msg["ts"]=time.strftime("%d.%m.%Y || %H:%M:%S")
				msg["ack"]=1
				con.msg_q.append(msg)
			elif(enc.get("cmd")=="login"):
				if(enc.get("ok")==1):
					con.logged_in=1

					light.l.d_r=enc.get("mRed")
					light.l.d_g=enc.get("mGreen")
					light.l.d_b=enc.get("mBlue")

					print("[A "+time.strftime("%H:%M:%S")+"] -> log-in OK")
					print("[A "+time.strftime("%H:%M:%S")+"] setting detection to "+str(enc.get("detection")))
					trigger.s.set_detection(int(enc.get("detection")))
				else:
					con.logged_in=0
					print("[A "+time.strftime("%H:%M:%S")+"] -> log-in failed")
			elif(enc.get("cmd")=="m2m_hb"):
				con.hb_out=0
				print("[A "+time.strftime("%H:%M:%S")+"] -> connection OK")
			elif(enc.get("cmd")=="set_detection"):
				print("[A "+time.strftime("%H:%M:%S")+"] setting detection to "+str(enc.get("state")))
				trigger.s.set_detection(enc.get("state"))
			elif(enc.get("cmd")=="wf"):
				ignore=1
			elif(enc.get("cmd")=="set_color"):
				light.l.d_r=enc.get("r",0)
				light.l.d_g=enc.get("g",0)
				light.l.d_b=enc.get("b",0)
				light.add_q_entry(time.time(),light.l.d_r,light.l.d_g,light.l.d_b,500) # 4 sec to dimm to warm orange - now

			elif(enc.get("cmd")=="set_interval"):
				print("setting interval to "+str(enc.get("interval",0)))
				if(enc.get("interval",0)==0):
					cam.webview_active=0
				else:
					cam.webview_active=1
				cam.interval=(enc.get("interval",0))
######### SPY MODE #########
#						if(enc.get("interval",0)>0):
#							light.add_q_entry(time.time(),0,100,0,1000) # 4 sec to dimm to off - in 10 min from now
#						else:
#							light.add_q_entry(time.time(),-1,-1,-1,1000) # 4 sec to dimm to off - in 10 min from now
######### SPY MODE #########
			else:
				print("unsopported command:"+enc.get("cmd"))
		#end of "if"
	# end of "for"

	if(data_array[len(data_array)-1]==""):
		#if data contained a full message and ended with closing tag, we a$
		con.recv_buffer=""
	else:
		# but if we grabbed something like 1.5 messages, we should buffer $
		con.recv_buffer=data_array[len(data_array)-1]
		#print("using buffer!")

	debug.set_last_action("recv done")
	return 0
#********************************************************#


# init objects and vars
STEP_DEBUG=0
TIMING_DEBUG=1

mid=str(uuid.getnode())

cam=WebCam() 				# webcam
con=WebSocketConnection()	# connection
d=Debugging()				# debug handle

trigger.start()
trigger.s.subscribe_callback(trigger_handle)

light.start()

debug.start()
# Main programm
#******************************************************#

while 1:
	d.frames_uploaded_since_active=0		# picture upload counter
	d.active_since_ts=0	# picture first upload timer

	# start connection
	con.logged_in=0
	con.sock=connect(con)

	while(con.sock!=""):
		debug.set_con(con.logged_in,len(con.unacknowledged_msg),len(con.msg_q),con.ack_request_ts)

		#************* receiving start ******************#
		try:
			ready_to_read, ready_to_write, in_error = select.select([con.sock], [con.sock,], [], 0)
			#print(str(len(ready_to_read))+"/"+str(len(ready_to_write))+"/"+str(len(in_error)))
		except:
			print("select detected a broken connection")
			con.sock=""
			break

			## react on msg in
		if(len(ready_to_read) > 0):
			#print("read process is ready")
			if(parse_incoming_msg(con)<0):
				break
		#************* receiving end ******************#

		#************* timeout check start ******************#
		if(time.time()-con.last_transfer>60*5 and con.hb_out==0):
			print("[A "+time.strftime("%H:%M:%S")+"] -> checking connection")
			msg={}
			msg["cmd"]="m2m_hb"
			con.msg_q.append(msg)
			con.hb_out=1
		#************* timeout check end ******************#

		#************* sending start ******************#
		if(len(con.msg_q)>5):
			print("!!!!!!!!!!!!!!!!!!!!!! con.msg_q is very long: "+str(len(con.msg_q))+", comm wait: "+str(len(con.unacknowledged_msg))+", logged in: "+str(con.logged_in))

		# we have a message waiting and either we have an empty unacknowledged_msg_queue or we are not logged in, or both!
		if(len(con.msg_q)>0 and (len(con.unacknowledged_msg)<con.MAX_OUTSTANDING_ACKS or not(con.logged_in))):
			msg=""
			if(con.logged_in!=1):	 	# check if we have a login msg in the q
				for msg_i in con.msg_q:
					if(msg_i["cmd"]=="prelogin"):
						print("[A "+time.strftime("%H:%M:%S")+"] -> requesting challange")
						msg=msg_i
						con.msg_q.remove(msg_i)
					if(msg_i["cmd"]=="login"):
						print("[A "+time.strftime("%H:%M:%S")+"] -> sending login")
						msg=msg_i
						con.msg_q.remove(msg_i)

			else:	# in this case we have a message waiting and we are logged in and the unacknowledged_msg_queue is short / empty
				msg=con.msg_q[0]
				con.msg_q.remove(msg)

			if(msg!=""):
				#print("A message is ready to send")
				debug.set_last_action("json / encode / sendall")

				send_msg=json.dumps(msg)
				send_msg_enc=send_msg.encode("UTF-8")
				try:
					#print("Wait to send at ",end="")
					#print(time.time(),end="")
					con.sock.sendall(send_msg)
					#	print(" sent " at ",end="")
					#	print(time.time())
				except:
					con.sock=""
					print("init reconnect")
					break
			
				debug.set_last_action("send all done")


				if(msg.get("ack",0)==1): # we want an ack!
					con.unacknowledged_msg.append((msg.get("cmd"),time.time()))
					con.ack_request_ts=time.time()
					#rint("increased con.unacknowledged_msg to "+str(len(con.unacknowledged_msg))+" entries for cmd "+msg["cmd"])

				#print("message send")
				if(msg.get("cmd"," ")=="wf"):
					if(msg.get("eof",0)==1):
						if(TIMING_DEBUG):
							if(time.time()-d.last_pic_taken_ts>15):
								d.active_since_ts=0
								print("reset fps")

							d.last_pic_taken_ts=time.time()
							d.frames_uploaded_since_active=d.frames_uploaded_since_active+1

							if(d.active_since_ts==0):
								d.active_since_ts=time.time()
								d.frames_uploaded_since_active=0
							else:
								print(str(d.frames_uploaded_since_active/(time.time()-d.active_since_ts))+"fps")
#								print("Uploaded "+str(d.frames_uploaded_since_active)+" Frames in "+str((time.time()-d.active_since_ts))+" this is "+str(d.frames_uploaded_since_active*25/(time.time()-d.active_since_ts))+"kBps or "+str(d.frames_uploaded_since_active/(time.time()-d.active_since_ts))+"fps")
#							print("\r\n\r\n")


		############## at this point we consider to upload a picture #####################
		if(len(con.msg_q)==0 and con.logged_in==1):
			if(cam.webview_active==1 and cam.last_picture_taken_ts+cam.interval<time.time()):
				upload_picture(con,0) #highres?
			elif(cam.alarm_pictures_remaining>0 and cam.last_picture_taken_ts+cam.alarm_interval<time.time()):
				cam.alarm_pictures_remaining=max(0,cam.alarm_pictures_remaining-1)
				upload_picture(con,0) #highres?
		############## at this point we consider to upload a picture #####################

		############## free us if there is a lost packet #####################
		if(len(con.unacknowledged_msg)>0 and con.logged_in==1):
			if(len(con.msg_q)>0 and con.ack_request_ts!=0 and con.ack_request_ts+con.SERVER_TIMEOUT<time.time()):
				print("[A "+time.strftime("%H:%M:%S")+"] -> server did not send ack")
				con.unacknowledged_msg=[]
		############## free us if there is a lost packet #####################

		#************* sending end ******************#
	print("connection destroyed, reconnecting")
	debug.set_last_action("connection destroyed")

	cam.webview_active=0 # switch off the webstream, we wouldn't have ws beeing connected to us anyway after resign on
	cam.alarm_pictures_remaining=0

#exit()


