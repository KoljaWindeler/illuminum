# TCP client example
import socket,os,time,json
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("192.168.1.80", 9876))
size = 512

while(1):
	print ("und los")
	print("send <sd>")
	msg={}
	msg["client_id"]="123"
	msg["cmd"]="sd"
	msg["ts"]=time.strftime("%d.%m.%Y || %H:%M:%S") 
	msg=json.dumps(msg)	
	client_socket.send(bytes(msg,"UTF-8"))
		
		
	data = bytearray(client_socket.recv(512)).decode('utf-8')
	print("received server message: "+data)
	exit()
