import time
import threading, sys, select, os


con=[]
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

#******************************************************#
def start():
	threading.Thread(target = start_debug, args = ()).start()

#******************************************************#
def start_debug():
	global s,last_action

	while(1):
		time.sleep(1)
		if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
			input=sys.stdin.readline()
			if(input[:1]=="q"):
				print("Quit")
				os._exit(1)
			elif(input[:1]=="s"):
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
			elif(input[:1]=="a"):
				print("Last submitted action: ",end="")
				print(last_action[0])	
			else:
				print("what do you mean by: "+input)
