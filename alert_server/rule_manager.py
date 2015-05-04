__author__ = 'kolja'


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
# .is_area(self,area)												returns 1 if the given area is already part of the areas list
# .add_area(self, area)											adds an object of class "area" to the list areas, this will trigger the reload_rules of the added area
# .rem_area(self, area) 										removes an object of class "area" from the list areas

# 2 # area, areas carry 0..N rules and the logic to evaluate them to switch the detection on/off in their area
# .area																			string that defines for for area they are used
# .account																	string that defines for what account they are used
# .rules																			list of class "rules"
# .sub_rules																list of class "rules"
# .db																				handle to the mysql db
# .clear_rules(self)													clears rules and sub_rules
# .add_rule(self, id, conn, arg1, arg2)				adds a new rule, this function is used by the reload_rules
# .add_sub_rule(self, id, conn, arg1, arg2)	adds a new sub_rule, this function is used by the reload_rules
# .print_rules(self)													debug
# .reload_rules(self)												reloads all rules via the db handle
# .get_sub_rule(self, rule_id)							return conn,arg1 and arg2 for the given rule_id and empty if not found
# .eval_rule(self,conn, arg1, arg2,depth)		return 1 if rule applies
# .check_rules(self)												returns 1 if any of the rules applies 

# 1 # rules, a simple rule data container without logic
# .id																				to be identified and found
# .connector																string connecting arg1 and arg2
# .arg1														 					argument 1 for rule
# .arg2 																			argument 2 for rule


## create rule manager
#rm = rule_manager()

## for every box coming up
#if(not(rm.is_account("jkw"))):
#	new_rule_account=rule_account("jkw")
#	rm.append(new_account_rules)

#if(not(rm.is_area_in_account("jkw","home"))):
#	new_area=area("home","jkw",db) # will load rule set on its own
#	rm.add_area_to_account(new_area,"jkw")


class rule_manager:
	def __init__(self):
		self.data = []
		
	def add_account(self, account):
		self.data = account
		
	def is_account(self, account):
		for a in self.data:
			if(a.account==account):
				return 1
		return 0
		
	def rem_account(self, account):
		for a in self.data:
			if(a.account==account):
				self.data.remove(a)
				return 1
		return 0
		
	def is_area_in_account(self,account,area):
		for a in self.data:
			if(a.account==account):
				return a.is_area(area)
				break
		return 0
		
	def add_area_to_account(self, account, area):
		for a in self.data:
			if(a.account==account):
				return a.add_area(area)
				break
		return 0

class rule_account:
	def __init__(self,account):
		self.account=account
		self.areas = []
	
	def add_area(self, area):
		self.areas.append(area)
		
	def rem_area(self, area):
		for a in self.areas:
			if(a.area==area):
				self.areas.remove(a)
				return 1
		return 0
		
	def is_area(self,area):
		for a in self.areas:
			if(a.area==area):
				return 1
				break
		return 0

class rule:
	def __init__(self, id, conn, arg1, arg2):
		self.id = id
		self.conn = conn
		self.arg1 = arg1
		self.arg2 = arg2

class area:
	def __init__(self, area, account, db):
		self.area = area
		self.account = account
		self.db = db
		self.rules = []
		self.sub_rules = []
		reload_rules()
		

	def add_sub_rule(self, id, conn, arg1, arg2):
		self.sub_rules.append(rule(id,conn,arg1,arg2))

	def add_rule(self, id, conn, arg1, arg2):
		self.rules.append(rule(id,conn,arg1,arg2))

	def clear_rules(self):
		self.rules = []
		self.sub_rules = []
		
	def reload_rules(self):
		# clear all rules
		self.clear_rules()
		# load new sets from database
		db_rules=self.db.load_rules(self.area,self.account,0) 				# 0=rules, 1=sub_rules
		db_sub_rules=self.db.load_rules(self.area,self.account,1)	# 0=rules, 1=sub_rules
		# add them
		for r in db_rules:
			self.add_rule(r)
		for r in db_sub_rules:
			self.add_sub_rules(r)
		# print for debugging
		self.print_rules()
		return 0
		
	def print_rules(self):
		print("This is area "+self.area+" on account "+self.account+". I have "+str(len(self.rules)))+" active rules + "+str(len(self.sub_rules))+" subrules")
		i=1
		print("Rules:")
		for r in self.rules:
			print((str(i)+"/"+str(len(self.rules))+" conn: "+str(r.conn)+", arg1: "+str(r.arg1)+", arg2:"+str(r.arg2))
			i+=1
		i=1
		print("Sub-Rules:")
		for r in self.sub_rules:
			print((str(i)+"/"+str(len(self.sub_rules))+" conn: "+str(r.conn)+", arg1: "+str(r.arg1)+", arg2:"+str(r.arg2))
			i+=1
		
	def check_rules(self):
		for r in self.rules:
			if(self.eval_rule(r.connector, r.arg1, r.arg2,10))
				return 1
		return 0
		
	def get_sub_rule(self, rule_id):
		conn=""
		arg1=""
		arg2=""
		for sr in self.sub_rules:
			if(sr.id==rule_id):
				conn=sr.connector
				arg1=sr.arg1
				arg2=sr.arg2
		return (conn,arg1,arg2)

	def eval_rule(self,conn, arg1, arg2,depth):
		if(depth<0):
			return 0
			
		## AND sub rule based
		if(conn=="AND"):
			(conn_1,arg1_1,arg2_1) = self.get_sub_rule(arg1)
			(conn_2,arg1_2,arg2_2) = self.get_sub_rule(arg2)
			res_1=eval_rule(conn_1,arg1_1,arg2_1,depth-1)
			res_2=eval_rule(conn_2,arg1_2,arg2_2,depth-1)
			if(res_1 and res_2):
				return 1
		## AND  sub rule based
		
		## NOT sub rule based
		elif(conn=="NOT"):
			(conn_1,arg1_1,arg2_1) = self.get_sub_rule(arg1)
			res_1=eval_rule(conn_1,arg1_1,arg2_1,depth-1)
			if(not(res_1)):
				return 1
		## NOT sub rule based
		
		## catch all - always on
		elif(conn=="*"):
			return 1
		## catch all - always on
		
		## time based
		elif(conn=="time"):
			now=time.mktime(datetime.datetime.strptime(time.strftime("%H:%M:%S", time.time()),"%H:%M:%S").timetuple())
			if(int(arg2)>int(arg1)): # meaning the user defined in the rule something like between 06:00 and 18:00
				if(now>int(arg1) and now<int(arg2)):
					return 1
			elif(int(arg2)<int(arg1)): # meaning alert active between 18:00 and 06:00
				if (now>int(arg2) and now<(int(arg1)+86400)): 
					return 1
		## time based
		
		## week day based
		elif(conn=="day"):
			today=time.strftime("%w", time.time())
			condition=time.strftime("%w", int(arg1))
			if(today==condition):
				return 1
		## week day based
		
		## GEO location based
		elif(conn=="nobody_at_geo_area"):
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
		## GEO location based
		
		## WLAN location based
		elif(conn=="wlan_area"):
			wlan_area=arg1
			return 0
		## WLAN location based
		
		return 0
