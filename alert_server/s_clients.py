#An example of a class
class s_clients:
 
	def __init__(self, addr):
		self.ip = addr.getpeername()[0]
		self.port = addr.getpeername()[1]
		self.conn=addr
		self.description = "This shape has not been described yet"
		self.author = "Nobody has claimed to make this shape yet"
		self.openfile="" # stasr
		self.buffer=""
		self.fp=""
		self.id=-1
		self.logged_in=0
		self.last_comm=0