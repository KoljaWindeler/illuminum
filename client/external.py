def movements_stopped():
	print("movement stopped function called, starting timer")
	#return threading.Timer(20*60*1000,switch_monitor_off)
	return threading.Timer(20,switch_monitor_off)
	
def movements_started():
	#str(subprocess.Popen(["xset","s","off"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	#str(subprocess.Popen(["xset","-dpms"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	#str(subprocess.Popen(["xset","s","noblank"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	print("movement started function called")
	return ""
	
def switch_monitor_off():
	#str(subprocess.Popen(["xset","+dpms"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	#str(subprocess.Popen(["xset","s","activate"],stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE).communicate()[0].decode())
	print("for testing: switching the monitor off")
