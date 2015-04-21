import time,json,os,base64,hashlib

import server_m2m
import server_ws


#******************************* m2m **********************#
#******************************************************#
# this function handles all incoming messages, they are already decoded
def m2m_msg_handle(data,cli):
	global msg_q_m2m, msg_q_ws
	# decode msg from string to dicc
	try:
		enc=json.loads(data)
	except:	
		enc=""
		print("-d--> json decoding failed on:" + data)
	
	#print("cli:"+str(cli.port)+"/"+str(cli.ip))
	if(type(enc) is dict):
		# if the message would like to be debugged
		if(enc.get("debug",0)==1):
			for key, value in enc.items() :
				print("-d-->Key:'"+key+"' / Value:'"+str(value)+"'")
				
		# set last_comm token
		cli.last_comm=time.time()

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
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' HB updating "+str(len(cli.m2v))+" clients")
			msg={}
			msg["cmd"]=enc.get("cmd")
			msg["ok"]=1
			msg_q_m2m.append((msg,cli))

			# tell subscribers
			msg={}
			msg["client_id"]=cli.id
			msg["cmd"]=enc.get("cmd")
			msg["ts"]=time.time()
			for subscriber in cli.m2v:
				#print("Tell that to "+subscriber.login)
				msg_q_ws.append((msg,subscriber))

		#### wf -> write file, message shall send the fn -> filename and set the EOF -> 1 if it is the last piece of the file
		elif(enc.get("cmd")=="wf"):
			if(cli.logged_in==1):
				if(cli.openfile!=enc.get("fn")):
					try:
						cli.fp.close()
					except:
						cli.fp=""
					cli.openfile = enc.get("fn")
					des_location="upload/"+str(int(time.time()))+"_"+cli.id+"_"+cli.openfile
					cli.fp = open(des_location,'wb')
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' is uploading to "+des_location)
					cli.paket_count_per_file=0
				cli.fp.write(base64.b64decode(enc.get("data").encode('UTF-8')))
				if(enc.get("eof")==1):
					cli.fp.close()
					cli.openfile=""
					print("Received "+str(cli.paket_count_per_file)+" parts for this file")
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' finished upload")
					# send good ack
				if(enc.get("ack")==-1):
					msg={}
					msg["cmd"]=enc.get("cmd")
					msg["fn"]=enc.get("fn")
					msg["ok"]=1
					msg_q_m2m.append((msg,cli))

				cli.paket_count_per_file+=1
				#print(str(time.time())+' enqueue')
				#print("received:"+str(enc.get("msg_id")))
				#print("sending ok")
				#server.send_data(cli,json.dumps(msg).encode("UTF-8"))
			else:
				if(enc.get("eof")==1):
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] client tried to upload without beeing logged in")
					# send bad ack
					msg={}
					msg["cmd"]=enc.get("cmd")
					msg["ok"]=-2 # not logged in
					msg_q_m2m.append((msg,cli))
					
		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="login"):
			msg={}
			msg["cmd"]=enc.get("cmd")

			# data base has to give us this values based on enc.get("client_id")
			pw=str(124)
			h = hashlib.new('ripemd160')
			h.update(pw.encode("UTF-8"))
			db={}
			db["pw"]=h.hexdigest()
			db["user_id"]="jkw"
			db["area"]="home"

			# check parameter
			if(db["pw"]==enc.get("client_pw")):
				cli.logged_in=1
				cli.id=enc.get("client_id")
				msg["ok"]=1 # logged in
				# get area and USER_id based on database value for this client-id
				cli.user_id=db["user_id"]
				cli.area=db["area"]
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"'@'"+cli.user_id+"' log-in: OK")
				# search for all (active and logged-in) viewers for this client (same user_id)
				info_viewer=0
				#print("my m2m user id is "+cli.user_id)
				for viewer in server_ws.clients:
					#print("this client has used_id "+viewer.user_id)
					if(viewer.user_id==cli.user_id):
						# introduce them to each other
						connect_ws_m2m(cli,viewer)
						info_viewer+=1
						# we could send a message to the box to tell the if there is a visitor logged in ... but they don't care
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] informed "+str(info_viewer)+" viewer about log-in of "+cli.id)
			else:
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' log-in: failed")
				msg["ok"]=-2 # not logged in
			msg_q_m2m.append((msg,cli))


		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="state_change"):
			# print on console
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' changed state to: "+str(enc.get("state")))

			# tell subscribers
			msg={}
			msg["client_id"]=cli.id
			msg["cmd"]=enc.get("cmd")
			msg["state"]=enc.get("state")
			for subscriber in cli.m2v:
				msg_q_ws.append((msg,subscriber))
		
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
		msg_q_m2m.append((msg,cli))
		
#******************************************************#	
#******************************************************#
def openfile2(cli):
	global update_all
	update_all=1
#******************************************************#
server_m2m.start()
server_m2m.subscribe_callback(m2m_msg_handle,"msg")
server_m2m.subscribe_callback(openfile2,"con")
#******************************* m2m **********************#


#******************************* WS clients **********************#
#******************************************************#
def ws_msg_handle(str,cli):
	try:
		enc=json.loads(str)
	except:
		enc=""
		print("-d--> json decoding failed on:" + data)

        #print("cli:"+str(cli.port)+"/"+str(cli.ip))
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
			cli.login=enc.get("login")
			pw2="124"
			h = hashlib.new('ripemd160')
			h.update(pw2.encode("UTF-8"))
			db={}
			db["pw"]=h.hexdigest()
			db["user_id"]="jkw"

			# check parameter
			if(db["pw"]==enc.get("client_pw") or 1):
				cli.logged_in=1
				msg_ws["ok"]=1 # logged in
				cli.user_id=db["user_id"]
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] '"+cli.login+"'@'"+cli.user_id+"' log-in: OK")
				# search for all (active and logged-in) camera modules with the same user_id and tell them that we'd like to be updated
				# introduce them to each other
				for m2m in server_m2m.clients:
					if(m2m.user_id==cli.user_id):
						connect_ws_m2m(m2m,cli)
			else:
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] '"+cli.login+"' log-in: failed")
				msg_ws["ok"]=-2 # not logged in
			msg_q_ws.append((msg_ws,cli))
		else:
			print("unsupported command: "+enc.get("cmd"))
			

def ws_con_handle(str,cli):
	#print("[A_ws "+time.strftime("%H:%M:%S")+"] connection change")
	if(str=="disconnect"):
		print("[A_ws  "+time.strftime("%H:%M:%S")+"] WS disconneted")
		# try to find that websockets in all client lists, so go through all clients and their lists	
		for m2m in server_m2m.clients:
			for viewer in m2m.m2v:
				if(viewer==cli):
					print("[A_ws  "+time.strftime("%H:%M:%S")+"] releasing '"+m2m.id+"' from "+cli.login)
					m2m.m2v.remove(viewer)
		server_ws.clients.remove(cli)
		
		
#******************************************************#
server_ws.start()
server_ws.subscribe_callback(ws_msg_handle,"msg")
server_ws.subscribe_callback(ws_con_handle,"con")
#******************************* WS clients **********************#
#******************************* common **********************#
def connect_ws_m2m(m2m,ws):
	# add us to their (machine to viewer) list, to be notified whats going on
	m2m.m2v.append(ws) #<- geht das? das wäre jetzt gern ein pointer, vor allem sollten wir vielleicht mal checken ob die schon verbunden waren?
	# and add them to us to give us the change to tell them if they should be sharp or not
	ws.v2m.append(m2m) 
	# send a nice and shiny message to the viewer to tell him what boxes are online, 
	# TODO: how will the user get informed about boxes which are not online? List of db?
	print("[A     "+time.strftime("%H:%M:%S")+"] M2M '"+m2m.id+"' <-> WS '"+ws.login+"'")
	msg_ws2={}
	msg_ws2["cmd"]="m2v_login" #enc.get("cmd")
	msg_ws2["m2m_client"]=m2m.id
	msg_ws2["area"]=m2m.area
	msg_ws2["state"]=m2m.state
	msg_ws2["user_id"]=m2m.user_id
	msg_q_ws.append((msg_ws2,ws))

#******************************* common **********************#
	





now = time.time()*2
update_all=0
msg_q_m2m=[]
msg_q_ws=[]

while 1:
	while(len(msg_q_m2m)>0):
		#print(str(time.time())+' fire in the hole')
		data=msg_q_m2m[0]
		msg=data[0]
		cli=data[1]
		if(0==server_m2m.send_data(cli,json.dumps(msg).encode("UTF-8"))):
			#print("sending something to m2m")
			msg_q_m2m.remove(data)
		else:
			# the cam box m2m unit is not longer available .. obviously, remove it from every viewer and inform them
			for ws in server_ws.clients:
				for viewer in m2m.v2m:
					if(viewer==cli):
						ws.v2m.remove(viewer)
						msg={}
						msg["cmd"]="m2m_disconnect"
						msg["client_id"]=cli.id
						msg_q_ws.append(msg)
			server_m2m.clients.remove(cli)



	while(len(msg_q_ws)>0):
		#print(str(time.time())+' fire in the hole')
		data=msg_q_ws[0]
		msg=data[0]
		cli=data[1]
		#try to submit the data to the websocket client, if that fails, remove that client.. and maybe tell him
		if(0==server_ws.send_data(cli,json.dumps(msg).encode("UTF-8"))):
			msg_q_ws.remove(data)
		else:
			ws_con_handle("disconnect",cli)

			
	#if(time.time()-now>=1 or update_all):
		# execute this once per second 
		#now=time.time()
		#msg={}
		#msg["app"]="ws"
		#msg["cmd"]="update_time"
		#msg["data"]=time.strftime("%d.%m.%Y || %H:%M:%S") 
		#msg=json.dumps(msg)
		#server.send_data_all_clients(msg)

	#for i in range(len(server.clients)):
	#	print("send to client #%d/%d"%(i,len(server.clients)))
	#	server.send_data(server.clients[i],msg)

	#for client in server.clients:
	#	if(time.time()-client.last_comm>10):
	#		print("client "+client.id+" timed out")
	#		client.conn.close()
	#		server.clients.remove(client)
	
	# clean up
	#if(update_all):
	#	update_all=0



