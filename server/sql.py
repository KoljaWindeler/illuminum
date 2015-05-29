import pymysql.cursors, time

class sql:
	def __init__(self):
		self.connection=''
		#print("init done")
	#############################################################
	def connect(self):
		# Connect to the database
		self.connection = pymysql.connect(host='localhost',user='root',passwd='123',db='alert',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
		#print("connect done")
	#############################################################
	def connection_check(self):
		try:
			#print("try:")
			with self.connection.cursor() as cursor:
				req = "SELECT now()"
				cursor.execure(req)
				result = cursor.fetchall()
				return 0
		except:
			return -1
	#############################################################
	def load_rules(self,area,account,sub_rules):
		#print("get data mid:"+mid)
		if(self.connection==''):
			print("sql has to be called with connect() first")
			result = -1
		else:
			#print("connection existing")
			try:
				#print("try:")
				with self.connection.cursor() as cursor:
					# Read a single record
					#print("gen req:")
					req = "SELECT `id`, `conn`, `arg1`, `arg2` FROM `rules` WHERE `area` ='"+str(area)+"' and `account` = '"+str(account)+"' and `sub_rule` = '"+str(sub_rules)+"'"
					#print(req)
					cursor.execute(req)
					result = cursor.fetchall()
			except:
				if(self.connection_check()==0):
					print("failed to load rules") # failure based on the command, connection ok
					result =-2
				else:
					self.connection=""
					self.connect()
					return self.load_rules(area,account,sub_rules)
		return result
	#############################################################
	def rm_rule(self,id):
		#print("get data mid:"+mid)
		if(self.connection==''):
			print("sql has to be called with connect() first")
			result = -1
		else:
			#print("connection existing")
			try:
				#print("try:")
				with self.connection.cursor() as cursor:
					# Read a single record
					#print("gen req:")
					req = "DELETE FROM `rules` WHERE `id` ='"+str(id)+"'"
					#print(req)
					cursor.execute(req)
					result =0
			except:
				if(self.connection_check()==0):
					print("failed to delete rule") # failure based on the command, connection ok
					result =-2
				else:
					self.connection=""
					self.connect()
					return self.rm_rule(id)
		return result
	#############################################################
	def get_data(self,mid):
		#print("get data mid:"+mid)
		if(self.connection==''):
			print("sql has to be called with connect() first")
			result = -1
		else:
			#print("connection existing")
			try:
				#print("try:")
				with self.connection.cursor() as cursor:
					# Read a single record
					#print("get_data gen req:")
					req = "SELECT COUNT(*) FROM m2m WHERE mid="+str(mid)
					cursor.execute(req)
					result = cursor.fetchone()
					#print(result)
					#print(result)
					if(result["COUNT(*)"]==1):
						req = "SELECT  pw, area, account, alias, longitude, latitude, color_pos, brightness_pos, mRed, mGreen, mBlue FROM m2m WHERE mid="+str(mid)
						#print(req)
						cursor.execute(req)
						#print("setting result to ")
						result = cursor.fetchone()
					else:
						result=-1
						print("count not 1")
						print(req)
						exit()
					#print(result)
			except:
				print("exception running self check")
				if(self.connection_check()==0):
					result = -2
					print("cobnectuon checjlh ==0")
					exit()
				else:
					print("self check return NOT 0")
					self.connection=""
					self.connect()
					result=self.get_data(mid)
				#print("failed!")
		return result
	#############################################################
	def update_location(self,login,location):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `location` = '"+location+"' WHERE  `ws`.`login` = '"+login+"'"
				cursor.execute(req, )
				req = "INSERT INTO  `history` (`id` ,`timestamp` ,`user` ,`action`)VALUES (NULL,'"+str(int(time.time()))+"','"+login+"','"+location+"');"
				cursor.execute(req, )
			self.connection.commit()
			result=0
		except:
			if(self.connection_check()==0):
				result = -2
			else:
				self.connection=""
				self.connect()
				result=self.update_location(login,location)
		return result
	#############################################################
	def update_color(self, m2m,r,g,b,brightness_pos,color_pos):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `mRed` =  "+str(r)+", `mGreen` =  "+str(g)+",`mBlue` =  "+str(b)+", `color_pos` =  "+str(color_pos)+", `brightness_pos` =  "+str(brightness_pos)+" WHERE  `m2m`.`mid` ="+m2m.mid
				cursor.execute(req, )
			self.connection.commit()
			result=0
		except:
			result=1
		return result
	#############################################################
	def update_det(self,login,account,area,state):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM area_state WHERE `account` = '"+str(account)+"' AND `area`='"+str(area)+"'"
				cursor.execute(req)
				result = cursor.fetchone()
				#print(result)
				if(result["COUNT(*)"]==1):
					req = "UPDATE  `area_state` SET  `state` = '"+str(state)+"', `login` = '"+str(login)+"', `updated` = '"+str(int(time.time()))+"'  WHERE  `account` = '"+account+"' AND `area` = '"+area+"'"
					#print(req)
					cursor.execute(req, )
					self.connection.commit()
					result=0
				elif(result["COUNT(*)"]==0):
					req = "INSERT INTO  `area_state` (`id` ,`area` ,`account` ,`state` ,`updated` ,`login`) VALUES (NULL,'"+str(area)+"','"+str(account)+"','"+str(state)+"','"+str(int(time.time()))+"','"+str(login)+"');"
					#print(req)
					cursor.execute(req, )
					self.connection.commit()
					result=0
				else: 
					result = -1
		except:
			result = -1
		return result
	#############################################################
	def get_areas_for_account(self,account):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT distinct `area` FROM  `m2m` WHERE  `account` = '"+str(account)+"'"
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		return result
	#############################################################
	def get_state(self,area,account):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM area_state WHERE `account` = '"+str(account)+"' AND `area`='"+str(area)+"'"
				cursor.execute(req)
				result = cursor.fetchone()
				#print(result)
				if(result["COUNT(*)"]==1):
					req = "SELECT `state` FROM  `area_state` WHERE  `account` = '"+str(account)+"' AND `area`='"+str(area)+"'"
					cursor.execute(req)
					result = cursor.fetchone()
				else: 
					return -1
		except:
			result = -1
		return result
	#############################################################
	def user_count_on_area(self,account,area):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM  `ws` WHERE  `account` = '"+str(account)+"' and `location` = '"+str(area)+"'"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchone()
		except:
			result = -1
		return result
	#############################################################
	def user_on_area(self,account,area):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT login FROM  `ws` WHERE  `account` = '"+str(account)+"' and `location` = '"+str(area)+"'"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		return result
	#############################################################
	def update_last_seen_m2m(self,mid,ip):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `last_seen` =  %s, `last_ip` = %s WHERE  `m2m`.`mid` =%s"
				cursor.execute(req, (str(time.time()), str(ip),str(mid)))
			
			self.connection.commit()
			result=0
		except:
			result = -1
		return result
	#############################################################
	def update_last_seen_ws(self,login,ip):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `update` =  %s, `ip` = %s WHERE  `ws`.`login` =%s"
				cursor.execute(req, (str(time.time()), str(ip),str(login)))
				self.connection.commit()
			result=0
		except:
			result = -1
		return result
	#############################################################
	def close(self):
		self.connection.close()
	#############################################################
	def get_m2m4account(self,account):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `mid` ,  `area` ,  `last_seen` ,  `last_ip`, `alias`, `longitude`, `latitude`, `brightness_pos`, `color_pos` FROM  `m2m` WHERE  `account` =  %s"
				cursor.execute(req, (str(account)))
				result = cursor.fetchall()
		except:
			result = -1
		return result
	#############################################################
	def create_alert(self, m2m, rm_string):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`alerts` (`id`, `f_ts`, `mid`, `area`, `account`, `rm_string`, `ack`, `ack_ts`, `ack_by`) VALUES (NULL, '"+str(time.time())+"', '"+str(m2m.mid)+"', '"+str(m2m.area)+"', '"+str(m2m.account)+"', '"+str(rm_string)+"', '0', '0', '')"
				cursor.execute(req)
				self.connection.commit()
				
				req = "SELECT LAST_INSERT_ID();"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['LAST_INSERT_ID()']
		except:
			result = -1
		return result
	############################################################# 
	def append_alert_photo(self, m2m, des_location):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`alert_pics` (`id`, `alert_id`, `path`,`ts`) VALUES (NULL, '"+str(m2m.alert.id)+"', '"+str(des_location)+"', '"+str(time.time())+"')"
				print(req)
				cursor.execute(req)
				self.connection.commit()
				result = 0
		except:
			result = -1
		return result
		