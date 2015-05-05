import time,json,os,base64,hashlib,string,random
from clients import alert_event,webcam_viewer,m2m_state,det_state
import server_m2m
import server_ws
import send_mail
from sql import *
 
#***************************************************************************************#
#***************************************** m2m *****************************************#
#***************************************************************************************#
# M2M functions are used to handle all messages between the server machine and the
# camera machine, M<->M. There should be no user interaction involved, as every message
# shall go over this server.
# There is a thread called server_m2m running in the background and waiting for incoming
# packets (low level). Whenever new camera is coming online the function recv_m2m_con_q_handle
# shall be triggered. This function will queue the data to recv_m2m_con_q and finish.
#
# The main loop shall run the function recv_m2m_con_dq_handle and check if our queue has
# elements to be processed. if this is the case the function will call recv_m2m_con_handle
# to process the connection change.
#
# The same principal is used to receive messages from the clients
#
# If recv_m2m_con_handle or recv_m2m_msg_handle or anyone else has to send something back
# to the cam, then they should append a message to the msq_q_m2m structure
# This structure will be checked by the main loop as well and if it contains some they
# will be send to the correct m2m device mentioned in the CLI argument. This way all messages
# and state changes are aligned in FIFO structures
#******************************************************#

################## M2M CONNECTION #########################
#******************************************************#
# recv_m2m_con_q_handle will be called by the server structure and shall just append
# the message to the queue
def recv_m2m_con_q_handle(data,m2m):
	recv_m2m_con_q.append((data,m2m))
#******************************************************#

#******************************************************#
# recv_m2m_con_dq_handle will be called in the main loop and will forward a message
# to the recv_m2m_con_handle if there is one in the queue
def recv_m2m_con_dq_handle():
	ret=0
	if(len(recv_m2m_con_q)>0):
		ret=1
		recv_con=recv_m2m_con_q[0]
		recv_m2m_con_q.remove(recv_con)
		recv_m2m_con_handle(recv_con[0],recv_con[1])
	return ret
#******************************************************#

#******************************************************#
# recv_m2m_con_handle will be called by the dequeue handle above.
# it shall handle disconnect situations to avoid that we are talking to dead sockets
def recv_m2m_con_handle(data,m2m):
	# this function is is used to be callen if a m2m disconnects, we have to update all ws clients
	#print("[A_m2m "+time.strftime("%H:%M:%S")+"] connection change")
	if(data=="disconnect"):
		print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+str(m2m.mid)+"' disconneted")
		# try to find that m2m in all ws clients lists, so go through all clients and their lists
		for ws in server_ws.clients:
			for viewer in ws.v2m:
				if(viewer==m2m):
					print("[A_ws  "+time.strftime("%H:%M:%S")+"] releasing '"+ws.login+"' from "+m2m.mid)
					ws.v2m.remove(viewer)
					msg={}
					msg["cmd"]="disconnect"
					msg["mid"]=m2m.mid
					msg["area"]=m2m.area
					msg["account"]=m2m.account
					msg_q_ws.append((msg,ws))
		try:
			server_m2m.clients.remove(m2m)
		except:
			ignore=1
		# update database
		# TODO database shall set state to "disconnected" and last seen to time.time()
		#sql.m2m_disconnect(m2m.mid)
#******************************************************#
################## M2M CONNECTION #########################

################## M2M MESSAGE #########################
#******************************************************#
# recv_m2m_msg_q_handle will be called by the server structure shall just append
# the message to the queue
def recv_m2m_msg_q_handle(data,m2m):
	recv_m2m_msg_q.append((data,m2m))
#******************************************************#

#******************************************************#
# recv_m2m_msg_dq_handle will be called in the main loop and will forward a message
# to the recv_m2m_handle if there is one in the queue
def recv_m2m_msg_dq_handle():
	ret=0
	if(len(recv_m2m_msg_q)>0):
		ret=1
		recv_msg=recv_m2m_msg_q[0]
		recv_m2m_msg_q.remove(recv_msg)
		recv_m2m_msg_handle(recv_msg[0],recv_msg[1])
	return ret
#******************************************************#

#******************************************************#
# this function, called by the dequeue above will handles all
# incoming messages and generate responses, which will be stored in the msg_q_m2m
def recv_m2m_msg_handle(data,m2m):
	global msg_q_m2m, msg_q_ws
	# decode msg from string to dicc
	try:
		enc=json.loads(data)
	except:
		enc=""
		print("-d--> json decoding failed on:" + data)

	#print("m2m:"+str(m2m.port)+"/"+str(m2m.ip))
	if(type(enc) is dict):
		# if the message would like to be debugged
		if(enc.get("debug",0)==1):
			for key, value in enc.items() :
				print("-d-->Key:'"+key+"' / Value:'"+str(value)+"'")

		# set last_comm token
		m2m.last_comm=time.time()

		#********* msg handling **************#
		# assuming that we could decode the message from json to dicc: we have to distingush between the commands:

		#### sd -> shut the server down
		if(enc.get("cmd")=="sd"):
			print("[main] running shutdown")
			server_m2m.stop_server()
			exit()

		#### heartbeat
		elif(enc.get("cmd")=="hb"):
			# respond
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' HB updating "+str(len(m2m.m2v))+" clients")
			msg={}
			msg["mid"]=m2m.mid
			msg["cmd"]=enc.get("cmd")
			msg["ok"]=1
			msg_q_m2m.append((msg,m2m))

			# tell subscribers
			msg={}
			msg["mid"]=m2m.mid
			msg["cmd"]=enc.get("cmd")
			msg["ts"]=time.time()
			for subscriber in m2m.m2v:
				#print("Tell that to "+subscriber.login)
				msg_q_ws.append((msg,subscriber))

		#### wf -> write file, message shall send the fn -> filename and set the EOF -> 1 if it is the last piece of the file
		elif(enc.get("cmd")=="wf"):
			if(m2m.logged_in==1):
				if(m2m.openfile!=enc.get("fn")):
					try:
						m2m.fp.close()
					except:
						m2m.fp=""
					m2m.openfile = enc.get("fn")
					des_location="../webserver/upload/"+str(int(time.time()))+"_"+m2m.mid+"_"+m2m.openfile
					m2m.fp = open(des_location,'wb')

					# this is the start of a transmission
					# a client in ALERT state will send UP TO N pictures, but might be disconnected before he finished.
					# we'll put every alert file filename in the m2m.alert_img list  and check in the loop if that list
					# has reached 5 pics, or hasn't been updated for > 20 sec.
					# if those conditions are satifies we'll check if the mail optioin is active and if so mail it to
					# the given address. after that we set the m2m.alert_mail_send to 1 state change to low should clear that
					if(m2m.state==1): # ALERT
						if(m2m.alert.notification_send_ts<=0): # not yet send, append fn to list and save timestamp
							m2m.alert.files.append(des_location)
							m2m.alert.last_upload = time.time()
					#tmp_loc=des_location.split('/')
					#print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' uploads "+tmp_loc[len(tmp_loc)-1])
					m2m.paket_count_per_file=0
				m2m.fp.write(base64.b64decode(enc.get("data").encode('UTF-8')))
				if(enc.get("eof")==1):
					# inform all clients
					msg={}
					msg["mid"]=m2m.mid
					msg["cmd"]="rf"
					msg["state"]=m2m.state
					# all image data
					if(enc.get("sof",0)==1):
						#send img, assuming this is a at once img
						msg["img"]=enc.get("data")
					else:
						#send path if it was hacked ... not wise TODO: read img and send at once
						tmp=m2m.fp.name.split('/')
						msg["path"]='upload/'+tmp[len(tmp)-1]

					# select the ws to send to
					if(m2m.state==1): # alert -> inform everyone
						# the m2v list has all viewer
						for v in m2m.m2v:
							if(v.snd_q_len<10):
								msg_q_ws.append((msg,v))
								v.snd_q_len+=1
					else: # webcam -> use webcam list as the m2v list has all viewer, but the webcam has those who have requested the feed
						for v in m2m.webcam:
							#only update if last ts war more then interval ago
							#try:
							ts_photo=enc.get("td",0)
							ts_photo=ts_photo[1][0]
							t_passed=ts_photo-v.ts+0.1
							if(t_passed>=v.interval and v.ws.snd_q_len<10): #todo .. only if queue is not too full
								v.ts=ts_photo
								v.ws.snd_q_len+=1
								msg_q_ws.append((msg,v.ws))
							else:
								print("skipping "+str(v.ws.login)+": "+str(t_passed)+" / "+str(v.ws.snd_q_len))

					des_location=m2m.fp.name
					tmp_loc=des_location.split('/')
					m2m.fp.close()
					m2m.openfile=""
					#print("Received "+str(m2m.paket_count_per_file)+" parts for this file")
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' uploaded "+tmp_loc[len(tmp_loc)-1])
					# send good ack
				if(enc.get("ack")==-1):
					msg={}
					msg["cmd"]=enc.get("cmd")
					msg["fn"]=enc.get("fn")
					msg["ok"]=1
					msg_q_m2m.append((msg,m2m))

				m2m.paket_count_per_file+=1
				#print(str(time.time())+' enqueue')
				#print("received:"+str(enc.get("msg_id")))
				#print("sending ok")
				#server.send_data(m2m,json.dumps(msg).encode("UTF-8"))
			else:
				if(enc.get("eof")==1):
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] client tried to upload without beeing logged in")
					# send bad ack
					msg={}
					msg["cmd"]=enc.get("cmd")
					msg["ok"]=-2 # not logged in
					msg_q_m2m.append((msg,m2m))


		#### pre login challange
		elif(enc.get("cmd")=="prelogin"):
			m2m.challange=get_challange()
			msg={}
			msg["cmd"]=enc.get("cmd")
			msg["challange"]=m2m.challange
			msg_q_m2m.append((msg,m2m))
			#print("received prelogin request, sending challange "+m2m.challange)

		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="login"):
			msg={}
			msg["cmd"]=enc.get("cmd")

			# data base has to give us this values based on enc.get("mid")
			db_r=db.get_data(enc.get("mid"))
			#print("Ergebniss der datenbank:")
			#print(db_r)

			if(db_r==-1): #user not found
				#print("db error")
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+str(enc.get("mid"))+"' not found in DB, log-in: failed")
				msg["ok"]=-3 # not logged in
			else:
				h = hashlib.new('ripemd160')
				h.update(str(db_r["pw"]+m2m.challange).encode("UTF-8"))
				#print("total to code="+(str(db["pw"]+m2m.challange)))
				#print("result="+h.hexdigest()+" received: "+enc.get("client_pw"))

				# check parameter
				if(h.hexdigest()==enc.get("client_pw")):
					m2m.logged_in=1
					m2m.mid=enc.get("mid")
					m2m.state=enc.get("state")
					m2m.alert=alert_event()
					msg["ok"]=1 # logged in

					# get area and account based on database value for this mid
					m2m.account=db_r["account"]
					m2m.area=db_r["area"]
					m2m.alias=db_r["alias"]

					# get detecion state based on db
					db_r2=db.get_state(m2m.area,m2m.account)
					msg["detection"]=int(db_r2["state"])

					# search for all (active and logged-in) viewers for this client (same account)
					info_viewer=0
					#print("my m2m account is "+m2m.account)
					for viewer in server_ws.clients:
						#print("this client has account "+viewer.account)
						if(viewer.account==m2m.account):
							# introduce them to each other
							connect_ws_m2m(m2m,viewer)
							info_viewer+=1
							# we could send a message to the box to tell the if there is a visitor logged in ... but they don't care
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"'@'"+m2m.account+"' log-in: OK (->"+str(info_viewer)+" ws_clients)")
					db.update_last_seen(m2m.mid,m2m.conn.getpeername()[0])
				else:
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+str(m2m.mid)+"' log-in: failed")
					msg["ok"]=-2 # not logged in
			# send message in any case
			msg_q_m2m.append((msg,m2m))


		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="state_change"):
			m2m.state=enc.get("state")
			# tell subscribers
			msg={}
			msg["mid"]=m2m.mid
			msg["cmd"]=enc.get("cmd")
			msg["state"]=enc.get("state")
			informed=0
			for subscriber in m2m.m2v:
				msg_q_ws.append((msg,subscriber))
				informed+=1

			# prepare notification system, arm or disarm
			if(m2m.state==1): # state=1 means Alert!
				m2m.alert.ts=time.time()
				m2m.alert.files = []
				m2m.alert.notification_send_ts = -1 # indicates that this is a thing to be done
				m2m.alert.last_upload=0
			elif(m2m.state==2 or m2m.state==3): #state 2 or 3 means: offline (+idle/+alert)
				# assuming that the system was already triggered and right after that the switch off command arrived -> avoid notification
				# check_alerts will search for m2m with notification_send_ts==-1
				m2m.alert.notification_send_ts = 0 # indicate that this is done


			# print on console
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' changed state to: '"+str(m2m_state[enc.get("state",4)])+"' (->"+str(informed)+" ws_clients)")


		#### unsupported command
		else:
				print("unsupported command: "+enc.get("cmd"))
		#********* msg handling **************#
	#### comm error
	else:
		print("-d--> json decode error")
		msg={}
		msg["cmd"]=enc.get("cmd")
		msg["ok"]=-1 #comm error
		msg_q_m2m.append((msg,m2m))
#******************************************************#

#******************************************************#
# last but not least we have to send messages to the M2M
# this is done by the snd_m2m_msg_dq_handle. it will check if there
# is a message and forward it to the server
def snd_m2m_msg_dq_handle():
	ret=0
	if(len(msg_q_m2m)>0):
		ret=1
		#print(str(time.time())+' fire in the hole')
		data=msg_q_m2m[0]
		msg_q_m2m.remove(data)

		msg=data[0]
		m2m=data[1]
		if(0!=server_m2m.send_data(m2m,json.dumps(msg).encode("UTF-8"))):
			# the cam box m2m unit is not longer available .. obviously, remove it from every viewer and inform them
			recv_m2m_con_handle("disconnect",m2m)
	return ret
#******************************************************#
#***************************************************************************************#
#************************************** end of m2m *************************************#
#***************************************************************************************#


#***************************************************************************************#
#************************************** WebSockets *************************************#
#***************************************************************************************#
# introduction text required

#******************************************************#
# the websocket server will call this funcion to put new incoming connection in the queue
def recv_ws_con_q_handle(data,ws):
	recv_ws_con_q.append((data,ws))
#******************************************************#

#******************************************************#
# the main loop will call the dequeue to check if there are new connection changes
def recv_ws_con_dq_handle():
	ret=0
	if(len(recv_ws_con_q)>0):
		ret=1
		recv_con=recv_ws_con_q[0]
		recv_ws_con_q.remove(recv_con)
		recv_ws_con_handle(recv_con[0],recv_con[1])
	return ret
#******************************************************#

#******************************************************#
# dequeue above will call us to process the new connection
def recv_ws_con_handle(data,ws):
	# this function is is used to be callen if a ws disconnects, we have to update all m2m clients and their webcam lists
	#print("[A_ws "+time.strftime("%H:%M:%S")+"] connection change")
	if(data=="disconnect"):
		print("[A_ws  "+time.strftime("%H:%M:%S")+"] WS disconneted")
		# try to find that websockets in all client lists, so go through all clients and their lists
		for m2m in server_m2m.clients:
			for viewer in m2m.m2v:
				if(viewer==ws):
					print("[A_ws  "+time.strftime("%H:%M:%S")+"] releasing '"+m2m.mid+"' from "+ws.login)
					m2m.m2v.remove(viewer)

					# also check if that ws has been one of the watchers of the webfeed
					set_webcam_con(m2m.mid,0,ws)

		try:
			server_ws.clients.remove(ws)
		except:
			ignore=1
#******************************************************#

#******************************************************#
# websocket server will call this function if new websocket messages arrived
# we will store them in the queue
def recv_ws_msg_q_handle(data,ws):
	recv_ws_msg_q.append((data,ws));
#******************************************************#

#******************************************************#
# and the main loop will call dequeue them if there are any and call msg_handle
def recv_ws_msg_dq_handle():
	ret=0
	if(len(recv_ws_msg_q)>0):
		ret=1
		recv_msg=recv_ws_msg_q[0]
		recv_ws_msg_q.remove(recv_msg)
		recv_ws_msg_handle(recv_msg[0],recv_msg[1])
	return ret
#******************************************************#

#******************************************************#
# callen by the dequeue above
def recv_ws_msg_handle(data,ws):
	global db
	try:
		enc=json.loads(data)
	except:
		enc=""
		print("-d--> json decoding failed on:" + data)

		#print("ws:"+str(ws.port)+"/"+str(ws.ip))
	if(type(enc) is dict):
		if(enc.get("debug",0)==1):
			print("websocket_msg")
			for key, value in enc.items() :
				print("-d-->Key:'"+key+"' / Value:'"+str(value)+"'")
		## AREA CHANGE ##
		if(enc.get("cmd"," ")=="area_change"):
			print("websocket announced area change")
			msg={}
			msg["cmd"]=enc.get("cmd")
		## LOGIN from a viewer ##
		elif(enc.get("cmd")=="login"):
			msg_ws={}
			msg_ws["cmd"]=enc.get("cmd")
			# data base has to give us this values
			ws.login=enc.get("login")
			pw2="124"
			h = hashlib.new('ripemd160')
			h.update(pw2.encode("UTF-8"))
			db_f={}
			db_f["pw"]=h.hexdigest() # todo get those data from sql
			db_f["account"]="jkw"

			# check parameter
			if(db_f["pw"]==enc.get("client_pw") or 1):
				ws.logged_in=1
				msg_ws["ok"]=1 # logged in
				ws.account=db_f["account"]
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] log-in: OK, '"+ws.login+"'@'"+ws.account+"'")
				# search for all (active and logged-in) camera modules with the same account and tell them that we'd like to be updated
				# introduce them to each other
				for m2m in server_m2m.clients:
					if(m2m.account==ws.account):
						connect_ws_m2m(m2m,ws)
				# and finally connect all disconnected m2m to the ws
				connect_ws_m2m("",ws)
			else:
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] log-in: failed, '"+ws.login+"'")
				msg_ws["ok"]=-2 # not logged in
			msg_q_ws.append((msg_ws,ws))

		## Detection on/off handle
		elif(enc.get("cmd")=="detection"):
			area=enc.get("area")
			# step 1: update database
			db.update_det(ws.login,ws.account,area,enc.get("state"))
			# check what m2m clients are in the list of this observer and what area they are in
			clients_affected=0
			for m2m in ws.v2m:
				if(area==m2m.area):
					msg={}
					msg["cmd"]="set_detection"
					msg["state"]=enc.get("state")
					msg_q_m2m.append((msg,m2m))
					clients_affected+=1
			print("[A_ws  "+time.strftime("%H:%M:%S")+"] set detection of area '"+area+"' to '"+str(enc.get("state"))+"' (->"+str(clients_affected)+" m2m_clients)")

		## webcam interval -> sign in or out to webcam
		elif(enc.get("cmd")=="set_interval"):
			set_webcam_con(enc.get("mid"),enc.get("interval",0),ws)

		## if a ws client supports location grabbing it can send location updates to switch on/off the detection
		elif(enc.get("cmd")=="update_location"):
			print("[A_ws  "+time.strftime("%H:%M:%S")+"] '"+ws.login+"'@'"+ws.account+"' moved to '"+enc.get("loc")+"'")
			# step 1: update database location for this login
			db_r=db.update_location(ws.login,enc.get("loc"))
			# step 2: get all possible areas for this user
			db_r=db.get_areas_for_account(ws.account)
			# step 3: for each possible area get all usercounts with location
			for entry in db_r:
				area=entry["area"]
				# step 4: check if the area is on "automatic?" TODO
				# assume so
				#print("looking for "+str(area))
				user_count=db.user_count_on_area(ws.account,area)
				#print("user_count_on_area gave us:")
				#print(user_count)
				#print("eoo")
				user_count=user_count["COUNT(*)"]
				#print("meaning")
				#print(user_count)
				#print("eoo")

				# step 5: if user count == 0 set active, else set inactive
				# assume deactivation of alarm system
				detection_state=0
				if(user_count==0):
					# start alarm system
					detection_state=2

				# step 6: update database
				db.update_det(ws.login,ws.account,area,detection_state)

				# step 7: go through all connected units and check which of them is in the current area
				clients_affected=0
				#print("suche durch alle v2m, len="+str(len(ws.v2m)))
				for m2m in ws.v2m:
					#print("client "+m2m.alias+" sitzt in area "+m2m.area)
					if(area==m2m.area):
						#print("die suchen wir!")
						msg={}
						msg["cmd"]="set_detection"
						msg["state"]=detection_state
						# step 8 append message for this m2m client to go sharp ;)
						msg_q_m2m.append((msg,m2m))

						clients_affected+=1
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] set detection of area '"+area+"' to '"+str(det_state[detection_state])+"' (->"+str(clients_affected)+" m2m_clients)")


		## unsupported cmd
		else:
			print("[A     "+time.strftime("%H:%M:%S")+"] unsupported command: "+enc.get("cmd"))
#******************************************************#

#******************************************************#
# and here again: the main loop will call us to check if there is a message to send back
def snd_ws_msg_dq_handle():
	ret=0
	if(len(msg_q_ws)>0):
		ret=1
		#print(str(time.time())+' fire in the hole')
		data=msg_q_ws[0]
		msg=data[0]
		cli=data[1]
		#try to submit the data to the websocket client, if that fails, remove that client.. and maybe tell him
		msg_q_ws.remove(data)
		cli.snd_q_len=max(0,cli.snd_q_len-1)
		if(server_ws.send_data(cli,json.dumps(msg).encode("UTF-8"))!=0):
			recv_ws_con_handle("disconnect",cli)
	return ret
#******************************************************#
#***************************************************************************************#
#*********************************** End of WebSockets *********************************#
#***************************************************************************************#

#***************************************************************************************#
#**************************************** Common  **************************************#
#***************************************************************************************#
# common function more than one of ws or m2m uses

#******************************************************#
# when ever a websocket or a m2m device signs-on this function will be called
# the purpose is that the web socket shall be informed about the new, available client
# and the m2m shall know that there is a viewer to inform
def connect_ws_m2m(m2m,ws):
	if(m2m!=""): # first lets assume that we shall connect a given pair right here
		# add us to their (machine to viewer) list, to be notified whats going on
		m2m.m2v.append(ws)
		# and add them to us to give us the change to tell them if they should be sharp or not
		ws.v2m.append(m2m)
		# send a nice and shiny message to the viewer to tell him what boxes are online,
		print("[A     "+time.strftime("%H:%M:%S")+"] MID '"+m2m.mid+"' <-> WS '"+ws.login+"'")
		msg_ws2={}
		msg_ws2["cmd"]="m2v_login"
		msg_ws2["mid"]=m2m.mid
		msg_ws2["area"]=m2m.area
		msg_ws2["state"]=m2m.state
		msg_ws2["account"]=m2m.account
		msg_ws2["alias"]=m2m.alias
		msg_ws2["last_seen"]=m2m.last_comm
		msg_q_ws.append((msg_ws2,ws))
	else: # this will be called at the very end of a websocket sign-on, it shall add all non connected boxes to the websocket.
		# TODO: how will the user get informed about boxes which are not online? List of db?
		# 1. get all boxed with the same account
		all_m2m4account=db.get_m2m4account(ws.account)
		if(all_m2m4account==-1):
			print("Error getting data for account "+ws.account)
		else:
			# 2. loop through them and make sure that they are not part of the list, that the ws already knows
			for m2m in all_m2m4account:
				found=0
				for am2m in ws.v2m:
					if(m2m["mid"]==am2m.mid):
						found=1
						break
				if(not(found)):
					msg_ws2={}
					msg_ws2["cmd"]="m2v_login"
					msg_ws2["mid"]=m2m["mid"]
					msg_ws2["area"]=m2m["area"]
					msg_ws2["alias"]=m2m["alias"]
					msg_ws2["state"]=-1
					msg_ws2["account"]=ws.account
					msg_ws2["last_seen"]=m2m["last_seen"]
			# 3. send data to the websocket
					msg_q_ws.append((msg_ws2,ws))
#******************************************************#

#******************************************************#
# this will be called if the websocket requests a webcam stream OR if he had done it before and disconnects
# purpose of this function is to ADD or REMOVE the websocket to the list "webcam" of the m2m unit and to tell
# the cam at what speed it shall run. BTW: there is a problem with the KGV .. but not important.
def set_webcam_con(mid,interval,ws):
	#print("--> change interval "+str(interval))
	msg={}
	msg["cmd"]="set_interval"
	#search for the m2m module that shall upload the picture to the ws
	for m2m in ws.v2m:
		if(m2m.mid==mid):
			#print("habe die angeforderte MID in der clienten liste vom ws gefunden")
			# thats our m2m cam
			if(interval>0):
				# scan if we are already in the webcam list, and remove us if so
				for wcv in m2m.webcam:
					if(wcv.ws==ws):
						m2m.webcam.remove(wcv)

				# put the ws on his list of webcam subscripters
				viewer=webcam_viewer(ws)
				viewer.interval=interval
				viewer.ts=0 # deliver the next frame asap
				m2m.webcam.append(viewer) 

				# find fastest webcam viewer
				sm_interval=9999
				for wcv in m2m.webcam:
					if(wcv.interval<interval):
						sm_interval=wcv.interval
				#check if our interval is even faster
				if(sm_interval>interval):
					#we requested a faster rate than every one else
					msg["interval"]=interval
					# inform the webcam that we are watching
					msg_q_m2m.append((msg,m2m))

				print("[A_ws  "+time.strftime("%H:%M:%S")+"] Added "+ws.login+" to webcam stream from "+mid)
					
			# this clients switched off 
			else:
				# remove us from the list 
				# go through all elements in the webcam list 
				#print("suche in der webcam liste nach unserem ws")
				for viewer in m2m.webcam:
					if(viewer.ws==ws):
						#print("gefunden und entfernt")
						m2m.webcam.remove(viewer)

						# check if we shall switch of the feed
						clients_remaining=len(m2m.webcam)
						if(clients_remaining==0):
							msg["interval"]=0
							#print("sende stop nachricht an m2m:"+str(m2m.mid))
						else:
							#find fastest webcam viewer
							sm_interval=9999
							for wcv in m2m.webcam:
								if(wcv.interval<sm_interval):
									sm_interval=wcv.interval
							msg["interval"]=sm_interval

						msg_q_m2m.append((msg,m2m))
						print("[A_ws  "+time.strftime("%H:%M:%S")+"] Removed "+ws.login+" from webcam stream of "+m2m.mid+" ("+str(clients_remaining)+" ws left)")
#******************************************************#

#******************************************************#
# get_challange is used to avoid that the clients send their password or even an encripted version of it.
# first they request a challange (generated by this function) which will be send back to the client, than
# the client will append his password to it and encode that. this makes sure that the loginpw is different
# at all logins and nobody can just repeat the login sequence
def get_challange(size=12, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
#******************************************************#

#******************************************************#
# this function will be called in the main loop and shall check if there is a client in the state that he
# started to capture a few images and might be ready to send them via mail / notification
def check_alerts():
	ret=-1
	for cli in server_m2m.clients:
		if(cli.alert.notification_send_ts==-1):
			# found client in "alert but not yet notified" state, see if it is time to notify
			send = 0
			# if the gab between the last_upload and now is > timeout
			if(cli.alert.last_upload!=0):
				if(time.time()>cli.alert.last_upload+cli.alert.file_max_timeout_ms/1000):
					#print("last upload ist old enough")
					send=1
			# or enough pictures have been uploaded
			if(len(cli.alert.files)>=cli.alert.files_expected):
				#print("found enough files")
				send=1

			# fire in the hole
			if(send==1):
				# email?
				if(cli.alert.comm_path % 2 == 1):
					#print("sending mail")
					#send_mail.send( subject, text, files=[], send_to="KKoolljjaa@gmail.com",send_from="koljasspam493@gmail.com", server="localhost"):
					send_mail.send("alert", "oho", cli.alert.files)
					cli.alert.notification_send_ts=time.time()
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+str(cli.mid)+"' triggered Email")
					ret=0
		return ret

####################				
#***************************************************************************************#
#************************************ End of Common  ***********************************#
#***************************************************************************************#

#***************************************************************************************#
#************************************** Variables **************************************#
#***************************************************************************************#
# M2M structures
recv_m2m_msg_q=[]	# incoming
recv_m2m_con_q=[]	# incoming
msg_q_m2m=[]		# outgoing
server_m2m.start()
server_m2m.subscribe_callback(recv_m2m_msg_q_handle,"msg")
server_m2m.subscribe_callback(recv_m2m_con_q_handle,"con")

# WS structures
recv_ws_msg_q=[]	# incoming
recv_ws_con_q=[]	# incoming
msg_q_ws=[] 		# outgoing
server_ws.start()
server_ws.subscribe_callback(recv_ws_msg_q_handle,"msg")
server_ws.subscribe_callback(recv_ws_con_q_handle,"con")

# DB Structure used for the login
db=sql()
db.connect()

# else
busy=1

#***************************************************************************************#
#********************************** End of Variables ***********************************#
#***************************************************************************************#

#***************************************************************************************#
#************************************** Main loop **************************************#
#***************************************************************************************#
while 1:
	# sleeping
	if(busy==0):
		time.sleep(0.03)
	busy=0

	############### recv ###################
	if(recv_m2m_con_dq_handle()==1): #returns 1 if there was a connection change by a m2m unit
		busy=1

	if(recv_m2m_msg_dq_handle()==1): #returns 1 if there was a message to receive from a m2m unit
		busy=1

	if(recv_ws_con_dq_handle()==1): #returns 1 if there was a connection change by a web socket client
		busy=1

	if(recv_ws_msg_dq_handle()==1):  #returns 1 if there was a message to receive from a web socket client
		busy=1

	############## send ###################
	if(snd_m2m_msg_dq_handle()==1): #returns 1 if there was a message to send
		busy=1

	if(snd_ws_msg_dq_handle()==1): #returns 1 if there was a message to send
		busy=1

	############## maintenance ###################
	# check if we have clients in the alert state ready to send a mail or so
	if(check_alerts()==0):
		busy=1
	
#***************************************************************************************#
#********************************** End of Main loop ***********************************#
#***************************************************************************************#
