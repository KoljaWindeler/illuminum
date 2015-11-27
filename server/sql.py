import pymysql.cursors, time, p, sys
from sql_login import *

class sql:
	def __init__(self):
		self.connection=''
	#############################################################
	def connect(self):
		try:
			# Connect to the database
			self.connection = pymysql.connect(host='localhost',user='root',passwd=sql_login,db='alert',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
		except:
			print("exception on connect to sql database")
	#############################################################
	def connection_check(self):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT now()"
				cursor.execure(req)
				result = cursor.fetchall()
				self.close()
				return 0
		except:
			return -1
	#############################################################
	def load_rules(self,area,account,sub_rules):
		try:
			#print("try:")
			self.connect()
			with self.connection.cursor() as cursor:
				# Read a single record
				#print("gen req:")
				req = "SELECT `id`, `conn`, `arg1`, `arg2` FROM `rules` WHERE `area` ='"+str(area)+"' and `account` = '"+str(account)+"' and `sub_rule` = '"+str(sub_rules)+"'"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchall()
		except:
				result =-2
		self.close()
		return result
	#############################################################
	def append_rule(self,account,area,conn,arg1,arg2):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`rules` (`id`, `area`, `account`, `sub_rule`, `conn`, `arg1`, `arg2`) VALUES (NULL, '"+area+"', '"+account+"', '0', '"+str(conn)+"', '"+str(arg1)+"', '"+str(arg2)+"');"
				cursor.execute(req)
				self.connection.commit()
				
				req = "SELECT LAST_INSERT_ID();"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['LAST_INSERT_ID()']
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def rm_rule(self,id):
		try:
			self.connect()
			#print("try:")
			with self.connection.cursor() as cursor:
				# Read a single record
				#print("gen req:")
				req = "DELETE FROM `rules` WHERE `id` ='"+str(id)+"'"
				#print(req)
				cursor.execute(req)

			self.connection.commit()
			result =0
		except:
			result =-2
		self.close()
		return result
	#############################################################
	def get_ws_data(self,login):
		#print("get data mid:"+mid)
		try:
			self.connect()
			#print("try:")
			with self.connection.cursor() as cursor:
				# Read a single record
				#print("get_data gen req:")
				req = "SELECT COUNT(*) FROM ws WHERE login='"+str(login)+"'"
				cursor.execute(req)
				result = cursor.fetchone()
				#print(result)
				#print(result)
				if(result["COUNT(*)"]==1):
					req = "SELECT  pw, account, email FROM ws WHERE login='"+str(login)+"'"
					#print(req)
					cursor.execute(req)
					#print("setting result to ")
					result = cursor.fetchone()
				else:
					result=-1
					p.rint("count not 1, it is "+result["COUNT(*)"],"d")
					p.rint(req,"d")
				#print(result)
		except:
			p.rint("exception running self check","d")
			result = -2
		self.close()
		return result
	#############################################################
	def get_data(self,mid):
		try:
			self.connect()
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
					req = "SELECT  pw, area, account, alias, longitude, latitude, color_pos, brightness_pos, mRed, mGreen, mBlue, alarm_ws, alarm_while_streaming, frame_dist  FROM m2m WHERE mid="+str(mid)
					#print(req)
					cursor.execute(req)
					#print("setting result to ")
					result = cursor.fetchone()
				else:
					result=-1
					p.rint("count not 1","d")
					p.rint(req,"d")
				#print(result)
		except:
			p.rint("exception running self check","d")
			result = -2
		self.close()
		return result
	#############################################################
	def update_location(self,login,location):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `location` = '"+location+"' WHERE  `ws`.`login` = '"+login+"'"
				cursor.execute(req, )
				req = "INSERT INTO  `history` (`id` ,`timestamp` ,`user` ,`action`)VALUES (NULL,'"+str(int(time.time()))+"','"+login+"','"+location+"');"
				cursor.execute(req, )
			self.connection.commit()
			result=0
		except:
			result = -2
		self.close()
		return result
	#############################################################
	def update_color(self, m2m,r,g,b,brightness_pos,color_pos):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `mRed` =  "+str(r)+", `mGreen` =  "+str(g)+",`mBlue` =  "+str(b)+", `color_pos` =  "+str(color_pos)+", `brightness_pos` =  "+str(brightness_pos)+" WHERE  `m2m`.`mid` ="+m2m.mid
				cursor.execute(req, )
			self.connection.commit()
			result=0
		except:
			result=1
		self.close()
		return result
	#############################################################
	def update_det(self,login,account,area,state):
		try:
			self.connect()
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
		self.close()
		return result
	#############################################################
	def get_areas_state(self,account,area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT `updated`,`state` FROM  `area_state` WHERE  `account` = '"+str(account)+"' and `area`= '"+str(area)+"'"
				cursor.execute(req)
				result = cursor.fetchone()
		except:
			result = -1
		self.close()
		return result

	#############################################################
	def get_areas_for_account(self,account):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT distinct `area` FROM  `m2m` WHERE  `account` = '"+str(account)+"'"
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_state(self,area,account):
		try:
			self.connect()
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
					p.rint("Count!=1","d")
					p.rint(req,"d")
					return -1
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def user_count_on_area(self,account,area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM  `ws` WHERE  `account` = '"+str(account)+"' and `location` LIKE '%"+str(area)+"%'"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchone()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def user_on_area(self,account,area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT login FROM  `ws` WHERE  `account` = '"+str(account)+"' and `location` like '%"+str(area)+"%'"
				#print(req)
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def update_last_seen_m2m(self,mid,ip):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `last_seen` =  %s, `last_ip` = %s WHERE  `m2m`.`mid` =%s"
				cursor.execute(req, (str(time.time()), str(ip),str(mid)))
			
			self.connection.commit()
			result=0
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def update_last_seen_ws(self,login,ip):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `update` =  %s, `ip` = %s WHERE  `ws`.`login` =%s"
				cursor.execute(req, (str(time.time()), str(ip),str(login)))
				self.connection.commit()
			result=0
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def close(self):
		try:
			self.connection.close()
		except:
			pass
	#############################################################
	def get_m2m4account(self,account):
		req = "SELECT  `mid` ,  `area` ,  `last_seen` ,  `last_ip`, `alias`, `longitude`, `latitude`, `brightness_pos`, `color_pos` FROM  `m2m` WHERE  `account` =  '"+str(account)+"'"
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			p.rint("req:"+req,"d")
			p.rint(sys.exc_info()[0],"d")
			result = -1
		self.close()
		return result
	#############################################################
	def create_alert(self, m2m, rm_string):
		try:
			self.connect()
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
		self.close()
		return result
	############################################################# 
	def append_alert_photo(self, m2m, des_location):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`alert_pics` (`id`, `alert_id`, `path`,`ts`) VALUES (NULL, '"+str(m2m.alert.id)+"', '"+str(des_location)+"', '"+str(time.time())+"')"
				#print(req)
				cursor.execute(req)
				self.connection.commit()
				result = 0
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_open_alert_count(self, account,mid):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  COUNT(*) FROM  `alerts` WHERE  `account` =  '"+account+"' and `ack`=0 and `mid`='"+mid+"'"
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_closed_alert_count(self, account,mid):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  COUNT(*) FROM  `alerts` WHERE  `account` =  '"+account+"' and `ack`!=0 and `mid`='"+mid+"'"
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_open_alert_ids(self, account, mid, a,b):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `id` FROM  `alerts` WHERE  `account` =  '"+account+"' and `ack`=0 and `mid`='"+mid+"' ORDER BY `f_ts` DESC LIMIT "+str(a)+","+str(b)
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_closed_alert_ids(self, account, mid, a,b):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `id` FROM  `alerts` WHERE  `account` =  '"+account+"' and `ack`!=0 and `mid`='"+mid+"' ORDER BY `f_ts` DESC LIMIT "+str(a)+","+str(b)
				cursor.execute(req)
				result = cursor.fetchall()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_alert_details(self, account,alert_id):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `f_ts`,`mid`,`area`,`rm_string`,`ack`,`ack_ts`,`ack_by` FROM  `alerts` WHERE  `account` =  '"+str(account)+"' and `id`="+str(alert_id)
				#print(req)
				cursor.execute(req)
				result = cursor.fetchone()
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_img_count_for_alerts(self,alert_id):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM  `alert_pics` WHERE  `alert_id` ="+str(alert_id)
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_img_for_alerts(self, alert_id,century):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				if(int(century)>=0 and int(century)<100):
					req = "SELECT  `path` , `ts` FROM  `alert_pics` WHERE  `alert_id` ="+str(alert_id)+" ORDER BY `id` DESC LIMIT "+str(int(century)*10)+" , "+str((int(century)+1)*20)
					cursor.execute(req)
					result = cursor.fetchall()
					#print(req)
					#print(result)
				else:
					result = -1
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def get_account_for_path(self, path):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT `account` FROM `alerts` WHERE `id`=(SELECT `alert_id` FROM `alert_pics` WHERE `path`='"+path+"')"
				cursor.execute(req)
				result = cursor.fetchone()
				result=result['account']
		except:
			result = -1
		self.close()
		return result
	#############################################################
	def ack_alert(self,mid,aid,login):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`alerts` SET  `ack` =  '1',`ack_ts` =  '"+str(int(time.time()))+"',`ack_by` =  '"+login+"' WHERE  `id` ="+str(aid)+" and `mid`='"+str(mid)+"'";
				cursor.execute(req)
			self.connection.commit()
			result=0
		except:
			result = -1
			p.rint(sys.exc_info()[0],"d")
		self.close()
		return result
	#############################################################
	def ack_all_alert(self,mid,login):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`alerts` SET  `ack` =  '1',`ack_ts` =  '"+str(int(time.time()))+"',`ack_by` =  '"+login+"' WHERE  `ack`=0  and `mid`='"+str(mid)+"'";
				cursor.execute(req)
			self.connection.commit()
			result=0
		except:
			result = -1
			p.rint(sys.exc_info()[0],"d")
		self.close()
		return result

	
	#############################################################
	def register_m2m(self,mid,m2m_pw,account):
		ret=-1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "DELETE FROM  `alert`.`m2m`  WHERE  `mid`='"+str(mid)+"'";
				cursor.execute(req)
				req = "INSERT INTO `alert`.`m2m` (`mid`, `pw`, `area`, `account`, `alias`, `latitude`, `longitude`) VALUES ('"+str(mid)+"', '"+str(m2m_pw)+"', 'home', '"+str(account)+"', 'SecretCam','0.0','0.0');"
				cursor.execute(req)
			self.connection.commit()
			ret=0
		except:
			ret=-1

		return ret
