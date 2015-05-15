import sys,  threading, time, datetime
from clients import m2m_state,det_state

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
	print_out.append(poe("h","Heartbeats","Shows the Heartbeats of every client",1))
	print_out.append(poe("r","Rulemanager","Rulemanager output",0))
	print_out.append(poe("u","Uploades","Shows every uploaded file",1))
	print_out.append(poe("l","Login","Shows every login",1))
	print_out.append(poe("s","State Change","Shows every state change via movement or rule change",1))

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
	found=0
	for a in print_out:
		if(a.shortcut==sc):
			found=1
			if(a.state==1):
				print(input)
	if(not(found)):
		print("didn't recogice shortcut '"+sc+"'")


def m2m_login(m2m,viewer):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	rint("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' / '"+p_alias+"' @ '"+p_account+"' log-in: OK, ->(M2M) set detection to '"+str(det_state[int(m2m.detection)])+"' (->"+str(viewer)+" ws_clients)","l")

def ws_login(ws):
	p_account=(ws.account+"          ")[0:10]
	p_login=(ws.login+"                                                ")[0:32]
	rint("[A_ws  "+time.strftime("%H:%M:%S")+"] '"+p_login+"' @ '"+p_account+"' log-in: OK, ->(WS)","l")

def change_state(m2m,viewer):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	p_state=(str(m2m_state[m2m.state])+"                  ")[0:5]
	rint("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' / '"+p_alias+"' @ '"+p_account+"' changed state to: '"+p_state+"', detection: '"+str(det_state[m2m.detection])+"' (->"+str(viewer)+" ws_clients)","s")

def connect_ws_m2m(m2m,ws):
	p_alias=(m2m.alias+"          ")[0:12]
	p_account=(m2m.account+"          ")[0:10]
	p_login=(ws.login+"             ")[0:20]
	rint("[A_m2m "+time.strftime("%H:%M:%S")+"] '"+m2m.mid+"' / '"+p_alias+"' @ '"+p_account+"' <-> WS '"+p_login+"' "+str(ws.ip),"l")


def show_ws(id,l,ws):
	if(id==-2):
		show_m2m(1,l,"")
		print("we got "+str(l)+" ws-clients connected")
	elif(id==-1):
		print("WS login        | Account    | IP             | l-in | last_seen  | Q-length | uuid")
		show_m2m(1,l,"")
	elif(id==0):
		p_login=(ws.login+"               ")[0:15]
		p_account=(ws.account+"               ")[0:10]
		p_ip=(str(ws.ip)+"                  ")[0:14]
		p_last_seen=(datetime.datetime.fromtimestamp(int(ws.last_comm)).strftime('%H:%M:%S')+"                         ")[0:10]
		p_qlen=(str(ws.snd_q_len)+"                    ")[0:8]
		
		output=p_login+" | "+p_account+" | "+str(p_ip)+" | "+str(ws.logged_in)+"    | "+p_last_seen+" | "+p_qlen+" | "+ws.uuid
		print(output)
	elif(id==1):
		show_m2m(1,"","")
		

def show_m2m(id,l,m2m):
	if(id==-2):
		show_m2m(1,l,m2m)
		print("we got "+str(l)+" m2m-clients connected")
	elif(id==-1):
		print("M2M (short mid/alias) | Account    | Detection | State         | IP             | l-in | last_seen  | Area            | Coordinates")
		show_m2m(1,l,m2m)
	elif(id==0):
		p_alias=(m2m.alias+"               ")[0:15]
		p_account=(m2m.account+"               ")[0:10]
		p_ip=(str(m2m.ip)+"                  ")[0:14]
		p_area=(str(m2m.area)+"                  ")[0:15]
		p_last_seen=(datetime.datetime.fromtimestamp(int(m2m.last_comm)).strftime('%H:%M:%S')+"                         ")[0:10]
		if(m2m.detection>=0):
			p_detection=(det_state[m2m.detection]+"           ")[0:9]
		else:
			p_detection=(str(m2m.detection)+"                  ")[0:9]
		p_state=(m2m_state[int(m2m.state)]+"                   ")[0:13]
		output=str(m2m.mid)[-5:]+"/"+p_alias+" | "+p_account+" | "+str(p_detection)+" | "+(p_state)+" | "+str(p_ip)+" | "+str(m2m.logged_in)+"    | "
		output+=p_last_seen+" | "+p_area+" | "+str(m2m.latitude)+"/"+str(m2m.longitude)
		print(output)
	elif(id==1):
		print("-------------------------------------------------------------------------------------------------------------------------------------------------------")



def show_status():
	for a in print_out:
		print("Shortcut '"+a.shortcut+"' for "+a.name+" is "+str(a.state))

callback = [subscribe_callback]
print_out =[]
