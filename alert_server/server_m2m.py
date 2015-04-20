#!/usr/bin/env python
 
import socket, struct,  threading, cgi, time, os
from s_clients import s_clients
from base64 import b64encode
from hashlib import sha1

#******************************************************#
def start():
	threading.Thread(target = start_server, args = ()).start()

#******************************************************#
def start_server ():
	s = socket.socket()
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('', 9875))
	s.listen(5) # max clients
	print("[m2m] -> Waiting on clients")
	while 1:
		conn, addr = s.accept()
		new_client=s_clients(conn)
		clients.append(new_client)
		print("[m2m] -> Connection from:"+ str(addr)+" Serving "+str(len(clients))+" clients now")
		threading.Thread(target = handle, args = (new_client, addr)).start()
		# send every subscr
		for callb in callback_con:
			callb(new_client)
	
#******************************************************#
def handle (client, addr):
	lock = threading.Lock()
	while 1:
		res = recv_data(client, 1024)
		if res<0:
			#print("returned:%d"%res)
			break
	print("[m2m] -> Client closed:"+str(addr))
	lock.acquire()
	if(client in clients):
		clients.remove(client)
	lock.release()
	client.conn.close()
	
#******************************************************#
def recv_data (client, length):
	#print("Wait on data")
	try:
		data = bytearray(client.conn.recv(length))
	except:	
		print("recv killed")
		return -1;
	#print("[m2m] -> Incoming")
	if(len(data)==0):
		#print("[m2m] -> len=0 ==> disconnect")
		return -1
	
	data_dec=data.decode("UTF-8")
	#print("input:"+data_dec+"<-")
	
	# add everything that we couldn't use from the last message (saved in the buffer)
	data_dec=client.buffer+data_dec
	# split messages at the end of the json identifier
	data_array=data_dec.split('}');
	
	# assume a bad return value
	ret=-3
	
	#print("we have "+str(len(data_array))+" elements")
	#for a in range(0,len(data_array)):
		#print("element "+str(a)+" value: "+data_array[a])
	
	# handle all but the last element
	for a in range(0,len(data_array)-1):
		# re-create the end tag
		data_array[a]+='}'
		
		# send the message to all subscribers of the msg event
		for callb in callback_msg:	 
			callb(data_array[a],client)
			ret=0
			
	if(data_array[len(data_array)-1]==""):
		#if data contained a full message and ended with closing tag, we are right now looking at an empty element
		client.buffer=""
	else:
		# but if we grabbed something like 1.5 messages, we should buffer the 0.5 message and use it in the next round
		client.buffer=data_array[len(data_array)-1]
		#print("using buffer!")
	
	return ret
	#end
 

def send_data(client, data):
	msg= bytearray()

	# add payload
	#msg.extend(data.encode('utf-8'))
	for d in bytearray(data):
            msg.append(d)
	try:
		#print('-s-->'+str(msg))
		client.conn.send(msg)
	except:
		print("failed")
		return -1

	return 0

def send_data_all_clients(data):
	rem_clients = []
	id_max=len(clients)
	for i in clients:
		if(send_data(i,data)!=0):
			rem_clients.append(i)

	lock = threading.Lock()
	lock.acquire()
	for i in rem_clients:
		if(i in clients):
			clients.remove(i)
	lock.release()
	 
def stop_server():
	send_data_all_clients(bytes("shutdown","UTF-8"))
	print("[m2m] -> shutdown")
	os._exit(1)

def subscribe_callback(fun,method):
	if(method=="msg"):
		if callback_msg[0]==subscribe_callback:
			callback_msg[0]=fun
		else:
			callback_msg.append(fun)
	elif(method=="con"):
		if callback_con[0]==subscribe_callback:
			callback_con[0]=fun
		else:
			callback_con.append(fun)
#******************************************************#

callback_con = [subscribe_callback]
callback_msg = [subscribe_callback]
clients = []



