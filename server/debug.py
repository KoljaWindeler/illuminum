import time

class debug:
	def __init__(self,_alias):
		self.last_img_recv_ts=0
		self.first_img_recv_ts=0
		self.num_img_recv=0
		self.last_five_times=[]
		self.max_times=5
		self.alias=_alias
		self.p=""

	def update(self):
		o=""
		if(time.time()-self.last_img_recv_ts > 15):
			self.first_img_recv_ts=time.time()
			self.num_img_recv = -1
                                        
			self.last_five_times.clear()
			for i in range(0,self.max_times):
				self.last_five_times.append(0)

		else:
			for i in range(0,self.max_times-1):
				this_diff=str(round(time.time()-self.last_five_times[i],2))
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
		self.p="(Debug "+self.alias+") "+o

	def print(self):
		return self.p
