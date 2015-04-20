import time,json,os,base64,hashlib

import server_m2m
import server_ws


#******************************* m2m **********************#
#******************************************************#
# this function handles all incoming messages, they are already decoded
def m2m_msg_handle(data,cli):
	global msg_q_m2m
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
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' HB")
			msg={}
			msg["cmd"]=enc.get("cmd")
			msg["ok"]=1
			msg_q_m2m.append((msg,cli))
		#### wf -> write file, message shall send the fn -> filename and set the EOF -> 1 if it is the last piece of the file
		elif(enc.get("cmd")=="wf"):
			if(cli.logged_in==1):
				if(cli.openfile!=enc.get("fn")):
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
			pw=124 # here is a database request needed!
			h = hashlib.new('ripemd160')
			h.update(str(pw).encode("UTF-8"))
			msg={}
			msg["cmd"]=enc.get("cmd")
			if(h.hexdigest()==enc.get("client_pw")):
				cli.logged_in=1
				cli.id=enc.get("client_id")
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' log-in: OK")
				msg["ok"]=1 # logged in
			else:
				print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' log-in: failed")
				msg["ok"]=-2 # not logged in
			msg_q_m2m.append((msg,cli))


		#### login try to set the logged_in to 1 to upload files etc
		elif(enc.get("cmd")=="state_change"):
			print("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+cli.id+"' changed state to: "+str(enc.get("state")))
		
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
		print("websocket_msg")
#******************************************************#
server_ws.start()
server_ws.subscribe_callback(ws_msg_handle,"msg")
#******************************* WS clients **********************#
	





now = time.time()*2
update_all=0
msg_q_m2m=[]

while 1:
	while(len(msg_q_m2m)>0):
		#print(str(time.time())+' fire in the hole')
		data=msg_q_m2m[0]
		msg=data[0]
		cli=data[1]
		if(server_m2m.send_data(cli,json.dumps(msg).encode("UTF-8"))==0):
			msg_q_m2m.remove(data)
		
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



