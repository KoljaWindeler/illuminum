###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Tavendo GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################
import  struct, os, threading, time, p, sys, traceback

from twisted.internet import reactor, ssl
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from clients import ws_clients
from base64 import b64encode
from hashlib import sha1

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS


class MyServerProtocol(WebSocketServerProtocol):
	ws = "";
    
	def onConnect(self, request):
		m_ip = request.peer.split(':')[1]
		m_port = request.peer.split(':')[2]
		self.ws=ws_clients(m_port,m_ip)
		self.ws.ws=self
		clients.append(self.ws)
		p.rint2("Connection from: "+ str(m_ip)+". Serving "+str(len(clients))+" ws_clients now","l","S_wss")
		for callb in callback_con:
			callb("conn",self.ws)


	def onOpen(self):
		#print("WebSocket connection open.")
		ignore=1

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			#print("Text message received: {0}".format(payload.decode('utf8')))
			for callb in callback_msg:
				callb(payload.decode('utf8'),self.ws)

	def onClose(self, wasClean, code, reason):
		disconnect(self.ws)
		try:
			p.rint("Client "+str(self.ws.login)+" closed: "+str(self.ws.ip),"l","S_wss")
		except:
			pass

#******************************************************#
def send_data(client, data):
	if client in clients:
		client.ws.sendMessage(data,False)
	return 0
#******************************************************#
#************* DISCONNECT *****************************************#
def disconnect(client):
	try:
		if client.ws.sock:
			client.ws.disconnect()
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
	try:
		client.alive = 0
	except:
		pass
#************* DISCONNECT *****************************************#
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
def start():
	PORT=9879	
	if(os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"experimental"))):
		PORT=9779
		print("!!!!! RUNNING EXPERIMENTAL VERSION OF WS SERVER !!!!!!")

	contextFactory = ssl.DefaultOpenSSLContextFactory('startssl.key','startssl.cert')
	factory = WebSocketServerFactory(u"wss://127.0.0.1:"+str(PORT),debug=False,debugCodePaths=False)

	factory.protocol = MyServerProtocol
	listenWS(factory, contextFactory)

	threading.Thread(target=reactor.run, args=(False,)).start()
	p.rint2("Waiting on wss_clients on Port "+str(PORT),"l","S_wss")
			
