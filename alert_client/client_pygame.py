# TCP client example
import socket,os,time,json,base64,hashlib,select,trigger
#img = cam.get_image()
#pygame.image.save(img,"test"+str(a)+".jpg")

size = 512
mid="23s54fa59sd"
pw=124
h = hashlib.new('ripemd160')
h.update(str(pw).encode("UTF-8"))
logged_in=0
file_uploading=""
msg_q=[]
file_q=[]
client_socket=""
last_transfer=time.time()

#******************************************************#
def trigger_handle(event,data):
	global msg_q
	if(event=="uploading"):
		file_q.append(data)
	elif(event=="state_change"):
		msg={}
		msg["cmd"]=event
		msg["state"]=data
		msg_q.append(msg)
#******************************************************#
def upload_file(path):
	#print(str(time.time())+" -> this is upload_file with "+path)
	global logged_in
	if(logged_in!=1):
		print("We can't upload as we are not logged in")
		return -1
	img = open(path,'rb')
	i=0
	while True:
		strng = img.read(size)
		if not strng:
			break

		msg={}
		msg["cmd"]="wf"
		msg["fn"]=path
		msg["data"]=base64.b64encode(strng).decode('utf-8')
		msg["eof"]=0
		msg["msg_id"]=i	
		msg["ack"]=-1
		if(len(strng)!=size):
			msg["eof"]=1
		#print('sending('+str(i)+') of '+path+'...')
		msg_q.append(msg)
		#msg=json.dumps(msg)	
		#client_socket.send(msg.encode("UTF-8"))
		i=i+1
	#print(str(time.time())+' all messages for '+path+' are in buffer.. i guess')
	img.close()
	return 0
	# end of while
#******************************************************#
def connect():
	print("[A "+time.strftime("%H:%M:%S")+"] -> connecting ...")
	c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		c_socket.connect(("192.168.1.80", 9875))
	except:
		print("Could not connect to server")
		print("retrying in 3 sec")
		time.sleep(3)
		return -1

	print("[A "+time.strftime("%H:%M:%S")+"] -> connected. Loggin in...")

	#### login 
	msg={}
	msg["mid"]=mid
	msg["client_pw"]=h.hexdigest()
	msg["cmd"]="login"	
	msg["ts"]=time.strftime("%d.%m.%Y || %H:%M:%S")
	msg["ack"]=-1
	msg_q.append(msg)
	#msg=json.dumps(msg)
	#client_socket.send(msg.encode("UTF-8"))
	#data=client_socket.recv(1024)
	#try:
	#	enc=json.loads(data.decode("UTF-8"))
	#except:
	#	enc=""
	#if(type(enc) is dict):
	#	if(enc.get("cmd")=="login"):
	#		if(enc.get("ok")==1):
	#			logged_in=1
	#			print("logged in")
	#### login 
	return c_socket

# Main programm
#******************************************************#

trigger.start()
trigger.subscribe_callback(trigger_handle,"")

comm_wait=0
waiter=[]
hb_out=0

while 1:
	logged_in=0
	client_socket=connect()	
	while(client_socket!=""):
		#************* receiving start ******************#		
		try:
			ready_to_read, ready_to_write, in_error = select.select([client_socket,], [client_socket,], [], 5)
		except:
			print("select detected a broken connection")
			break

		if(len(ready_to_read) > 0):
			#print("one process is ready")
			try:
				recv = client_socket.recv(2048)
				#print("Data received:"+str(recv))
			except:
				print('client_socketection error')
				break;
			
			comm_wait=0
			try:
				enc=json.loads(recv.decode("UTF-8"))
			except:
				enc=""
				break;
			
			if(type(enc) is dict):
				#print("json decoded msg")
				#print(enc)
				if(enc.get("cmd")=="login"):
					if(enc.get("ok")==1):
						logged_in=1
						print("[A "+time.strftime("%H:%M:%S")+"] -> log-in OK")
					else:
						logged_in=0
						print("[A "+time.strftime("%H:%M:%S")+"] -> log-in failed")
				elif(enc.get("cmd")=="hb"):
					last_transfer=time.time()
					hb_out=0
					print("[A "+time.strftime("%H:%M:%S")+"] -> connection OK")
				elif(enc.get("cmd")=="set_detection"):
					print("setting detection to "+str(enc.get("state")))
					trigger.set_detection(enc.get("state"))
				elif(enc.get("cmd")=="wf"):
					ignore=1
				else:
					print("unsopported command:"+enc.get("cmd"))
		#************* receiving end ******************#
		
		#************* timeout check start ******************#
		if(time.time()-last_transfer>60 and hb_out==0):
			print("[A "+time.strftime("%H:%M:%S")+"] -> checking connection")
			msg={}
			msg["cmd"]="hb"
			msg_q.append(msg)
			hb_out=1
		#************* timeout check end ******************#

		#************* file preperation start ******************#
		if(len(file_q)>0):
			file=file_q[0]
			file_q.remove(file)
			upload_file(file)
		#************* file preperation end ******************#

		#************* sending start ******************#
		if(len(msg_q)>0 and (comm_wait==0 or logged_in!=1)):
			msg=""
			#print("We have "+str(len(msg_q))+" waiting...")
			if(logged_in!=1):
				for msg_i in msg_q:
					if(msg_i["cmd"]=="login"):
						print("[A "+time.strftime("%H:%M:%S")+"] -> sending login")
						msg=msg_i
						msg_q.remove(msg_i)
			else:
				msg=msg_q[0]
				msg_q.remove(msg)
			
			if(msg!=""):
				#print("A message is ready to send")
				send_msg=json.dumps(msg)
				try:
					client_socket.send(send_msg.encode("UTF-8"))
				except:
					client_socket=""
					print("init reconnect")
					break
				#print("message send")
				if(json.loads(send_msg).get("ack",0)==-1):
					#print("waiting on response")
					comm_wait=1
				if(json.loads(send_msg).get("cmd"," ")=="wf"):
					if(json.loads(send_msg).get("eof",0)==1):
						print("[A "+time.strftime("%H:%M:%S")+"] -> uploading "+json.loads(send_msg).get("fn")+" done")
		#else:
		#************* sending end ******************#
	print("connection destroyed, reconnecting")		
		
#exit()
