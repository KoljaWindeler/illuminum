class watcher:
	def __init__(self):
		self.clients = [] 				# list of all watcher_m2m clients
		self.handle_movements_stopped = ""			# the handle for the 'after'-functions
		self.handle_movements_started = ""			# the handle for the 'after'-functions
		self.output = 0		# state of the output
		
class watcher_m2m:
	def __init__(self,mid,state):
		self.mid = mid 				# the mid of the m2m
		self.state = state			# the state of the m2m
