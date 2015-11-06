import select, os
import sys,  threading, time, datetime

__author__ = 'kolja'
#******************************************************#

def subscribe_callback(fun):
	if callback[0]==subscribe_callback:
		callback[0]=fun
	else:
		callback.append(fun)
#******************************************************#

class poe:
	def __init__(self,s,n,d,state):
		self.shortcut =s  	# e.g. U
		self.name=n		# e.g. Upload
		self.description = d	# e.g. Shows the filename of every upload
		self.state = state	# e.g. active
	def set_state(self,state):
		self.state=state

#******************************************************#


def start():
	threading.Thread(target = start_listen, args = ()).start()

def start_listen():
	print_out.append(poe("v","Verbose","Shows a lot output, like requests etc",0))

	while(1):
		input=sys.stdin.readline()
		input=input[0:len(input)-1] # strip newline
		if(len(input)==0):
			continue

		if(input[0]=="q"):
			print("Quit")
			os._exit(1)
		elif(input[0]=="s"):
			print("Status:");
			print("len(con.msg_q):",end="")
			print(con[2])
			print("len(unacknowledged_msg):",end="")
			print(con[1])
			print("con.logged_in:",end="")
			print(con[0])
			print("con.ack_req_ts:",end="")
			print(con[3],end="")
			print(" vs time:",end="")
			print(time.time())
		elif(input[0]=="a"):
			print("Last submitted action: ",end="")
			print(last_action[0])	
		elif(input[0]=="_" and len(input)>=3): #activate or deactivate outputs
			found=0
			for a in print_out:
				if(input[1]==a.shortcut):
					if(int(input[2])==1):
						a.state=1
						print("switched output of '"+a.description+"' on")
						found=1
						break
					elif(int(input[2])==0):
						a.state=0
						print("switched output of '"+a.description+"' off")
						found=1
						break
			if(input[1]=="_"):
				show_status()
				found=1
			elif(input[1]=="a"):
				state=-1
				found=1
				if(int(input[2])==1):
					state=1
				elif(int(input[2])==0):
					state=0
				if(state!=-1):
					for a in print_out:
						a.state=state
					if(state):
						print("switched all output on")
					else:
						print("switched all output off")
				

			if(not(found)):
				print("")
				print("I haven't understood you sequece, possible sequences are:")
				print("_a for all")
				for a in print_out:
					print("_"+str(a.shortcut)+" for '"+str(a.description)+"'")
				print("followed by '1' or '0'")
				print("")
		

def rint(input,sc):
	try:
		found=0
		for a in print_out:
			if(a.shortcut==sc):
				found=1
				if(a.state==1):
					input="("+str(sc)+")"+input
					print(input)
					
					input_log="["+time.strftime("%Y_%m_%d")+"] "+input+"\r\n"
					with open("log.txt", "a") as log_file:
						log_file.write(input_log)
						log_file.close()
    				
					
		if(not(found)):
			print("didn't recogice shortcut '"+sc+"'")
	except:
		ignore=1




def show_status():
	i=0
	p_out=""
	p_out2=""
	for a in print_out:
		p_out2="Shortcut '"+a.shortcut+"' for "+a.name
		for b in range(0,50):
			p_out2+="."
		p_out2=p_out2[0:50]
		if(a.state):
			p_out2+=".....active"
		else:
			p_out2+=".not active"
		i+=1
		if(i%2==0):
			print(p_out+p_out2)
			p_out2=""
			p_out=""
		else:
			p_out=p_out2+" | "
	if(p_out!=""):
		print(p_out)
		
	print("")
		

callback = [subscribe_callback]
print_out =[]

con=[]
con.append(0)
con.append(0)
con.append(0)
con.append(0)

last_action=[]
last_action.append("")

def set_con(log,unack,msg_q,ack_req_ts):
	con[0]=log
	con[1]=unack
	con[2]=msg_q
	con[3]=ack_req_ts

def set_last_action(action):
	global last_action
	last_action[0]=action
	#print(action)

def start_debug():
	global s,last_action

	while(1):
		time.sleep(1)
		if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
			input=sys.stdin.readline()
