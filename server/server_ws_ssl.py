#!/usr/bin/env python
from OpenSSL import SSL
import socket, struct,  threading, cgi, time, p, sys
from clients import ws_clients
from base64 import b64encode
from hashlib import sha1

import SocketServer
import hashlib
import base64
import socket
import struct
import ssl
import sys
import errno
import codecs
from collections import deque
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from select import select

MAX_SIZE_RECV=1024000
PORT=9879
MAX_CLIENTS=5

_VALID_STATUS_CODES = [1000, 1001, 1002, 1003, 1007, 1008, 1009, 1010, 1011, 3000, 3999, 4000, 4999]

HANDSHAKE_STR = (
	"HTTP/1.1 101 Switching Protocols\r\n"
	"Upgrade: WebSocket\r\n"
	"Connection: Upgrade\r\n"
	"Sec-WebSocket-Accept: %(acceptstr)s\r\n\r\n"
)

GUID_STR = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

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

#******************************************************#
def recv_data (client, length):
	#print("Wait on data")
	if(handshake(client)>0):
		#print('[S_ws] -> done')
		ignore=0
		
	
	try:
		data = bytearray(client.conn.recv(MAX_SIZE_RECV))
	except:
		data=""
	#print("[ws] -> Incoming")
	if(len(data)==0):
		#print("[S_ws  "+time.strftime("%H:%M:%S")+"] -> len=0 ==> disconnect")
		for callb in callback_con:
			callb("disconnect",client)
		return -1
	elif(data[0]!=129):
		#print("[S_ws  "+time.strftime("%H:%M:%S")+"] -> regular disconnect")
		for callb in callback_con:
			callb("disconnect",client)
		return -1
	elif(len(data) < 6):
		p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] -> Error reading data","d")
	else:
		datalen = (0x7F & data[1])
		
		if(datalen > 6): #fin,length,4xmask,?
			#print("datalen: %d"%datalen)
			indexFirstMask=2
			if(datalen==126):
				indexFirstMask+=2
			elif(datalen==127):
				indexFirstMask+=8

			mask_key = data[indexFirstMask:indexFirstMask+4]
			masked_data = data[indexFirstMask+4:(indexFirstMask+4+datalen)]
			unmasked_data=""
			for i in range(0,len(masked_data),1):
				unmasked_data+=(chr(masked_data[i] ^ mask_key[i%4]))
		
			#print("Message:")
			#print(str_data)
			#print("EOM")
			for callb in callback_msg:
				callb(unmasked_data,client)
		return 0
	return -3
	#end
 


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
	

def handle (client, addr):
	lock = threading.Lock()
	while 1:
		rList, wList, xList = select(client.conn, client.conn, client.conn, 3)
		
		for ready in wList:
			client = None
			try:
				while client.ws.sendq:
					opcode, payload = client.ws.sendq.popleft()
					remaining = client.ws._sendBuffer(payload)
					if remaining is not None:
						client.ws.sendq.appendleft((opcode, remaining))
						break
					else:
						if opcode == CLOSE:
							raise Exception("received client close")

			except Exception as n:
				if client.conn:
					client.conn.close()
				
				try:
					if client:
						client.handleClose()
				except:
					pass

				try:
					del self.connections[ready]
				except:
					pass

				try:
					self.listeners.remove(ready)
				except:
					pass

		for ready in rList:
			client = None
			try:
				client.ws._handleData()
			except Exception as n:
				  
				  if client:
					 client.client.close()
					 
				  try:
					 if client:
						client.handleClose()
				  except:
					 pass
				  
				  try:
					 del self.connections[ready]
				  except:
					 pass
				 
				  try:
					 self.listeners.remove(ready)
				  except:
					 pass
	  
		 for failed in xList:
			if failed == self.serversocket:
			   self.close()
			   raise Exception("server socket failed")
			else:
			   client = None
			   try:
				   client = self.connections[failed]
				   client.client.close()
				   
				   try:
					  client.handleClose()
				   except:
					  pass
				  
				   try:
					  self.listeners.remove(failed)
				   except:
					  pass
				   
			   except:
				  pass
			  
			   finally:
				  if client:
					 del self.connections[failed]
			
		#time.sleep(5)
		# -- client.ws.
		#print("Sending...")
		#msg="hi"
		#print("Done")
		res = recv_data(client, MAX_SIZE_RECV)
		if res<0:
			#print("returned:%d"%res)
			break
		#print("recv_data!!")
		#if not data: break
		#data = cgi.escape(data)
		#lock.acquire()
		#[send_data(c, data) for c in clients]
		#lock.release()
	p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] -> Client "+client.login+" closed: "+str(client.ip),"l")
	lock.acquire()
	if(client in clients):
		clients.remove(client)
	lock.release()
	client.conn.close()
	
def start_server ():
	context = SSL.Context(SSL.TLSv1_METHOD)
	context.use_privatekey_file('key')
	context.use_certificate_file('cert')
	
	s_n = socket.socket()
	s_n.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s = SSL.Connection(context, s_n)

	s.bind(('', PORT))
	s.listen(MAX_CLIENTS) # max clients

	p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] Waiting on wss_clients on Port "+str(PORT),"l")
	while 1:
		conn, addr = s.accept()
		new_client=ws_clients(conn)
		new_client.ws=WebSocket() # generate new object
		clients.append(new_client)
		p.rint("[S_wss "+time.strftime("%H:%M:%S")+"] -> Connection from: "+ str(addr[0])+". Serving "+str(len(clients))+" ws_clients now","l")
		threading.Thread(target = handle, args = (new_client,addr)).start()
		# send every subscr
		for callb in callback_con:
			callb("conn",new_client)

 
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


class HTTPRequest(BaseHTTPRequestHandler):
	def __init__(self, request_text):
		self.rfile = StringIO(request_text)
		self.raw_requestline = self.rfile.readline()
		self.error_code = self.error_message = None
		self.parse_request()

class WebSocket(object):

	def __init__(self):	
		self.handshaked = False
		self.headerbuffer = ''
		self.headertoread = 2048
		
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
			reason = u''
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
					self.data = u''.join(self.frag_buffer)
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

			self.handleMessage()


	def _handleData(self):
		# do the HTTP header and handshake
		if self.handshaked is False:
			
			data = self.client.recv(self.headertoread)
			if not data:
				raise Exception("remote socket closed")

			else:
				# accumulate
				self.headerbuffer += data

				if len(self.headerbuffer) >= self.maxheader:
					raise Exception('header exceeded allowable size')
					
				# indicates end of HTTP header
				if '\r\n\r\n' in self.headerbuffer:
					self.request = HTTPRequest(self.headerbuffer)
							
					# handshake rfc 6455
					if self.request.headers.has_key('Sec-WebSocket-Key'.lower()):
						key = self.request.headers['Sec-WebSocket-Key'.lower()]
						hStr = HANDSHAKE_STR % { 'acceptstr' :  base64.b64encode(hashlib.sha1(key + GUID_STR).digest()) }
						self.sendq.append((BINARY, hStr))
						self.handshaked = True
						self.headerbuffer = ''
						self.handleConnected()

					else:
						raise Exception('Sec-WebSocket-Key does not exist')

		# else do normal data		
		else:
			data = self.client.recv(8192)
			if not data:
				raise Exception("remote socket closed")
			
			for d in data:
				self._parseMessage(ord(d))

	def close(self, status = 1000, reason = u''):
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
				if isinstance(reason, unicode):
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
				sent = self.client.send(buff[already_sent:])
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
			 
			 If data is a unicode object then the frame is sent as Text.
			 If the data is a bytearray object then the frame is sent as Binary. 
		"""
		opcode = BINARY
		if isinstance(data, unicode):
			opcode = TEXT
		self._sendMessage(True, opcode, data)

	def sendFragment(self, data):
		"""
			 see sendFragmentStart()
			 
			 If data is a unicode object then the frame is sent as Text.
			 If the data is a bytearray object then the frame is sent as Binary. 
		"""
		self._sendMessage(True, STREAM, data)

	def sendFragmentEnd(self, data):
		"""
			 see sendFragmentEnd()
			 
			 If data is a unicode object then the frame is sent as Text.
			 If the data is a bytearray object then the frame is sent as Binary. 
		"""			
		self._sendMessage(False, STREAM, data)

	def sendMessage(self, data):
		"""
			 Send websocket data frame to the client.
			 
			 If data is a unicode object then the frame is sent as Text.
			 If the data is a bytearray object then the frame is sent as Binary. 
		"""
		opcode = BINARY
		if isinstance(data, unicode):
			opcode = TEXT
		self._sendMessage(False, opcode, data)
	

	def _sendMessage(self, fin, opcode, data):
		header = bytearray()
		b1 = 0
		b2 = 0
		if fin is False:
			b1 |= 0x80
		b1 |= opcode
		
		if isinstance(data, unicode):
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
		
		payload = None
		if length > 0:		
			payload = str(header) + str(data)
		else:
			payload = str(header)
		
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
				self.length = struct.unpack_from('!H', str(self.lengtharray))[0]
				
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
				self.length = struct.unpack_from('!Q', str(self.lengtharray))[0]

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
