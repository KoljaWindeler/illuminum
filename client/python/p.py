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
#******************************************************#
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'

	RED = '\033[91m'
	CYAN = '\033[96m'
	WHITE = '\033[97m'
	YELLOW = '\033[93m'
	MAGENTA = '\033[95m'
	GREY = '\033[90m'
	BLACK = '\033[90m'
	DEFAULT = '\033[99m'

	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
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


def start(alive):
	threading.Thread(target = start_listen, args = (alive,)).start()

def start_listen(alive):

	while(alive):
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
					input_p="("+str(sc)+")["+time.strftime("%Y_%m_%d %H:%M:%S")+"] "+input
					print(input_p)
					
					input_log="["+time.strftime("%Y_%m_%d")+"] "+input+"\r\n"
					with open("log.txt", "a") as log_file:
						log_file.write(input_log)
						log_file.close()
    				
					
		if(not(found)):
			print("didn't recogice shortcut '"+sc+"'")
	except:
		ignore=1

def rint2(input, sc, snd="", color=0):
	try:
		found=0
		for a in print_out:
			if(a.shortcut==sc):
				found=1
				##### prepare print and log #####
				# color
				c_in=""
				c_out=""
				if(color!=0):
					c_in=color
					c_out=bcolors.ENDC
				# shortcut
				shortcut="("+str(sc)+")"
				# timestamp
				timestamp_s = time.strftime("%H:%M:%S")
				timestamp_l = time.strftime("%H:%M:%S")
				# sender
				sender="" 
				if(snd!=""):
					sender=(str(snd)+"     ")[0:5]+" "

				# print it if active
				if(a.state==1): 
					# assemble
					text = c_in+shortcut+"["+sender+timestamp_s+"] "+input+c_out
					print(text)

				# log it in each case		
				# assemble
				text = shortcut+"["+sender+timestamp_l+"] "+input+"\r\n"
				with open("log.txt", "a") as log_file:
					log_file.write(text)
					log_file.close()
    				
					
		if(not(found)):
			print("didn't recogice shortcut '"+sc+"'")
	except:
		ignore=1

def warn(input):
	try:
		rint2("==============================================","e","WARN",bcolors.WARNING)
		rint2(input,"e","WARN",bcolors.WARNING)
		input_log="["+time.strftime("%Y_%m_%d")+"] "+input+"\r\n"
		with open("err.txt", "a") as log_file:
			log_file.write(input_log)
			log_file.close()
		rint2("==============================================","e","WARN",bcolors.WARNING)
    									
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
print_out.append(poe("v","Verbose","Shows a lot output, like requests etc",0))
print_out.append(poe("l","Logging","Regular logging",1))
print_out.append(poe("d","Debug","Debug information",1))
print_out.append(poe("r","RGB","led dimming information",0))
print_out.append(poe("t","Trigger","printing changes from the trigger",0))
print_out.append(poe("g","GPIO","printing IO info",0))
print_out.append(poe("e","ERROR","Errors and warnings",1))

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
