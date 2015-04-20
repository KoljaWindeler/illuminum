import time
import server
import json
from subprocess import Popen, PIPE
import os
import urllib2

from subprocess import call
#******************************************************#

def test(str,cli):
#	try:
		json_encoded=json.loads(str)
		for key, value in json_encoded.items() :
			print("-a-->Key:'"+key+"' / Value:'"+value+"'")

		if json_encoded.has_key("app") and json_encoded.has_key("cmd"):
			if json_encoded["app"]=="web_cam" and json_encoded["cmd"]=="start":
				print("ok .. lets try")
				process = Popen(["/home/pi/python/server/helper.sh", "motion", ""], stdout=PIPE)
				(output, err) = process.communicate()
				exit_code = process.wait()
			elif json_encoded["app"]=="web_cam" and json_encoded["cmd"]=="detection_start":
				print("ok, ich schalte die cam an")
				address="http://192.168.1.74:8080/0/detection/start"
				website = urllib2.urlopen(address).read()
				detection_active()
			elif json_encoded["app"]=="web_cam" and json_encoded["cmd"]=="detection_pause":
				print("ok, ich schalte die cam aus")
				address="http://192.168.1.74:8080/0/detection/pause"
				website = urllib2.urlopen(address).read()
				detection_active()
			elif json_encoded["app"]=="web_cam" and json_encoded["cmd"]=="single":
				print("taking a single picture")
				Popen(["sudo","rm","/var/www/webcam/dump.jpg"],stdout=PIPE)
				pprocess = Popen(["/home/pi/python/server/helper.sh", "webcam", ""],)
				# create a msg and send to client
				msg={}
				msg["app"]="web_cam"
				msg["cmd"]="pic_ready"
				for i in range(0,10):
					if(os.path.isfile('/var/www/webcam/dump.jpg')):
						break
					time.sleep(0.1)
				msg=json.dumps(msg)
				server.send_data(cli,msg)
				print("picture done")

			elif json_encoded["app"]=="system" and json_encoded["cmd"]=="reboot":
				msg={}
				msg["app"]="system"
				msg["cmd"]="wait 15 sec"
				msg=json.dumps(msg)
				server.send_data(cli,msg)
				Popen(["sudo","reboot","0"],stdout=PIPE)

#			for i in range(len(server.clients)):
#				if server.clients[i]==cli:
#					server.send_data(server.clients[i],"warum stop?")
#				else:
#					server.send_data(server.clients[i],"jemand wollte stop")
		
def test2(cli):
	global update_all
	update_all=1
#	except: 
#		pass



def detection_active():
	msg={}
	msg["app"]="web_cam"
	msg["cmd"]="detection_activ"
	website=""
	address="http://127.0.0.1:8080/0/detection/status"
	try:
		website = urllib2.urlopen(address).read()
	except:
		pass
	if(website.find("PAUSE")>0):
		msg["cmd"]="detection_inactiv"
	msg=json.dumps(msg)
	print(msg)
	server.send_data_all_clients(msg)
#******************************************************#


server.start()
server.subscribe_callback(test,"msg")
server.subscribe_callback(test2,"con")


i=1
now = time.time()*2
webcam_running=0
update_all=0

while 1:
	if(time.time()-now>=1 or update_all):
		# update time
		now=time.time()
		
		msg={}
		msg["app"]="ws"
		msg["cmd"]="update_time"
		msg["data"]=time.strftime("%d.%m.%Y || %H:%M:%S") 
		msg=json.dumps(msg)
		server.send_data_all_clients(msg)

	# check if motion is running
	process = Popen(["/home/pi/python/server/helper.sh", "run", "motion"], stdout=PIPE)
	(output, err) = process.communicate()
	exit_code = process.wait()
	
	if(output != "" and webcam_running==0): #webcam started
		webcam_running=1
		send_msg=1
	elif(output=="" and webcam_running==1): #webcam dropped
		webcam_running=0
		send_msg=1
	else:					# nothing changed
		send_msg=0

	if(send_msg or update_all):
		msg={}
		msg["app"]="web_cam"
		if(webcam_running):
			msg["cmd"]="online"
		else:
			msg["cmd"]="offline"
		msg=json.dumps(msg)
		print(msg)
		for i in range(len(server.clients)):
			print("send to client #%d/%d"%(i,len(server.clients)))
			server.send_data(server.clients[i],msg)
		if(webcam_running):
			# check status
			detection_active()

	# clean up
	if(update_all):
		update_all=0

	time.sleep(.1)
	i+=1

