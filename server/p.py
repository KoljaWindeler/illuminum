import sys,  threading, time, datetime
from clients import m2m_state,det_state
import send_mail

__author__ = 'kolja'

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
	print_out.append(poe("h","Heartbeats","Shows the Heartbeats of every client",0))
	print_out.append(poe("r","Rulemanager","Rulemanager output",0))
	print_out.append(poe("u","Uploades","Shows every uploaded file",1))
	print_out.append(poe("l","Login/logout","Shows every login/logout",1))
	print_out.append(poe("s","State Change","Shows every state change via movement or rule change",0))
	print_out.append(poe("d","Debug","Shows errors etc",1))
	print_out.append(poe("c","Camera","Shows uploads, livestream starts etc",1))
	print_out.append(poe("a","Alert","Shows alerts, emails etc",1))
	print_out.append(poe("v","Verbose","Shows a lot output, like requests etc",0))
	print_out.append(poe("w","very Verbose","Shows information about number of bytes send etc",0))
	print_out.append(poe("e","Error reporting","Shows programm errors, events that should not happen",1))

	while(1):
		input=sys.stdin.readline()
		input=input[0:len(input)-1] # strip newline
		if(len(input)==0):
			continue
		
		if(input[0]=="_" and len(input)>=3): #activate or deactivate outputs
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

		else:
			callback[0](input)

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


def err(input):
	try:
		rint2("==============================================","e","ERR",bcolors.FAIL)
		rint2(input,"e","ERR",bcolors.FAIL)
		send_mail.send("illuminum ERROR",input, files=[], send_to="KKoolljjaa@gmail.com",send_from="koljasspam493@gmail.com", server="localhost")
		input_log="["+time.strftime("%Y_%m_%d")+"] "+input+"\r\n"
		with open("err.txt", "a") as log_file:
			log_file.write(input_log)
			log_file.close()
		rint2("==============================================","e","ERR",bcolors.FAIL)
    									
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


def m2m_login(m2m,viewer):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	p_mid=("'"+m2m.mid+"'                  ")[0:17]
	rint2(p_mid+" / '"+p_alias+"' @ '"+p_account+"' log-in: OK, ->(M2M) set detection to '"+str(det_state[int(m2m.detection)])+"' (->"+str(viewer)+" ws_clients)","l","A_m2m",bcolors.OKGREEN)

def ws_login(ws):
	p_account=(ws.account+"          ")[0:10]
	p_login=(ws.login+"                                                ")[0:32]
	rint(bcolors.OKBLUE+"[A_ws  "+time.strftime("%H:%M:%S")+"] '"+p_login+"' @ '"+p_account+"' log-in: OK, ->(WS)"+bcolors.ENDC,"l")

def change_state(m2m,viewer):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	p_state=(str(m2m_state[m2m.state])+"                  ")[0:5]
	rint(bcolors.OKGREEN+"[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' / '"+p_alias+"' @ '"+p_account+"' changed state to: '"+p_state+"', detection: '"+str(det_state[m2m.detection])+"' (->"+str(viewer)+" ws_clients)"+bcolors.ENDC,"s")

def connect_ws_m2m(m2m,ws):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	p_login=(ws.login+"             ")[0:20]
	rint(bcolors.OKGREEN+"[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' / '"+p_alias+"' @ '"+p_account+"' <-> WS '"+p_login+"' "+str(ws.ip)+bcolors.ENDC,"l")


def show_ws(id,l,ws):
	if(id==-2):
		show_m2m(1,l,"")
		print(bcolors.WARNING+"we got "+str(l)+" ws-clients connected"+bcolors.ENDC)
	elif(id==-1):
		print(bcolors.WARNING+"WS login        | Account    | IP             | l-in | last_seen  | uuid | Location "+bcolors.ENDC)
		show_m2m(1,l,"")
	elif(id==0):
		p_login=(ws.login+"               ")[0:15]
		p_account=(ws.account+"               ")[0:10]
		p_ip=(str(ws.ip)+"                  ")[0:14]
		p_last_seen=(datetime.datetime.fromtimestamp(int(ws.last_comm)).strftime('%H:%M:%S')+"                         ")[0:10]
		p_qlen=(str(ws.snd_q_len)+"                    ")[0:8]
		p_uuid=(str(ws.uuid)+"                   ")[0:4]
		p_location=(str(ws.location)+"             ")[0:14]
		
		output=p_login+" | "+p_account+" | "+str(p_ip)+" | "+str(ws.logged_in)+"    | "+p_last_seen+" | "+p_uuid
		output+=" | "+p_location
		print(bcolors.WARNING+output+bcolors.ENDC)
	elif(id==1):
		show_m2m(1,"","")
		

def show_m2m(id,l,m2m):
	if(id==-2):
		show_m2m(1,l,m2m)
		print(bcolors.WARNING+"we got "+str(l)+" m2m-clients connected"+bcolors.ENDC)
	elif(id==-1):
		print(bcolors.WARNING+"M2M (short mid/alias) | Account    | Detection | State         | IP             | l-in | last_seen  | Area            | Version (nr/hash/sec)"+bcolors.ENDC)
		show_m2m(1,l,m2m)
	elif(id==0):
		p_mid=("                       "+str(m2m.mid))[-5:]
		p_alias=(m2m.alias+"                        ")[0:15]
		p_account=(m2m.account+"                    ")[0:10]
		p_ip=(str(m2m.ip)+"                         ")[0:14]
		p_area=(str(m2m.area)+"                     ")[0:15]
		p_last_seen=(datetime.datetime.fromtimestamp(int(m2m.last_comm)).strftime('%H:%M:%S')+"                         ")[0:10]
		if(m2m.detection>=0):
			p_detection=(det_state[m2m.detection]+"           ")[0:9]
		else:
			p_detection=(str(m2m.detection)+"                  ")[0:9]
		p_state=(m2m_state[int(m2m.state)]+"                   ")[0:13]
		output=p_mid+"/"+p_alias+" | "+p_account+" | "+str(p_detection)+" | "+(p_state)+" | "+str(p_ip)+" | "+str(m2m.logged_in)+"    | "
		output+=p_last_seen+" | "+p_area+" | "+str(m2m.v_short)+"/"+str(m2m.v_hash)+"/"+str(m2m.v_sec)
		print(bcolors.WARNING+output+bcolors.ENDC)
	elif(id==1):
		print(bcolors.WARNING+"-------------------------------------------------------------------------------------------------------------------------------------------------------"+bcolors.ENDC)



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
