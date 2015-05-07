import sys,  threading, time

__author__ = 'kolja'
#******************************************************#

def subscribe_callback(fun):
	if callback[0]==subscribe_callback:
		callback[0]=fun
	else:
		callback.append(fun)
#******************************************************#


def start():
	threading.Thread(target = start_listen, args = ()).start()

def start_listen():
	while(1):
		input=sys.stdin.readline()
		callback[0](input)


callback = [subscribe_callback]
