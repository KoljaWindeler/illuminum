import OpenSSL
import socket,os,time,json,base64, datetime
import hashlib,select,trigger,uuid
import sys,light
from binascii import unhexlify, hexlify
from login import *
from math import *

MAX_MSG_SIZE = 10024000 # 10 MB?
SERVER_IP = "52.24.157.229"
#SERVER_IP = "192.168.1.84"
SERVER_PORT = 9875
mid=str(uuid.getnode())
SERVER_TIMEOUT = 15
MAX_OUTSTANDING_ACKS=2

# login
l=login()
pw=l.pw
msg_out_ts=0			# used to save the time when the last message, requesting a ACK was send
logged_in=0			# avoiding that we send stuff without beeing logged in
file_uploading=""
msg_q=[]
file_q=[]
file_str_q=[]
client_socket=""
last_transfer=time.time()
light_dimming_q=[]
my_state=-1
my_detection=-1

mRed=0
mGreen=0
mBlue=0



#******************************************************#
def get_time():
	return time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
#******************************************************#
#******************************************************#
def trigger_handle(event,data):
	global msg_q
	global my_state
	global my_detection
	global trigger
	global mRed
	global mGreen
	global mBlue

	if(event=="state_change"):
		msg={}
		msg["cmd"]=event
		msg["state"]=data[0]
		msg["detection"]=data[1]
		my_state=data[0]
		my_detection=data[1]
		
		#delete old status msg
		for m in msg_q:
			if(msg["cmd"]==m["cmd"]):
				msg_q.remove(m)
		msg_q.append(msg)
		
		# light dimming stuff
		if(trigger.get_interval()==0):
			for l in light_dimming_q:
				light_dimming_q.remove(l)

			if(my_detection==0 and my_state==1): # deactive and motion
				light_dimming_q.append((time.time(),mRed,mGreen,mBlue,4000)) # 4 sec to dimm to warm orange - now
				# remove all eventueally further dimmm off's					
			elif(my_detection==0 and my_state==0): # deactive and no motion
				print("back to lights off")
				delay_off=5*60 # usually 5 min
				off_time=get_time()+delay_off
				if(off_time>22*60*60 or (off_time%86400)<6*60*60): # switch off after 22h and before 6
					delay_off=0
				print("at "+str((datetime.datetime.fromtimestamp(int((time.time()+delay_off)))).strftime('%y_%m_%d %H:%M:%S')))
				light_dimming_q.append((time.time()+delay_off,0,0,0,4000)) # 4 sec to dimm to off - in 10 min from now
				#light_dimming_q.append((time.time(),0,0,0,4000)) # 4 sec to dimm to off - in 10 min from now
			elif(my_detection==1 and my_state==1):
				light_dimming_q.append((time.time(),100,0,0,4000)) # 4 sec to dimm to off - in 10 min from now
			elif(my_detection==1 and my_state==0):
				light_dimming_q.append((time.time(),0,0,0,4000)) # 4 sec to dimm to off - in 10 min from now

	elif(event=="uploading_str"):
		file_str_q.append(data)

#******************************************************#
def upload_file(path,td,high_res):
#	print(str(time.time())+" -> this is upload_file")
	if(trigger.STEP_DEBUG):
		print("[A "+time.strftime("%H:%M:%S")+"] Step 5. this is upload_file for "+path+" with "+str(len(msg_q))+" msg in q")
	if(len(msg_q)>10):
		print("skip picture, q full")
		return 1

	global logged_in
	if(logged_in!=1):
		print("We can't upload as we are not logged in")
		return -1

	#cheat, read hardcoded file instead of path info to save copy time
	#todo, if full frame read other file
	if high_res:
		img = open("/dev/shm/mjpeg/cam_full.jpg",'rb')
	else:
		img = open("/dev/shm/mjpeg/cam_prev.jpg",'rb')
	i=0
	while True:
		# should realy read it in once, 10MB buffer
#		if(trigger.TIMING_DEBUG):
#			td.append((time.time(),"start reading"))

		strng = img.read(MAX_MSG_SIZE-100)

#		if(trigger.TIMING_DEBUG):
#			td.append((time.time(),"reading img done"))

		if not strng:
			#print("could not read")
			break

		msg={}
		msg["cmd"]="wf"
		msg["fn"]=path
		msg["data"]=base64.b64encode(strng).decode('utf-8')
		#for i in range(0,1280*20):
		#	msg["data"]+="."
		msg["sof"]=0
		if(i==0):
			msg["sof"]=1
		msg["eof"]=0
		msg["msg_id"]=i	
		msg["ack"]=-1 #-1
		msg["ts"]=td
		if(len(strng)!=(MAX_MSG_SIZE-100)):
			msg["eof"]=1
		#print('sending('+str(i)+') of '+path+'...')

		if(trigger.TIMING_DEBUG):
			td.append((time.time(),"b64 - gen msg"))
		
		msg["td"]=td
		msg_q.append(msg)
		if(trigger.STEP_DEBUG):
			print("[A "+time.strftime("%H:%M:%S")+"] Step 6  upload appended message for "+path)
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
	context = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
	c_socket = OpenSSL.SSL.Connection(context,s)
	try:
		c_socket.connect((SERVER_IP, SERVER_PORT))
	except:
		print("Could not connect to server")
		print("retrying in 3 sec")
		time.sleep(3)
		return -1

	print("[A "+time.strftime("%H:%M:%S")+"] -> connected. Loggin in...")

	#### prelogin
	msg={}
	msg["mid"]=mid
	msg["cmd"]="prelogin"
	msg_q.append(msg)
	#print("sending prelogin request")

	return c_socket

#def helper_output(input):
#	input=input[0:len(input)-1]
#	if(input=="rm"):


# Main programm
#******************************************************#

trigger.start()
trigger.subscribe_callback(trigger_handle,"")
#trigger.set_interval(10)
#trigger.set_interval(1)

light.start()

# our helper for the console
#std_input.start()
#std_input.subscribe_callback(helper_output)

comm_wait=[]
waiter=[]
hb_out=0
recv_buffer=""
last_pic=time.time()
mq_len=0

while 1:
	pu_num=0
	pu_start_ts=0

	logged_in=0
	client_socket=connect()	
	while(client_socket!=""):
		#************* receiving start ******************#		
		try:
			ready_to_read, ready_to_write, in_error = select.select([client_socket,sys.stdin], [client_socket,], [], 0)
			#print(str(len(ready_to_read))+"/"+str(len(ready_to_write))+"/"+str(len(in_error)))
		except:
			print("select detected a broken connection")
			client_socket=""
			break
	
		# test
		if(len(in_error)>0):
			print("in error!")

		## react on keydown
		if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
			input=sys.stdin.readline()
			if(input[:1]=="q"):
				print("Quit")
				os._exit(1)
			else:
				print("what do you mean by: "+input)

		## do some light dimming
		if(len(light_dimming_q) > 0):
			for data in light_dimming_q:
				if(data[0]<=time.time()):
					light_action=data
					light_dimming_q.remove(data)
					if(light_action[1]==-1 and light_action[2]==-1 and light_action[3]==-1):
						light.return_to_old(light_action[4])
					else:
						light.dimm_to(light_action[1],light_action[2],light_action[3],light_action[4])
				
		## react on msg in
		if(len(ready_to_read) > 0):
			#print("read process is ready")
			try:
				data = client_socket.recv(MAX_MSG_SIZE)
				if(len(data)==0):
					print("disconnect")
					client_socket=""
					break;
				data_dec = data.decode("UTF-8")
				#print("Data received:"+str(data))
			except:
				print('client_socket.recv detected error')
				break;
			
			data_dec=recv_buffer+data_dec
			data_array=data_dec.split('}')
		
			for a in range(0,len(data_array)-1):
				data_array[a]+='}'

				try:
					enc=json.loads(data_array[a])
				except:
					enc=""
					print("json decode failed on:"+data_array[a])
					break;
			
				if(type(enc) is dict):
					last_transfer=time.time()
					#print("json decoded msg")
					#print(enc)
					# ack ok packets are always send alone, they carry the cmd to acknowledge, but the resonse will be a separate msg
					if(enc.get("ack_ok",0)==1): 
						if(len(comm_wait)>0 or 1):
							first_element=comm_wait[0]
							comm_wait.remove(first_element)
							#print("comm wait dec at "+str(time.time())+" -> "+str(len(comm_wait)))
							msg_out_ts=0

					elif(enc.get("cmd")=="prelogin"):
						#### login 
						#print("received challange "+enc.get("challange"))
						h = hashlib.md5()
						h.update(str(pw+enc.get("challange")).encode("UTF-8"))
						#print("total to code="+str(pw+enc.get("challange")))
						pw_c=h.hexdigest()
						#print("result="+pw_c)

						msg={}
						msg["mid"]=mid
						msg["client_pw"]=pw_c
						msg["cmd"]="login"
						msg["state"]=my_state
						msg["detection"]=my_detection
						msg["ts"]=time.strftime("%d.%m.%Y || %H:%M:%S")
						msg["ack"]=-1
						msg_q.append(msg)
					elif(enc.get("cmd")=="login"):
						if(enc.get("ok")==1):
							logged_in=1
							
							mRed=enc.get("mRed")
							mGreen=enc.get("mGreen")
							mBlue=enc.get("mBlue")
							
							print("[A "+time.strftime("%H:%M:%S")+"] -> log-in OK")
							print("[A "+time.strftime("%H:%M:%S")+"] setting detection to "+str(enc.get("detection")))
							trigger.set_alias(enc.get("alias"))
							trigger.set_detection(int(enc.get("detection")))
						else:
							logged_in=0
							print("[A "+time.strftime("%H:%M:%S")+"] -> log-in failed")
					elif(enc.get("cmd")=="m2m_hb"):
						hb_out=0
						print("[A "+time.strftime("%H:%M:%S")+"] -> connection OK")
					elif(enc.get("cmd")=="set_detection"):
						print("[A "+time.strftime("%H:%M:%S")+"] setting detection to "+str(enc.get("state")))
						trigger.set_detection(enc.get("state"))
					elif(enc.get("cmd")=="wf"):
						ignore=1
					elif(enc.get("cmd")=="set_color"):
						mRed=enc.get("r",0)
						mGreen=enc.get("g",0)
						mBlue=enc.get("b",0)
						light_dimming_q.append((time.time(),mRed,mGreen,mBlue,500)) # 4 sec to dimm to warm orange - now
						
					elif(enc.get("cmd")=="set_interval"):
						print("setting interval to "+str(enc.get("interval",0)))
						trigger.set_interval(enc.get("interval",0))
#						if(enc.get("interval",0)>0):
#							light_dimming_q.append((time.time(),0,100,0,1000)) # 4 sec to dimm to off - in 10 min from now
#						else:
#							light_dimming_q.append((time.time(),-1,-1,-1,1000)) # 4 sec to dimm to off - in 10 min from now
					else:
						print("unsopported command:"+enc.get("cmd"))
				#end of "if"
			# end of "for"

			if(data_array[len(data_array)-1]==""):
				#if data contained a full message and ended with closing tag, we a$
				recv_buffer=""
			else:
				# but if we grabbed something like 1.5 messages, we should buffer $
				recv_buffer=data_array[len(data_array)-1]
				#print("using buffer!")
		#************* receiving end ******************#
		
		#************* timeout check start ******************#
		if(time.time()-last_transfer>60*5 and hb_out==0):
			print("[A "+time.strftime("%H:%M:%S")+"] -> checking connection")
			msg={}
			msg["cmd"]="m2m_hb"
			msg_q.append(msg)
			hb_out=1
		#************* timeout check end ******************#

		#************* sending start ******************#
		if(len(msg_q)>5):
			print("!!!!!!!!!!!!!!!!!!!!!! msg_q is very long: "+str(len(msg_q))+", comm wait: "+str(len(comm_wait))+", logged in: "+str(logged_in))

		if(len(msg_q)>0 and (len(comm_wait)<MAX_OUTSTANDING_ACKS or not(logged_in))):
			msg=""
			if(logged_in!=1):
				for msg_i in msg_q:
					if(msg_i["cmd"]=="prelogin"):
						print("[A "+time.strftime("%H:%M:%S")+"] -> requesting challange")
						msg=msg_i
						msg_q.remove(msg_i)
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
#				if(msg.get("cmd"," ")=="wf"):
#					if(msg.get("sof",0)==1):
#						print("[A "+time.strftime("%H:%M:%S")+"] -> uploading "+msg.get("fn"))
#						msg["td"].append((time.time(),"upload start"))

				send_msg_enc=send_msg.encode("UTF-8")
				try:
					msg["td"].append((time.time(),"sendall start"))
				except: 
					ignore=1
				try:
					#print("Wait to send at ",end="")
					#print(time.time(),end="")
					client_socket.sendall(send_msg)
					#	print(" sent " at ",end="")
					#	print(time.time())
				except:
					client_socket=""
					print("init reconnect")
					break
				try:
					msg["td"].append((time.time(),"sendall done"))
				except: 
					ignore=1

				if(msg.get("ack",0)==-1):
					comm_wait.append(("wf",time.time()))
					msg_out_ts=time.time()
					#print("increased comm_wait to "+str(len(comm_wait))+" entries for cmd "+msg["cmd"])

				#print("message send")
				if(msg.get("cmd"," ")=="wf"):
					if(msg.get("eof",0)==1):
#						print("[A "+time.strftime("%H:%M:%S")+"] -> uploading "+msg.get("fn")+" done")
						#os.remove(json.loads(send_msg).get("fn"))
						
						#print("[A "+time.strftime("%H:%M:%S")+"] -> upload took:"+str(time.time()-file_upload_start))
						if(trigger.TIMING_DEBUG):
#							msg["td"].append((time.time(),"upload done"))
#							old=msg["td"][0][0]
#							print("Debug of "+msg.get("fn")+"'s timing")
#							for a in msg["td"]:
#								p_state=(a[1]+"             ")[0:15]
#								p_t1=(str(int((a[0]-old)*1000))+"          ")[0:5]
#								p_t2=(str(int((a[0]-msg["td"][0][0])*1000))+"          ")[0:5]
#								
#								print("[A "+time.strftime("%H:%M:%S")+"] -> event:"+p_state+": "+p_t1+" / "+p_t2+" ms at "+str(a[0]))
#								old=a[0]
#							print("[A "+time.strftime("%H:%M:%S")+"] time between photos:"+str(time.time()-last_pic),end="")
#							print("[A "+time.strftime("%H:%M:%S")+"] delay "+str(time.time()-msg["td"][0][0]))
							if(time.time()-last_pic>15):
								pu_start_ts=0
								print("reset fps")

							last_pic=time.time()

							pu_num=pu_num+1
							if(pu_start_ts==0):
								pu_start_ts=time.time()
								pu_num=0
							else:
								print(str(pu_num/(time.time()-pu_start_ts))+"fps")
#								print("Uploaded "+str(pu_num)+" Frames in "+str((time.time()-pu_start_ts))+" this is "+str(pu_num*25/(time.time()-pu_start_ts))+"kBps or "+str(pu_num/(time.time()-pu_start_ts))+"fps")
#							print("\r\n\r\n")


		elif(len(msg_q)==0 and logged_in==1):
			td=[]
			td.append((time.time(),"start"))
			data=trigger.get_photo_state() # (take a picture, target path, high res)
			if(data[0]>0):
				upload_file(data[1],td,data[2]) 

#		if(mq_len!=len(msg_q)):
#			mq_len=len(msg_q)	
#			print("len msg_q="+str(len(msg_q)))
#			for a in range(0,len(msg_q)):
#				print("cmd ist: "+msg_q[a]["cmd"])
		
		############## free us if there is a lost packet #####################
		if(len(comm_wait)>0 and logged_in==1):
			if(len(msg_q)>0 and msg_out_ts!=0 and msg_out_ts+SERVER_TIMEOUT<time.time()):
				print("[A "+time.strftime("%H:%M:%S")+"] -> server did not send ack")
				comm_wait=[]
		############## free us if there is a lost packet #####################


		#************* sending end ******************#
	print("connection destroyed, reconnecting")		
	trigger.set_interval(0) # switch off the webstream, we wouldn't have ws beeing connected to us anyway after resign on
		
#exit()
