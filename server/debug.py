import time

class debug_client:
	def __init__(self,_mid,_alias):
		self.last_img_recv_ts=0
		self.first_img_recv_ts=0
		self.num_img_recv=0
		self.last_five_times=[]
		self.max_times=5
		self.alias=_alias
		self.p=""	
		self.mid=_mid

	def update(self):
		o=""
		if(time.time()-self.last_img_recv_ts > 15):
			self.first_img_recv_ts=time.time()
			self.num_img_recv = -1
                                        
			self.last_five_times.clear()
			for i in range(0,self.max_times):
				self.last_five_times.append(0)

		else:
			for i in range(1,self.max_times-1):
				this_diff=round(self.last_five_times[i-1]-self.last_five_times[i],2)
				if(this_diff>100):
					this_diff="0.00"
				this_diff=str(this_diff)
				while(len(this_diff)<4):
					this_diff=this_diff+"0"
				o=o+" "+this_diff

			for i in range(0,self.max_times-1):
				self.last_five_times[4-i]=self.last_five_times[3-i]
			self.last_five_times[0]=time.time()
                                
		self.num_img_recv = self.num_img_recv+1
		self.last_img_recv_ts=time.time()

		if(self.num_img_recv>=1):
			this_diff=str(round(self.num_img_recv/(time.time()-self.first_img_recv_ts),2))
			while(len(this_diff)<4):
					this_diff=this_diff+"0"
			o=o[1:]+" / "+this_diff+" fps"
		else:
			o=o[1:]+" / "
		self.p="("+self.alias+") "+o

	def print(self):
		return self.p

class debug:
	def __init__(self,_alias):
		self.clients=[]
		self.alias=_alias

	def update(self,mid):
		for client in self.clients:
			if(client.mid==mid):
				client.update()
				return 0

		# not found, add new
		client=debug_client(mid,self.alias)
		self.clients.append(client)
		self.update(mid)

	def print(self,mid):
		for client in self.clients:
			if(client.mid==mid):
				return client.print()

		# not found, add new
		client=debug_client(mid,self.alias)
		self.clients.append(client)
		return self.print(mid)
				
			


class loading_assist:
	def __init__(self,server_ws,server_m2m):
		self.last_checked=0
		self.clients=[]
		self.interval=1
		self.ws=server_ws
		self.m2m=server_m2m

	def check(self,msg_q_ws):
		if(time.time()>self.last_checked+self.interval):
			self.last_checked=time.time()

			# collect the debug_ts from all clients in the server_WS and server_M2M
			# as long as those tasks are running the time shall be <1, if one hangs
			# time will rise
			o="WS:"
			for cli in self.ws.clients:
				o=o+str(round(time.time()-cli.debug_ts,1))+" "

			o=o+" | m2m:"
			for cli in self.m2m.clients:
				o=o+str(round(time.time()-cli.debug_ts,1))+" "

		
			for cli in self.clients:
				msg={}
				msg["cmd"]="hb_fast"
				msg["time"]=str(round((time.time()*100)%10000,0)/100)
				msg["tasks"]=o
				msg_q_ws.append((msg,cli))


	
	def subscribe(self,_cli):
		self.clients.append(_cli)

	def unsubscribe(self,_cli):
		for cli in self.clients:
			if(cli==_cli):
				self.clients.remove(cli)
	
				
