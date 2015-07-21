__author__ = 'kolja'
import time, datetime, p

# 4 # rule_manager, used to hold multiple rule_accounts
# .data																			list of all "rule_accounts"
# .is_account(self, account)								returns 1 if the given account already exists in the list data
# .add_account(self, account)							add the given object (type rule_account) to the list data
# .rem_account(self, account)							removes the given account from the list data
# .is_area_in_account(self,account,area)		return 1 if the given area is in the given account
# .add_area_to_account(self, account, area) can add a area of type "area" to an account of type "rule_account"

# 3 # rule_account, used to hold multiple areas in one account
# .account																	string that holds the account name for easy identification
# .areas		 																list of class "area"
# .next_ts															this ts should tell us when we should run a check again
# .is_area(self,area)												returns 1 if the given area is already part of the areas list
# .add_area(self, area)											adds an object of class "area" to the list areas, this will trigger the reload_rules of the added area
# .rem_area(self, area) 										removes an object of class "area" from the list areas

# 2 # area, areas carry 0..N rules and the logic to evaluate them to switch the detection on/off in their area
# .area																			string that defines for for area they are used
# .account																	string that defines for what account they are used
# .rules																			list of class "rules"
# .sub_rules																list of class "rules"
# .db																				handle to the mysql db
# .get_next_ts(self)													get the next time base alert for this area
# .clear_rules(self)													clears rules and sub_rules
# .add_rule(self, id, conn, arg1, arg2)				adds a new rule, this function is used by the reload_rules
# .add_sub_rule(self, id, conn, arg1, arg2)	adds a new sub_rule, this function is used by the reload_rules
# .print_rules(self)													debug
# .reload_rules(self)												reloads all rules via the db handle
# .get_sub_rule(self, rule_id)							return conn,arg1 and arg2 for the given rule_id and empty if not found
# .eval_rule(self,conn, arg1, arg2,depth, use_db)		return 1 if rule applies
# .check_rules(self,use_db)												returns 1 if any of the rules applies

# 1 # rules, a simple rule data container without logic
# .id																				to be identified and found
# .conn																string connecting arg1 and arg2
# .arg1														 					argument 1 for rule
# .arg2 																			argument 2 for rule


#*********************************** THIS IS HOW IT SHOULD WORK ******************************#

## create rule manager
#rm = rule_manager()

# add an account but check first if it is already there
#if(not(rm.is_account(m2m.account))):
#	print("account did not exist, adding")
#	new_rule_account=rule_account(m2m.account)
#	rm.add_account(new_rule_account)
#
# then check the same for the area, if there was NO m2m and NO ws connected, the area wont be in the rm, otherwise it should be there
#if(not(rm.is_area_in_account(m2m.account,m2m.area))):
#	print("area did not exist, adding")
#	new_area=area(m2m.area,m2m.account,db) # will load rule set on its own from the database
#	rm.add_area_to_account(m2m.account,new_area)
#
# when ever a environment change (like a ws changed his location or wifi SSID) happens do this:
# acc=rm.get_account(account) # where account is the string of the account
# for b in acc.areas:
# 	detection_state=b.check_rules(use_db) 	# get the state
#	db.update_det(login,account,b.area,detection_state)
# after that you may want to tell your clients to change state
#
# to check if a time_based trigger occurred do this:
# acc=rm.get_account(account) # where account is the string of the account
# if(now>acc.next_ts or acc.check_day_jump()):	#check_day_jump will return 1 if there was a day_based_rule and we've checked last yesterday
#	acc.update_next_ts()
#	# at least one rule indicated that we should recheck the account
#	# at this point you should call the function that handles the environment changes or at least to this
# 	for b in acc.areas:
# 		detection_state=b.check_rules(use_db) 	# get the state
#		db.update_det(login,account,b.area,detection_state)
# after that you may want to tell your clients to change state


#*************************************#
# this is the manager, the highest class
# its purpose is to hold and manage all
# accounts!
# it can add, remove and check if a account exists
# and even return it back for more details work
# it can also check/add a area to an account
#*************************************#
class rule_manager:
	def __init__(self):
		self.data = []
	#############################################################	
	def add_account(self, account):
		self.data.append(account)
	#############################################################	
	def is_account(self, account):
		for a in self.data:
			if(a.account==account):
				return 1
		return 0
	#############################################################	
	def rem_account(self, account):
		for a in self.data:
			if(a.account==account):
				self.data.remove(a)
				return 1
		return 0
	#############################################################	
	def is_area_in_account(self,account,area):
		for a in self.data:
			if(a.account==account):
				return a.is_area(area)
				break
		return 0
	#############################################################	
	def add_area_to_account(self, account, area):
		for a in self.data:
			if(a.account==account):
				return a.add_area(area)
				break
		return 0
	#############################################################
	def print_all(self):
		reactivate=0
		for p_rule in p.print_out:
			if(p_rule.shortcut=="r"):
				if(not(p_rule.state)):
					p_rule.state=1
					reactivate=1
				break
			
		now=time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
		p.rint("== I'm the rule manager, I have "+str(len(self.data))+" accounts registered at ts: "+str(now)+"==","r")
		i=1
		for a in self.data:
			p.rint("","r")
			p.rint("|+ Account "+str(i)+"/"+str(len(self.data)),"r")
			a.print_account()
			i+=1
		p.rint("","r")
		p.rint("== End of rule manager output ==","r")
		
		#### stop output again
		if(reactivate):
			for p_rule in p.print_out:
				if(p_rule.shortcut=="r"):
					p_rule.state=0
					break
	#############################################################
	def get_account(self,account):
		for a in self.data:
			if(a.account==account):
				return a
		return -1	

#*************************************#
# this is our account class. the second highest animal
# purpose of the account is to hold the area
# an account has a timestamp that tells us
# when the next check of the rules is required
#*************************************#
class rule_account:
	def __init__(self,account):
		self.account=account
		self.areas = []
		self.next_ts = -1
		self.day_last_check=-1
	#############################################################
	def add_area(self, area):
		self.areas.append(area)
		self.update_next_ts()
	#############################################################
	def check_day_jump(self):
		today=time.localtime()[2]
		if(self.day_last_check!=today):
			self.day_last_check=today
			if(self.next_ts==86400):
				return 1
		return 0
	#############################################################
	def update_next_ts(self):
		for a in self.areas:
			next_event_for_this_area=a.get_next_ts()
			if(next_event_for_this_area>-1 and (next_event_for_this_area<self.next_ts or self.next_ts==-1)):
				self.next_ts=next_event_for_this_area
		return 0
	#############################################################
	def rem_area(self, area):
		for a in self.areas:
			if(a.area==area):
				self.areas.remove(a)
				return 1
		return 0
	#############################################################
	def is_area(self,area):
		for a in self.areas:
			if(a.area==area):
				return 1
				break
		return 0
	#############################################################
	def get_area(self,area):
		for a in self.areas:
			if(a.area==area):
				return a
				break
		return 0
	#############################################################
	def print_account(self):
		p.rint("|+ This is account '"+self.account+"' I have "+str(len(self.areas))+" areas:","r")
		i=1
		for a in self.areas:
			p.rint("||+ Area "+str(i)+"/"+str(len(self.areas)),"r")
			a.print_rules()
			i+=1
		p.rint("|+ my next timebased trigger event is at '"+str(self.next_ts)+"'","r")
	
#*************************************#
# an area is the third animal or second from the bottom
# it hold the rules, and sub_rules and can check them
#*************************************#
class area:
	def __init__(self, area, account, db):
		self.area = area
		self.account = account
		self.db = db
		self.has_override_detection_on=0
		self.has_override_detection_off=0
		self.rules = []
		self.sub_rules = []
		self.reload_rules()

	#**********************************************************#
	# This function shall go through all rules and subrules and
	# find some time based trigger, it will return a timestamp
	# in UTC between 0..86400 where 86400 means that we have a
	# day rule. -1 means no time trigger
	#**********************************************************#
	def get_next_ts(self):
		now=time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
		closest_event=-1

		for c_rules in [self.rules,self.sub_rules]:
			for r in c_rules:
				if(r.conn=="time"):
					if(int(r.arg1)>now and (closest_event==-1 or int(r.arg1)<closest_event)):
						closest_event=int(r.arg1)
					if(int(r.arg2)>now and (closest_event==-1 or int(r.arg2)<closest_event)):
						closest_event=int(r.arg2)
				elif(r.conn=="day"):
					if(closest_event==-1 or now>closest_event):
						closest_event=86400
				elif(r.conn=="*" or r.conn=="/"): # override with enddate
					if(int(r.arg1)>0):
						# argh!! the "best before"-timestamp of an override is written in UTC sec since epoch.
						# but our closest_event will be local time and only seconds since dawn of the day .. (as an event at 5pm should always be at 5pm)
						if (time.localtime().tm_isdst == 0):
							offset = time.timezone  
						else:
							offset = time.altzone 
						# UTC ts - UTC ts @ dawn of the day - timezone offset = seconds after dawn in localtime
						change=int(int(r.arg1)-(time.time()-time.time()%86400+offset)) # relativ time stamp to today
						if(change>now and (closest_event==-1 or change<closest_event)):
							closest_event=change

		return closest_event
	#############################################################
	def add_sub_rule(self, id, conn, arg1, arg2):
		self.sub_rules.append(rule(id,conn,arg1,arg2))
	#############################################################
	def append_rule(self, conn,arg1,arg2):
		id=self.db.append_rule(self.account,self.area,conn,arg1,arg2)
		self.add_rule(id,conn,arg1,arg2)
	#############################################################
	def add_rule(self, id, conn, arg1, arg2):
		self.rules.append(rule(id,conn,arg1,arg2))
		if(conn=="*"):
			self.has_override_detection_on=1
		elif(conn=="/"):
			self.has_override_detection_off=1
	#############################################################
	def clear_rules(self):
		self.rules = []
		self.sub_rules = []
	#############################################################
	def reload_rules(self):
		# clear all rules
		self.clear_rules()
		# load new sets from database
		db_rules=self.db.load_rules(self.area,self.account,0) 				# 0=rules, 1=sub_rules
		db_sub_rules=self.db.load_rules(self.area,self.account,1)	# 0=rules, 1=sub_rules
		#print(db_rules)
		# add them
		for r in db_rules:
			self.add_rule(r["id"],r["conn"],r["arg1"],r["arg2"])
		for r in db_sub_rules:
			self.add_sub_rule(r['id'],r['conn'],r['arg1'],r['arg2'])
		# print for debugging
		#self.print_rules()
		return 0
	#############################################################
	def explain_rule(self,r,on,i):
		## msg
		p_arg1=""
		p_arg2=""
		p_conn=""
		
		###############
		if(str(r.conn)=="nobody_at_my_geo_area"):
			if(on):
				p_conn="Activating protection, because nobody is near "+self.area+"."
			else:
				p_conn="Not activating protection, because actually there are "
				user_count=self.db.user_count_on_area(self.account, self.area)
				if(user_count!=-1): # no db problem
					user_count=int(user_count["COUNT(*)"])
				p_conn+=str(user_count)+" user close to "+self.area
				if(user_count>0):
					p_conn+=": "
					user_present=self.db.user_on_area(self.account,self.area)
					ii=0
					for u in user_present:
						ii+=1
						p_conn+=u["login"]
						if(ii<user_count):
							p_conn+=", "	
										
		###############
		elif(str(r.conn)=="AND"):
			if(on):
				p_conn="Activating protection, because both subrules id="+str(r.arg1)+" and id="+str(r.arg2)+" are true"
			else:
				p_conn="Not activating protection, because not both subrules id="+str(r.arg1)+" and id="+str(r.arg2)+" are true"
		###############
		elif(str(r.conn)=="/" or str(r.conn)=="*"):
			if(str(r.conn)=="/"):
				p_conn="OVERRIDE: this will deactivate the protection"
			else:
				p_conn="OVERRIDE: this will activate the protection"
			if(int(r.arg1)>0):
				p_conn+=", until "+str((datetime.datetime.fromtimestamp(int(r.arg1))).strftime('%y_%m_%d %H:%M:%S'))
			else:
				p_conn+=", until this rule is being deleted"
		###############
		else:
			p_conn="conn: "+str(r.conn)
			if(not(str(r.arg1)=="")):
				p_arg1=", arg1: "+str(r.arg1)
			if(not(str(r.arg2)=="")):
				p_arg2=", arg2: "+str(r.arg2)
			p_conn+=p_arg1+p_arg2
		###############
			
		return str(i)+"/"+str(len(self.rules))+" id: ("+str(r.id)+") "+p_conn
		## msg
		
	#############################################################
	def print_rules(self,bars=1,account_info=1,print_out=1):
		ret=""
		if(bars):
			ret+="|||+ "
		
		if(account_info):
			ret+="This is area '"+self.area+"' on account '"+self.account+"'. I have "
			ret+=str(len(self.rules))+" active rules and "+str(len(self.sub_rules))+" subrules\r\n"
		i=1
		if(bars):
			ret+="|||+ "
		ret+="Rules: (protection activated if one or more of them is true)\r\n"
		for r in self.rules:
			## marker
			g=0
			if(bars):
				ret+="||||- "
			if(self.eval_rule(r.conn,r.arg1,r.arg2,10,1,r.id)>=1):
				ret+="<g>"
				g=1
			else:
				ret+="<r>"
			## marker
			ret+=self.explain_rule(r,g,i)
			## marker
			if(g):
				ret+="</g>\r\n"
			else:
				ret+="</r>\r\n"
			## marker
			i+=1
			
		if(len(self.rules)==0):
			if(bars):
				ret+="||||- "
			ret+="none\r\n"

		i=1
		if(bars):
			ret+="|||\r\n"
			ret+="|||+ "
		ret+="Sub-Rules:\r\n"
		
		for r in self.sub_rules:
		## marker
			g=0
			if(bars):
				ret+="||||- "
			if(self.eval_rule(r.conn,r.arg1,r.arg2,10,1,r.id)>=1):
				ret+="<g>"
				g=1
			else:
				ret+="<r>"
			## marker
			ret+=self.explain_rule(r,g,i)
			## marker
			if(g):
				ret+="</g>\r\n"
			else:
				ret+="</r>\r\n"
			## marker
			i+=1
			
		if(len(self.sub_rules)==0):
			if(bars):
				ret+="||||- "
			ret+="none\r\n"
			
		if(print_out):
			p.rint(ret,"r")
			return 0
		
		return ret
		
	#############################################################		
	def check_rules(self,use_db):
		ret=0 					# assume false
		for r in self.rules:
			res=self.eval_rule(r.conn, r.arg1, r.arg2,10,use_db,r.id)
			if(res==-1): 		# -1 == override off (/), return 0 without further checks
				return 0		
			elif(res==2): 		# 2 == override on (*), return 1 without further checks
				return 1
			elif(res):			# if 1, set ret but keep checking
				ret=1
		return ret
	#############################################################	
	def get_sub_rule(self, rule_id):
		conn=""
		arg1=""
		arg2=""
		for sr in self.sub_rules:
			#print("vergleiche "+str(sr.id)+" mit "+str(rule_id))
			if(int(sr.id)==int(rule_id)):
				conn=sr.conn
				arg1=sr.arg1
				arg2=sr.arg2
		return (conn,arg1,arg2)
	#############################################################
	def rm_override(self, override):
		del_list=[]
		if(override=="*"):
			self.has_override_detection_on=0
			for r in self.rules:
				if(r.conn=="*"):
					del_list.append(r)
		elif(override=="/"):
			self.has_override_detection_off=0
			for r in self.rules:
				if(r.conn=="/"):
					del_list.append(r)

		for r in del_list:
			self.rm_rule(r.id)
	#############################################################
	def rm_rule(self, id):
		found=0
		for r in self.rules:
			if(r.id==id):
				self.rules.remove(r)
				found=1
				break;
			
		if(not(found)):
			for r in self.sub_rules:
				if(r.id==id):
					self.sub_rules.remove(r)
					break;
				
		if(not(self.db.rm_rule(id)==0)):
			p.rint("Delete rule "+str(id)+" failed","r")
	#############################################################
	def eval_rule(self,conn, arg1, arg2, depth, use_db, id):
		if(depth<0):
			return 0
			
		## AND sub rule based
		if(conn=="AND"):
			(conn_1,arg1_1,arg2_1) = self.get_sub_rule(arg1)
			(conn_2,arg1_2,arg2_2) = self.get_sub_rule(arg2)
			#print("fetched for subrule "+str(arg1)+" this:"+str(conn_1)+"/"+str(arg1_1)+"/"+str(arg2_1))
			#print("fetched for subrule "+str(arg2)+" this:"+str(conn_2)+"/"+str(arg1_2)+"/"+str(arg2_2))
			res_1=self.eval_rule(conn_1,arg1_1,arg2_1,depth-1,use_db,arg1) # arg1 is rule id
			res_2=self.eval_rule(conn_2,arg1_2,arg2_2,depth-1,use_db,arg2)
			if(res_1 and res_2):
				return 1
		## AND  sub rule based
		
		## NOT sub rule based
		elif(conn=="NOT"):
			(conn_1,arg1_1,arg2_1) = self.get_sub_rule(arg1)
			res_1=self.eval_rule(conn_1,arg1_1,arg2_1,depth-1,use_db,arg1)
			if(not(res_1)):
				return 1
		## NOT sub rule based
		
		## catch none - always off
		elif(conn=="/"):
			arg1=int(arg1)
			if(arg1>0): # with time limit
				if(arg1>time.time()):					
					return -1
				else:
					self.rm_rule(id)
					#return 0 see below
			else: # forever
				return -1
		## catch none - always off
		
		## catch all - always on
		elif(conn=="*"):
			arg1=int(arg1)
			if(arg1>0): # with time limit
				if(arg1>time.time()):					
					return 2
				else:
					self.rm_rule(id)
					#return 0 see below
			else: # forever
				return 2
		## catch all - always on
		
		## time based
		elif(conn=="time"):
			#this now is timezoned cleared (the niklas way)
			now=time.localtime()[3]*3600+time.localtime()[4]*60+time.localtime()[5]
			if(int(arg2)>int(arg1)): # meaning the user defined in the rule something like between 06:00 and 18:00
				if(now>int(arg1) and now<int(arg2)):
					return 1
			elif(int(arg2)<int(arg1)): # meaning alert active between 18:00 and 06:00
				if (now>int(arg1) and now<(int(arg2)+86400)):
					return 1
		## time based
		
		## week day based
		elif(conn=="day"):
			today=datetime.datetime.today().weekday()
			#print("heute ist:"+str(today)+" arg1: "+str(arg1))
			if(int(today)==int(arg1)):
				return 1
		## week day based
		
		## GEO location based
		elif(conn=="nobody_at_my_geo_area"):
			if(use_db):
				# Step 0: our area is known, it is "self.area"
				# Step 1: count user from this account, being logged on to this  (our) area
				try:
					user_count=self.db.user_count_on_area(self.account, self.area)
					#print("user_count_on_area gave us:")
					#print(user_count)
					#print("eoo")
					if(user_count!=-1): # no db problem
						user_count=int(user_count["COUNT(*)"])
					#print("meaning")
					#print(user_count)
					#print("eoo")

					# step 2: if user count == 0 the rule "nobody at geo area" is true
						if(user_count==0):
							return 1
				except:
					return 0
			else:
				#print("skipped")
				return 0
		## GEO location based
		
		## WLAN location based
		elif(conn=="wlan_area"):
			wlan_area=arg1
			return 0
		## WLAN location based
		
		return 0
#############################################################
#############################################################
class rule:
	def __init__(self, id, conn, arg1, arg2):
		self.id = id
		self.conn = conn
		self.arg1 = arg1
		self.arg2 = arg2
