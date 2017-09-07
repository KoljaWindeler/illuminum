# sudo pip3 install paho-mqtt

##for the client
#import jkw_mqtt
#mq = jkw_mqtt(m2m.mid)
#mq.r.m.subscribe_topic(m2m.mid+"/PWM_dimm/switch")  # on / off
#mq.r.m.subscribe_topic(m2m.mid+"/PWM_RGB_dimm/color/set") # set color
#mq.start()
#trigger.subscribe_callback(mq.r.motion_publish) # tell trigger to call mq.publish to report motion to the mqtt server
#******************************************************#

import time
import paho.mqtt.client as mqtt
import threading
import p

class myMQTT:
	def __init__(self):
		self.server_ip = "192.168.2.84"
		self.server_port = 1883
		self.login = "ha"
		self.pw = "ah"
		self.callback_action=[""]
		self.topics=[""]

	def subscribe_callback(self,fun):
		if self.callback_action[0]=="":
			self.callback_action[0]=fun
		else:
			self.callback_action.append(fun)
			
	def subscribe_topic(self,topic):
		if self.topics[0]=="":
			self.topics[0]=topic
		else:
			self.topics.append(topic)

#******************************************************#
class runner(threading.Thread):
	def __init__(self):
		self.alive = False
		self.m = myMQTT()	# initialize one object

	def set_id(self,mid):
		self.mid = mid

	def set_light(self,light):
		self.light = light

	def on_disconnect(client, userdata, rc):
		p.rint2("Unexpected disconnection. Will auto-reconnect","l","MQTT")
			
	def on_connect(self, client, userdata, flag, rc):
		p.rint2("connected","l","MQTT")
		
	def send(self, topic,msg):
		p.rint2("Publish: "+topic+" : "+msg,"l","MQTT")
		self.c.publish(topic, msg, retain=True)
		
	def motion_publish(self, event, data):
		if(event == "state_change"): # should always be true
			status="OFF"
			if(data[0]==1):
				status="ON"
			self.send(self.mid+"/motion/status",status)
			
	def on_message(self, client, userdata, rc):
		p.rint2("incoming messages","l","MQTT")
		
		if(rc.topic==self.mid+"/PWM_RGB_dimm/color/set"):
			p.rint2("set light color","l","MQTT")
			#print("here we have to parse the msg and call light q")
			#print(rc.payload)
			mq_c=str(rc.payload).replace('b','').replace('\'','').split(',')
			#print(mq_c)
			self.light.clear_q()
			self.light.add_q_entry(time.time(), int(mq_c[0]), int(mq_c[1]), int(mq_c[2]), 500)
			self.light.runner.l.d_r=int(mq_c[0])
			self.light.runner.l.d_g=int(mq_c[1])
			self.light.runner.l.d_b=int(mq_c[2])
		elif(rc.topic==self.mid+"/PWM_dimm/switch"):
			p.rint2("set light status","l","MQTT")
			#print(rc.payload)
			#self.light.clear_q()
			if(rc.payload==b'ON'):
				#print("turn on")
				self.light.add_q_entry(time.time(), self.light.runner.l.d_r, self.light.runner.l.d_g, self.light.runner.l.d_b, 4000)
				self.send(self.mid+"/PWM_light/status","ON")
			else:
				#print("turn off")
				self.light.add_q_entry(time.time(), 0, 0, 0, 4000)
				self.send(self.mid+"/PWM_light/status","OFF")
		else:
			for callb in self.m.callback_action:
				if(not(type(callb) is str)):
					try:
						callb((rc.topic,rc.msg))
					except:
						p.rint2("callback crashed","l","MQTT")

	def run(self):
		self.alive = True
		p.rint2("thread started","l","MQTT")

		self.c = mqtt.Client(self.mid, clean_session=False)
		self.c.username_pw_set(self.m.login, self.m.pw)
		self.c.connect(self.m.server_ip, self.m.server_port)
		for t in self.m.topics:
			self.c.subscribe(t, qos=1)
			
		self.c.on_connect = self.on_connect
		self.c.on_message = self.on_message
		self.c.on_disconnect = self.on_disconnect
		self.c.loop_forever()
			
		
	def stop(self):
		if(self.alive):
			self.c.disconnect()
			self.c.loop_stop(force=True)
			self.alive = False

			
r = runner()

def start():
	threading.Thread(target = r.run, args = ([])).start()

def stop():
	r.stop()
	while(r.alive):
		time.sleep(0.1)

def restart():
	stop()
	start()
	
