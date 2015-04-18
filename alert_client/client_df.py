# TCP client example
import socket,os,time,json,base64,hashlib,select,trigger
size = 512
client_id="121s3sf"
pw=124
h = hashlib.new('ripemd160')
h.update(str(pw).encode("UTF-8"))
logged_in=0


#******************************************************#
def trigger_handle(path):
	global logged_in
	if(logged_in!=1):
		print("We can't upload as we are not logged in")
		return -1
	repeat=1
	while(repeat>=0):
		img = open(path,'rb')
		try:
			i=0
			while True:
				strng = img.read(size)
				if not strng:
					break
		
				chk_ack=0
				msg={}
				msg["cmd"]="wf"
				msg["fn"]=path
				msg["data"]=base64.b64encode(strng).decode('utf-8')
				msg["eof"]=0
				msg["msg_id"]=i
				if(len(strng)!=size):
					msg["eof"]=1
				chk_ack=1
				msg=json.dumps(msg)	
				#print('sending('+str(i)+')...')
				client_socket.send(msg.encode("UTF-8"))

				if(chk_ack==1):
					#print('waiting('+str(i)+')...')
					data=client_socket.recv(1024)
					#print(data)			
				i+=1

			img.close()
			return 0
		except:
			if(repeat==0):
				logged_in=0
			connect()
			repeat-=1
	# end of while
#******************************************************#
def connect():
	global logged_in
	global client_socket
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect(("192.168.1.80", 9876))

	#### login 
	msg={}
	msg["client_id"]=client_id
	msg["client_pw"]=h.hexdigest()
	msg["cmd"]="login"	
	msg["ts"]=time.strftime("%d.%m.%Y || %H:%M:%S")
	msg=json.dumps(msg)
	client_socket.send(msg.encode("UTF-8"))
	data=client_socket.recv(1024)
	try:
		enc=json.loads(data.decode("UTF-8"))
	except:
		enc=""
	if(type(enc) is dict):
		if(enc.get("cmd")=="login"):
			if(enc.get("ok")==1):
				logged_in=1
				print("logged in")
	#### login 
	

# Main programm
#******************************************************#


while 1:
	connect()	
	print('3..')
	time.sleep(1)		
	print('2..')
	time.sleep(1)		
	print('1..')
	time.sleep(1)		
	print('fire')
	trigger_handle('alert0.jpg')
	exit()
