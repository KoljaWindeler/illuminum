#!/usr/bin/env python
#import ssl
from OpenSSL import SSL
import socket, struct,  threading, cgi, time, p, sys, traceback
from clients import ws_clients
from base64 import b64encode
from hashlib import sha1

import hashlib
import base64
import socket
import struct
import ssl
import sys
import errno
import codecs
from collections import deque
from select import select

PORT=9879	

MAX_CLIENTS=5

_VALID_STATUS_CODES = [1000, 1001, 1002, 1003, 1007, 1008, 1009, 1010, 1011, 3000, 3999, 4000, 4999]

STREAM = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xA

HEADERB1 = 1
HEADERB2 = 3
LENGTHSHORT = 4
LENGTHLONG = 5
MASK = 6
PAYLOAD = 7
  
MAXHEADER = 65536
MAXPAYLOAD = 33554432

#************* EXPOSED METHODS *****************************************# 
def send_data(client, data):
	if client in clients:
		client.ws.sendMessage(data)
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
#************* EXPOSED METHODS *****************************************#

#************* DISCONNECT *****************************************#
def disconnect(client):
	try:
		if client.ws.sock:
			client.ws.sock.close()
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
	client.alive = 0
#************* DISCONNECT *****************************************#

#************* HANDLE CONNECTION *****************************************#
def handle (client,addr):
	t1=0
	t2=0

	busy=1
	#lock = threading.Lock()
	while client.alive:
		try:
			rList, wList, xList = select([client.ws.sock], [client.ws.sock], [client.ws.sock], 3)
		except:
			break;

		if(busy==0):
			time.sleep(0.03)
		busy=0
		######################## SEND ###########################
		if(len(wList)>0):
			try:
				t1=time.time()
				while client.ws.sendq:
					busy=1
					opcode, payload = client.ws.sendq.popleft()
					remaining = client.ws._sendBuffer(payload)
					if remaining is not None:
						client.ws.sendq.appendleft((opcode, remaining))
						break
					else:
						if opcode == CLOSE:
							for callb in callback_con:
								callb("disconnect",client)
				t1=time.time()-t1
			except Exception as n:
				disconnect(client)
		######################## SEND ###########################
		####################### RECEIVE ##########################
		if(len(rList)>0):
			busy=1
			lt=""
			try:
				lt="start _handleData()"
				t2=time.time()
				if(client.ws._handleData()==-1):
					disconnect(client)
					
				while(client.ws.data_ready==True):
					lt="Start getMessage()"
					msg=client.ws.getMessage() # getMessage will unset the data_ready flag if no data left
					if(client.ws.data_ready==True):
						#print(msg) # <-- prints the received data
						lt="Start callb"
						for callb in callback_msg:
							callb(msg,client)
						#client.ws.data_ready=False
						#client.ws.last_data=""
				t2=time.time()-t2

			except (SSL.ZeroReturnError, SSL.SysCallError):
				# regular good SSL disconnect
				disconnect(client)
			except ValueError as err:
				# disconnct while handshake
				disconnect(client)
			except Exception as n:
				print("except while read in server_ws, our status ",end="")
				print(lt)
				print("sys:",end="")
				print(sys.exc_info()[0])
				print(sys.exc_info()[1])
				print(repr(traceback.format_tb(sys.exc_info()[2])))
				print("")

				disconnect(client)
		####################### RECEIVE ##########################
		######################## ERROR ##########################
		if(len(xList)>0):
			busy=1
			disconnect(client)
		######################## ERROR ##########################
		######################## MAINTAINANCE ##########################
		if(time.time()-client.debug_ts>1):
			#if(time.time()-client.debug_ts>10):
			#	print("woohoo its me")
			#	print(t1)
			#	print(t2)
			client.debug_ts=time.time()
		######################## MAINTAINANCE ##########################
	# end of while 1
	p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] -> Client "+str(client.login)+" closed: "+str(client.ip),"l")
	#lock.acquire()
	#if(client in clients):
	#	clients.remove(client)
	#lock.release()
#************* HANDLE CONNECTION *****************************************#
	
def start_server ():
#	context = SSL.Context(SSL.TLSv1_2_METHOD)
	context = SSL.Context(SSL.TLSv1_METHOD)
	
	context.use_privatekey_file('startssl.key')
	context.use_certificate_file('startssl.cert')
	context.use_certificate_chain_file('startssl.cert')
	
	s_n = socket.socket()
	s_n.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s_n.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)
	s = SSL.Connection(context, s_n)

	s.bind(('', PORT))
	s.listen(MAX_CLIENTS) # max clients

	p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] Waiting on wss_clients on Port "+str(PORT),"l")
	while 1:
		conn, addr = s.accept()
		try:
			#connstream = ssl.wrap_socket(conn, server_side=True, certfile="cert", keyfile="key", ssl_version=ssl.PROTOCOL_TLSv1)
			# generate new client
			new_client=ws_clients(conn)
			new_client.ws=WebSocket(conn) 
			# append it
			clients.append(new_client)
			p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] -> Connection from: "+ str(addr[0])+". Serving "+str(len(clients))+" ws_clients now","l")
			threading.Thread(target = handle, args = (new_client,addr)).start()
			# send every subscr
			for callb in callback_con:
				callb("conn",new_client)
		except Exception as n:
			p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] exception before starting connect thread","d")
			print(n)
			

 
def start():
	threading.Thread(target = start_server, args = ()).start()

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

class WebSocket(object):

	def __init__(self,mSocket):	
		self.handshaked = False
		self.headerbuffer = ''
		self.headertoread = 2048
		self.sock = mSocket
		
		self.fin = 0
		self.data = bytearray()
		self.opcode = 0
		self.hasmask = 0
		self.maskarray = None
		self.length = 0
		self.lengtharray = None
		self.index = 0
		self.request = None
		self.usingssl = False
		self.data_ready = False
		#self.last_data=""
		self.msgB=[]
		
		self.frag_start = False
		self.frag_type = BINARY
		self.frag_buffer = None
		self.frag_decoder = codecs.getincrementaldecoder('utf-8')(errors='strict')
		self.closed = False
		self.sendq = deque()

		
		self.state = HEADERB1
	
		# restrict the size of header and payload for security reasons
		self.maxheader = MAXHEADER
		self.maxpayload = MAXPAYLOAD


	def _handlePacket(self):
		self.data_ready = False
		if self.opcode == CLOSE:
			pass
		elif self.opcode == STREAM:
			pass
		elif self.opcode == TEXT:
			pass
		elif self.opcode == BINARY:
			pass
		elif self.opcode == PONG or self.opcode == PING:
			if len(self.data) > 125:
				raise Exception('control frame length can not be > 125')
		else:
			# unknown or reserved opcode so just close
			raise Exception('unknown opcode')

		if self.opcode == CLOSE:
			status = 1000
			reason = ''
			length = len(self.data)

			if length == 0:
				pass
			elif length >= 2:
				status = struct.unpack_from('!H', self.data[:2])[0]
				reason = self.data[2:]
				
				if status not in _VALID_STATUS_CODES:
					status = 1002

				if len(reason) > 0:
					try:
						reason = reason.decode('utf-8', errors='strict')
					except:
						status = 1002
			else:
				status = 1002

			self.close(status, reason)
			return
		
		elif self.fin == 0:
			if self.opcode != STREAM:
				if self.opcode == PING or self.opcode == PONG:
					raise Exception('control messages can not be fragmented')

				self.frag_type = self.opcode
				self.frag_start = True
				self.frag_decoder.reset()

				if self.frag_type == TEXT:
					self.frag_buffer = []
					utf_str = self.frag_decoder.decode(self.data, final = False)
					if utf_str:
						self.frag_buffer.append(utf_str)
				else:
					self.frag_buffer = bytearray()
					self.frag_buffer.extend(self.data)
						
			else:
				if self.frag_start is False:
					raise Exception('fragmentation protocol error')

				if self.frag_type == TEXT:
					utf_str = self.frag_decoder.decode(self.data, final = False)
					if utf_str:
						self.frag_buffer.append(utf_str)
				else:
					self.frag_buffer.extend(self.data)
								
		else:				
			if self.opcode == STREAM:
				if self.frag_start is False:
					raise Exception('fragmentation protocol error')

				if self.frag_type == TEXT:
					utf_str = self.frag_decoder.decode(self.data, final = True)
					self.frag_buffer.append(utf_str)
					self.data = ''.join(self.frag_buffer)
				else:
					self.frag_buffer.extend(self.data)
					self.data = self.frag_buffer

				self.handleMessage()

				self.frag_decoder.reset()	
				self.frag_type = BINARY
				self.frag_start = False
				self.frag_buffer = None

			elif self.opcode == PING:
				self._sendMessage(False, PONG, self.data)

			elif self.opcode == PONG:
				pass
			
			else:
				if self.frag_start is True:
					raise Exception('fragmentation protocol error')  

				if self.opcode == TEXT:
					try:
						self.data = self.data.decode('utf-8', errors='strict')
					except Exception as exp:
						raise Exception('invalid utf-8 payload')

			self.data_ready = True
			#self.last_data=self.data
			self.handleMessage()

	def handleMessage(self):
		self.msgB.append(self.data)

	def getMessage(self):
		if(len(self.msgB)>0):
			msg=self.msgB[0]
			self.msgB.remove(msg)
			return msg
		else:
			self.data_ready = False
			return -1

	def _handleData(self):
		# do the HTTP header and handshake
		if self.handshaked is False:
			lt=""
			try:
				lt="recv"
				time.sleep(0.01)
				data = self.sock.recv(self.headertoread)
				if not data:
					return -1
#				print("I've received:",end="")
#				print(len(data))
				lt="decoding"
				data = data.decode("UTF-8")
			except Exception as e:
				#rint("")
				#rint("SERVER_WS ")
				#rint("recv exception in handshaking:'", end="")
				#rint(lt,end="")
				#rint(" ",end="")
				#rint(e,end="")
				#rint("'")
				raise ValueError('disconnect')
				#raise Exception("remote socket closed")
			if not data:
				#print("empty data received, eventhough headertoread was "+str(self.headertoread))
				raise Exception("remote socket closed")

			else:
				# accumulate
				self.headerbuffer += data

				if len(self.headerbuffer) >= self.maxheader:
					raise Exception('header exceeded allowable size')
					
				# indicates end of HTTP header
				if '\r\n\r\n' in self.headerbuffer:
					headers = {}
					lines = data.splitlines()
					#print("lines:")
					#print(lines)
					for l in lines:
						parts = l.split(": ", 1)
						if len(parts) == 2:
							headers[parts[0]] = parts[1]
					headers['code'] = lines[len(lines) - 1]
							
					shake = "HTTP/1.1 101 Switching Protocols\r\n"
					for k, v in headers.items():
						if(k=='Connection' and v=='Upgrade'):
							shake += "Upgrade: websocket\r\n"
							shake += "Connection: Upgrade\r\n"
						elif(k=='Origin'):
							shake += "Sec-WebSocket-Origin: %s\r\n" % (headers['Origin'])
						elif(k=='Host'):
							shake += "Sec-WebSocket-Location: ws://%s\r\n" % (headers['Host'])
						elif(k=='Sec-WebSocket-Protocol'):
							shake += "Sec-WebSocket-Protocol: sample\r\n\r\n"
						elif(k=='Sec-WebSocket-Key'):
							GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
							response_key = b64encode(sha1(v.encode('utf-8') + GUID.encode('utf-8')).digest())
							shake +="Sec-WebSocket-Accept:%s\r\n"%response_key.decode()
					shake+="\r\n"
				
					self.sendq.append((TEXT, shake.encode("UTF-8")))
					self.handshaked = True
					self.headerbuffer = ''
					#self.handleConnected()


		# else do normal data		
		else:
			lt="recv handshake done"
			time.sleep(0.01)
			data = self.sock.recv(8192)
			#print(data)
			if not data:
				return -1
#				raise Exception("remote socket closed")			
			for d in data:
				self._parseMessage(d)
			return 0

	def close(self, status = 1000, reason = ''):
		"""
			Send Close frame to the client. The underlying socket is only closed 
			when the client acknowledges the Close frame. 
			
			status is the closing identifier.
			reason is the reason for the close. 
		"""
		try:
			if self.closed is False:
				close_msg = bytearray()
				close_msg.extend(struct.pack("!H", status))
				if type(reason)==bytes:
					close_msg.extend(reason.encode('utf-8'))
				else:
					close_msg.extend(reason)

				self._sendMessage(False, CLOSE, str(close_msg))

		finally:
				self.closed = True
		

	def _sendBuffer(self, buff):
		size = len(buff)
		tosend = size
		already_sent = 0

		while tosend > 0:
			try:
				# i should be able to send a bytearray
				sent = self.sock.send(buff[already_sent:])
				p.rint("send "+str(sent)+" bytes","w")
				if sent == 0:
					raise RuntimeError("socket connection broken")

				already_sent += sent
				tosend -= sent

			except socket.error as e:
				# if we have full buffers then wait for them to drain and try again
				if e.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
					return buff[already_sent:]
				else:
					raise e

		return None

	def sendFragmentStart(self, data):
		"""
			Send the start of a data fragment stream to a websocket client.
			Subsequent data should be sent using sendFragment().
			A fragment stream is completed when sendFragmentEnd() is called.
			
			If data is a str object then the frame is sent as Text.
			If the data is a bytearray object then the frame is sent as Binary. 
		"""
		opcode = BINARY
		if type(data)==bytes:
			opcode = TEXT
		self._sendMessage(True, opcode, data)

	def sendFragment(self, data):
		#
		#	see sendFragmentStart()
		#	
		#	If data is a str object then the frame is sent as Text.
		#	If the data is a bytearray object then the frame is sent as Binary. 
		#
		self._sendMessage(True, STREAM, data)

	def sendFragmentEnd(self, data):
		#
		#	see sendFragmentEnd()
		#	
		#	If data is a str object then the frame is sent as Text.
		#	If the data is a bytearray object then the frame is sent as Binary. 
		#			
		self._sendMessage(False, STREAM, data)

	def sendMessage(self, data):
		#
		#	Send websocket data frame to the client.
		#	
		#	If data is a str object then the frame is sent as Text.
		#	If the data is a bytearray object then the frame is sent as Binary. 
		#"
		opcode = BINARY
		if type(data)==bytes:
			opcode = TEXT
		elif type(data)==str:
			opcode = TEXT
		self._sendMessage(False, opcode, data)
	

	def _sendMessage(self, fin, opcode, data):
		#print("this is _sendMessage and my opcode is "+str(opcode))
		header = bytearray()
		b1 = 0
		b2 = 0
		if fin is False:
			b1 |= 0x80
		b1 |= opcode
		
		if type(data)==str:
			data = data.encode('utf-8')
		
		length = len(data)
		header.append(b1)
		
		if length <= 125:
			b2 |= length
			header.append(b2)
		
		elif length >= 126 and length <= 65535:
			b2 |= 126
			header.append(b2)
			header.extend(struct.pack("!H", length))
		
		else:
			b2 |= 127
			header.append(b2)
			header.extend(struct.pack("!Q", length))
		
		payload = header
		if length > 0:		
			for d in bytearray(data):
				payload.append(d)
		
		self.sendq.append((opcode, payload))


	def _parseMessage(self, byte):	
		# read in the header
		if self.state == HEADERB1:

			self.fin = byte & 0x80
			self.opcode = byte & 0x0F
			self.state = HEADERB2

			self.index = 0
			self.length = 0
			self.lengtharray = bytearray()
			self.data = bytearray()
			
			rsv = byte & 0x70
			if rsv != 0:
				raise Exception('RSV bit must be 0')
			
		elif self.state == HEADERB2:
			mask = byte & 0x80				
			length = byte & 0x7F
			
			if self.opcode == PING and length > 125:
				raise Exception('ping packet is too large')
			
			if mask == 128:
				self.hasmask = True
			else:
				self.hasmask = False
			
			if length <= 125:
				self.length = length
				
				# if we have a mask we must read it
				if self.hasmask is True:
					self.maskarray = bytearray()
					self.state = MASK
				else:
					# if there is no mask and no payload we are done
					if self.length <= 0:
						try:
							self._handlePacket()
						finally:
							self.state = self.HEADERB1
							self.data = bytearray()
							
					# we have no mask and some payload
					else:
						#self.index = 0
						self.data = bytearray()
						self.state = PAYLOAD
					
			elif length == 126:
				self.lengtharray = bytearray()
				self.state = LENGTHSHORT
				
			elif length == 127:
				self.lengtharray = bytearray()
				self.state = LENGTHLONG

		
		elif self.state == LENGTHSHORT:
			self.lengtharray.append(byte)

			if len(self.lengtharray) > 2:
				raise Exception('short length exceeded allowable size')

			if len(self.lengtharray) == 2:
				self.length = struct.unpack_from('!H', self.lengtharray)[0]
				
				if self.hasmask is True:
					self.maskarray = bytearray()
					self.state = MASK
				else:
					# if there is no mask and no payload we are done
					if self.length <= 0:
						try:
							self._handlePacket()
						finally:
							self.state = HEADERB1
							self.data = bytearray()

					# we have no mask and some payload
					else:
						#self.index = 0
						self.data = bytearray()
						self.state = PAYLOAD
			
		elif self.state == LENGTHLONG:

			self.lengtharray.append(byte)

			if len(self.lengtharray) > 8:
				raise Exception('long length exceeded allowable size')

			if len(self.lengtharray) == 8:
				self.length = struct.unpack_from('!Q', self.lengtharray)[0]

				if self.hasmask is True:
					self.maskarray = bytearray()
					self.state = MASK
				else:
					# if there is no mask and no payload we are done
					if self.length <= 0:
						try:
							self._handlePacket()
						finally:
							self.state = HEADERB1
							self.data = bytearray()

					# we have no mask and some payload
					else:
						#self.index = 0
						self.data = bytearray()
						self.state = PAYLOAD
			
		# MASK STATE
		elif self.state == MASK:
			self.maskarray.append(byte)

			if len(self.maskarray) > 4:
				raise Exception('mask exceeded allowable size')

			if len(self.maskarray) == 4:
				# if there is no mask and no payload we are done
				if self.length <= 0:
					try:
						self._handlePacket()
					finally:
						self.state = HEADERB1
						self.data = bytearray()
						
				# we have no mask and some payload
				else:
					#self.index = 0
					self.data = bytearray()
					self.state = PAYLOAD
		
		# PAYLOAD STATE
		elif self.state == PAYLOAD:
			if self.hasmask is True:
				self.data.append( byte ^ self.maskarray[self.index % 4] )
			else:
				self.data.append( byte )
			
			# if length exceeds allowable size then we except and remove the connection
			if len(self.data) >= self.maxpayload:
				raise Exception('payload exceeded allowable size')

			# check if we have processed length bytes; if so we are done
			if (self.index+1) == self.length:
				try:
					self._handlePacket()
				finally:
					#self.index = 0
					self.state = HEADERB1
					self.data = bytearray()
			else:
				self.index += 1
