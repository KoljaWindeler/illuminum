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
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"' HB updating "+str(len(cli.m2v))+" clients")
			msg={}
			msg["mid"]=cli.mid
			msg["cmd"]=enc.get("cmd")
			msg["ok"]=1
			msg_q_m2m.append((msg,cli))

			# tell subscribers
			msg={}
			msg["mid"]=cli.mid
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
					des_location="../webserver/upload/"+str(int(time.time()))+"_"+cli.mid+"_"+cli.openfile
					cli.fp = open(des_location,'wb')
					tmp_loc=des_location.split('/')
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"' uploads "+tmp_loc[len(tmp_loc)-1])
					cli.paket_count_per_file=0
				cli.fp.write(base64.b64decode(enc.get("data").encode('UTF-8')))
				if(enc.get("eof")==1):
					# inform all clients
					msg={}
					msg["mid"]=cli.mid
					msg["cmd"]="rf"
					tmp=cli.fp.name.split('/')
					msg["path"]='upload/'+tmp[len(tmp)-1]
					for v in cli.m2v:
						msg_q_ws.append((msg,v))

					cli.fp.close()
					cli.openfile=""
					#print("Received "+str(cli.paket_count_per_file)+" parts for this file")
					print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"' finished upload")	
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

			# data base has to give us this values based on enc.get("mid")
			pw=str(124)
			h = hashlib.new('ripemd160')
			h.update(pw.encode("UTF-8"))
			db={}
			db["pw"]=h.hexdigest()
			db["account"]="jkw"
			db["area"]="home"

			# check parameter
			if(db["pw"]==enc.get("client_pw")):
				cli.logged_in=1
				cli.mid=enc.get("mid")
				msg["ok"]=1 # logged in
				# get area and account based on database value for this mid
				cli.account=db["account"]
				cli.area=db["area"]
				# search for all (active and logged-in) viewers for this client (same account)
				info_viewer=0
				#print("my m2m account is "+cli.account)
				for viewer in server_ws.clients:
					#print("this client has account "+viewer.account)
					if(viewer.account==cli.account):
						# introduce them to each other
						connect_ws_m2m(cli,viewer)
						info_viewer+=1
						# we could send a message to the box to tell the if there is a visitor logged in ... but they don't care
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"'@'"+cli.account+"' log-in: OK (->"+str(info_viewer)+" ws_clients)")
			else:
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"' log-in: failed")
				msg["ok"]=-2 # not logged in
			msg_q_m2m.append((msg,cli))


		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="state_change"):
			# tell subscribers
			msg={}
			msg["mid"]=cli.mid
			msg["cmd"]=enc.get("cmd")
			msg["state"]=enc.get("state")
			informed=0
			for subscriber in cli.m2v:
				msg_q_ws.append((msg,subscriber))
				informed+=1

			# print on console
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.mid+"' changed state to: "+str(enc.get("state"))+" (->"+str(informed)+" ws_clients)")

				
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
def m2m_con_handle(data,cli):
	# this function is is used to be callen if a m2m disconnects, we have to update all ws clients
	#print("[A_m2m "+time.strftime("%H:%M:%S")+"] connection change")
	if(data=="disconnect"):
		print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+str(cli.mid)+"' disconneted")
		# try to find that m2m in all ws clients lists, so go through all clients and their lists	
		for ws in server_ws.clients:
			for viewer in ws.v2m:
				if(viewer==cli):
					print("[A_ws  "+time.strftime("%H:%M:%S")+"] releasing '"+ws.login+"' from "+cli.mid)
					ws.v2m.remove(viewer)
					msg={}
					msg["cmd"]="disconnect"
					msg["mid"]=cli.mid
					msg["area"]=cli.area
					msg["account"]=cli.account
					msg_q_ws.append((msg,ws))
		server_m2m.clients.remove(cli)
#******************************************************#
server_m2m.start()
server_m2m.subscribe_callback(m2m_msg_handle,"msg")
server_m2m.subscribe_callback(m2m_con_handle,"con")
#******************************* m2m **********************#


#******************************* WS clients **********************#
#******************************************************#
def ws_msg_handle(data,cli):
	try:
		enc=json.loads(data)
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
			db["account"]="jkw"

			# check parameter
			if(db["pw"]==enc.get("client_pw") or 1):
				cli.logged_in=1
				msg_ws["ok"]=1 # logged in
				cli.account=db["account"]
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] log-in: OK, '"+cli.login+"'@'"+cli.account+"'")
				# search for all (active and logged-in) camera modules with the same account and tell them that we'd like to be updated
				# introduce them to each other
				for m2m in server_m2m.clients:
					if(m2m.account==cli.account):
						connect_ws_m2m(m2m,cli)
			else:
				print("[A_ws  "+time.strftime("%H:%M:%S")+"] log-in: failed, '"+cli.login+"'")
				msg_ws["ok"]=-2 # not logged in
			msg_q_ws.append((msg_ws,cli))

		## Detection on/off handle
		elif(enc.get("cmd")=="detection"):
			area=enc.get("area")
			# check what m2m clients are in the list of this observer and what area they are in
			clients_affected=0
			for m2m in cli.v2m:
				if(area==m2m.area):
					msg={}
					msg["cmd"]="set_detection"
					msg["state"]=enc.get("state")
					msg_q_m2m.append((msg,m2m))
					clients_affected+=1
			print("[A_ws  "+time.strftime("%H:%M:%S")+"] set detection of area '"+area+"' to '"+str(enc.get("state"))+"' (->"+str(clients_affected)+" m2m_clients)")

		## unsupported cmd
		else:
			print("unsupported command: "+enc.get("cmd"))
			

def ws_con_handle(data,cli):
	# this function is is used to be callen if a ws disconnects, we have to update all m2m clients
	#print("[A_ws "+time.strftime("%H:%M:%S")+"] connection change")
	if(data=="disconnect"):
		#print("[A_ws  "+time.strftime("%H:%M:%S")+"] WS disconneted")
		# try to find that websockets in all client lists, so go through all clients and their lists	
		for m2m in server_m2m.clients:
			for viewer in m2m.m2v:
				if(viewer==cli):
					print("[A_ws  "+time.strftime("%H:%M:%S")+"] releasing '"+m2m.mid+"' from "+cli.login)
					m2m.m2v.remove(viewer)
		try:
			server_ws.clients.remove(cli)
		except:
			ignore=1
		
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
	print("[A     "+time.strftime("%H:%M:%S")+"] MID '"+m2m.mid+"' <-> WS '"+ws.login+"'")
	msg_ws2={}
	msg_ws2["cmd"]="m2v_login" #enc.get("cmd")
	msg_ws2["mid"]=m2m.mid
	msg_ws2["area"]=m2m.area
	msg_ws2["state"]=m2m.state
	msg_ws2["account"]=m2m.account
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
						msg["mid"]=cli.mid
						msg_q_ws.append(msg)
			server_m2m.clients.remove(cli)



	while(len(msg_q_ws)>0):
		#print(str(time.time())+' fire in the hole')
		data=msg_q_ws[0]
		msg=data[0]
		cli=data[1]
		#try to submit the data to the websocket client, if that fails, remove that client.. and maybe tell him
		msg_q_ws.remove(data)
		if(server_ws.send_data(cli,json.dumps(msg).encode("UTF-8"))!=0):
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
	#		print("client "+client.mid+" timed out")
	#		client.conn.close()
	#		server.clients.remove(client)
	
	# clean up
	#if(update_all):
	#	update_all=0



