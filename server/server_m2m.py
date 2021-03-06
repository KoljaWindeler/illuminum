#!/usr/bin/env python
import socket, struct,  threading, cgi, time, os, p
from OpenSSL import SSL 
from select import select
from clients import m2m_clients
from base64 import b64encode
from hashlib import sha1

SERVER_PORT=9875
if(os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"experimental"))):
	SERVER_PORT=9775
	print("!!!!! RUNNING EXPERIMENTAL VERSION OF M2M SERVER!!!!!!")
MAX_CONN=50
MAX_MSG_SIZE=1024000

#******************************************************#
def start():
	threading.Thread(target = start_server, args = ()).start()

#******************************************************#
def start_server ():
	context = SSL.Context(SSL.TLSv1_METHOD)
#	context = SSL.Context(SSL.TLSv1_2_METHOD)
	context.use_privatekey_file('startssl.key')
	context.use_certificate_file('startssl.cert')
	
	s_n = socket.socket()
	s_n.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s_n.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
	s = SSL.Connection(context, s_n)

	s.bind(('', SERVER_PORT))
	s.listen(MAX_CONN) # max clients
	p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] Waiting on m2m_clients on port "+str(SERVER_PORT),"l")
	while 1:
		conn, addr = s.accept()
		#rint(conn.recv(65535))
		new_client=m2m_clients(conn)
		clients.append(new_client)
		p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> Connection from: "+ str(addr[0])+". Serving "+str(len(clients))+" m2m_clients now","l")
		threading.Thread(target = handle, args = (new_client, addr)).start()
		# for what ever that might be good for
		for callb in callback_con:
			callb("connect",new_client)


def disconnect(client):
	try:
		if client.conn:
			client.conn.close()
	except:
		pass
			
	try:
		for callb in callback_con:
			callb("disconnect",client)
	except:
		pass

	try:
		clients.remove(client)
	except:
		pass

	
#******************************************************#
def handle (client, addr):
	lock = threading.Lock()
	busy=1
	while 1:
		try:
			rList, wList, xList = select([client.conn], [client.conn], [client.conn], 3)
		except Exception as n:
			p.warn("S_m2m Select() return an exception for connection "+str(addr)+":"+str(n))
			disconnect(client)
			break

		if(busy==0):
			time.sleep(0.03)
		busy=0
		######################## SEND ###########################
		if(len(wList)>0):
			try:
				if(len(client.sendq)>0):
					busy=1
					payload=client.sendq[0]
					client.sendq.remove(payload)
					
					msg= bytearray()
					# add payload
					for d in bytearray(payload):
				            msg.append(d)
					client.conn.send(msg)
					p.rint("m2m send "+str(len(msg))+" bytes","w")

			except Exception as n:
				print("exception!!!")
				print(n)
			
				disconnect(client)

		######################## SEND ###########################
		####################### RECEIVE ##########################
		if(len(rList)>0):
			busy=1
			lt=""
			try:
				#print(addr,end="")
				#print("server_m2m: rList has "+str(len(rList))+" Elements")
				lt="start _handleData()"
				res = recv_data(client, MAX_MSG_SIZE)
				if(res<0):
					disconnect(client)

			except Exception as n:
				print("exception!!!")
				print(n)

				print("")
				print("except, our status ",end="")
				print(lt,end="")
				print(" sys:",end="")
				print(sys.exc_info()[0])
				print("")

				disconnect(client)

		####################### RECEIVE ##########################
		######################## ERROR ##########################
		if(len(xList)>0):
			busy=1
			try:
				print("exception!!!")
				if client.conn:
					client.conn.close()
				try:
					for callb in callback_con:
						callb("disconnect",client)
				except:
					break;
					pass

				try:
					clients.remove(client)
				except:
					break;
					pass
			except:
				pass
			break;
		######################## ERROR ##########################
		######################## MAINTAINANCE ##########################                
		if(time.time()-client.debug_ts>1):
			client.debug_ts=time.time()
		######################## MAINTAINANCE ##########################
	p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> Client closed:"+str(addr),"l")

	
#******************************************************#
def recv_data (client, length):
	#rint("Wait on data")
	try:
		#rint("before recv ",end="")
		#rint(time.time())
		data = bytearray(client.conn.recv(length))
		#rint("after recv ",end="")
		#rint(time.time())
	except:	
		#p.rint("recv killed","d")
		return -1;
	#rint("[S_m2m] -> Incoming")
	#rint("[S_m2m] -> recv "+str(len(data))+" bytes")
	if(len(data)==0):
		p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> Client disconnected!","l")
		return -1
	
	try:
		data_dec=data.decode("UTF-8")
	except:
		p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> UTF8 decoding failed!","d")
		data_dec=""
	#rint("input:"+data_dec+"<-")
	
	# add everything that we couldn't use from the last message (saved in the buffer)
	data_dec=client.buffer+data_dec
	#rint("[S_m2m] buffer holds "+str(len(data_dec)))

	# split messages at the end of the json identifier
	data_array=data_dec.split('}');
	
	# assume a good return value
	ret=0
	
	#rint("we have "+str(len(data_array))+" elements")
	#for a in range(0,len(data_array)):
		#rint("element "+str(a)+" value: "+data_array[a])
	
	# handle all but the last element
	for a in range(0,len(data_array)-1):
		# re-create the end tag
		data_array[a]+='}'
		#rint("found EOJM")
		
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
		#rint("using buffer!")
	
	return ret
	#end
 

def send_data(client, data):
	client.sendq.append(data)
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
	p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> shutdown","d")
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

def check_clients():
	p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> checking clients","r")
	for cli in clients:
		if(cli.last_comm>0 and cli.last_comm+cli.comm_timeout<time.time()):
			p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] disconnecting client as last comm is older than timeout","r")
			disconnect(cli)
	p.rint("[S_m2m "+time.strftime("%H:%M:%S")+"] -> checking clients done","r")
#******************************************************#

callback_con = [subscribe_callback]
callback_msg = [subscribe_callback]
clients = []
