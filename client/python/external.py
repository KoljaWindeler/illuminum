import threading,subprocess,os
import p

timer_sec=20*60

def movements_stopped():
	p.rint("MOVEMENT, no motion, starting timer","l")
	return threading.Timer(1,dummy)
	#return threading.Timer(timer_sec,switch_monitor_off)
	
def movements_started():
	p.rint("MOVEMENT, motion, turn display on","l")
	path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","externals","disp_on.sh")
	str(subprocess.Popen([path],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	return threading.Timer(1,dummy)
	
def switch_monitor_off():
	p.rint("MOVEMENT, no motion for long time, turn display off","l")
	path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","externals","disp_off.sh")
	str(subprocess.Popen([path],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())

def dummy():
	return ""
