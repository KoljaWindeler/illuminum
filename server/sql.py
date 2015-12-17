import pymysql.cursors, time, p, sys, traceback
from sql_login import *

class sql:
	def __init__(self):
		self.connection = ''
	#############################################################
	def he(self):
		p.err("sys:")
		p.err(str(sys.exc_info()[0]))
		p.err(str(sys.exc_info()[1]))
		p.err(str(repr(traceback.format_tb(sys.exc_info()[2]))))
		
	#############################################################
	def connect(self):
		try:
			# Connect to the database
			self.connection = pymysql.connect(host = 'localhost', user = 'root', passwd = sql_login, db = 'alert', charset = 'utf8mb4', cursorclass = pymysql.cursors.DictCursor)
		except:
			self.he()
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
			self.he()
			return -1
	#############################################################
	def load_rules(self, area, account, sub_rules):
		try:
			#rint("try:")
			self.connect()
			with self.connection.cursor() as cursor:
				# Read a single record
				#rint("gen req:")
				req = "SELECT `id`, `conn`, `arg1`, `arg2` FROM `rules` WHERE `area` =%s and `account` = %s and `sub_rule` = %s"
				#rint(req)
				cursor.execute(req, (str(area), str(account), str(sub_rules)) )
				result = cursor.fetchall()
		except:
			self.he()
			result = -2
		self.close()
		return result
	#############################################################
	def append_rule(self, account, area, conn, arg1, arg2):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`rules` (`id`, `area`, `account`, `sub_rule`, `conn`, `arg1`, `arg2`) VALUES (NULL, %s, %s, '0', %s, %s, %s)"
				cursor.execute(req, (area, account, str(conn), str(arg1), str(arg2)) )
				self.connection.commit()
				
				req = "SELECT LAST_INSERT_ID()"
				#rint(req)
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['LAST_INSERT_ID()']
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def rm_rule(self, id):
		try:
			self.connect()
			#rint("try:")
			with self.connection.cursor() as cursor:
				# Read a single record
				#rint("gen req:")
				req = "DELETE FROM `rules` WHERE `id` =%s"
				#rint(req)
				cursor.execute(req, str(id))

			self.connection.commit()
			result = 0
		except:
			self.he()
			result = -2
		self.close()
		return result
	#############################################################
	def get_ws_data(self, login):
		#rint("get data mid:"+mid)
		try:
			self.connect()
			#rint("try:")
			with self.connection.cursor() as cursor:
				# Read a single record
				#rint("get_data gen req:")
				req = "SELECT COUNT(*) FROM ws WHERE login=%s"
				cursor.execute(req, str(login))
				result = cursor.fetchone()
				#rint(result)
				#rint(result)
				if(result["COUNT(*)"] == 1):
					req = "SELECT  pw, account, email FROM ws WHERE login=%s"
					#rint(req)
					cursor.execute(req, str(login))
					#rint("setting result to ")
					result = cursor.fetchone()
				else:
					result = -1
					p.rint("count not 1, it is "+result["COUNT(*)"], "d")
					p.rint(req, "d")
				#rint(result)
		except:
			self.he()
			result = -2
		self.close()
		return result
	#############################################################
	def get_data(self, mid):
		try:
			self.connect()
			#rint("try:")
			with self.connection.cursor() as cursor:
				# Read a single record
				#rint("get_data gen req:")
				req = "SELECT COUNT(*) FROM m2m WHERE mid= %s"
				cursor.execute(req, str(mid))
				result = cursor.fetchone()
				#rint(result)
				#rint(result)
				if(result["COUNT(*)"] == 1):
					req = "SELECT  pw, area, account, alias, color_pos, brightness_pos, mRed, mGreen, mBlue, alarm_ws, alarm_while_streaming, frame_dist, resolution  FROM m2m WHERE mid= %s"
					cursor.execute(req, str(mid))
					result = cursor.fetchone()

					# area is just an id, lets replace it with a name and som location data
					req2 = "SELECT  area, longitude, latitude FROM area_state WHERE id= %s"
					cursor.execute(req2, str(result["area"]))
					result2 = cursor.fetchone()
					
					result["area_id"]=result["area"]
					result["latitude"]=result2["latitude"]
					result["longitude"]=result2["longitude"]
					result["area"]=result2["area"]
					
				else:
					result = -1
					p.err("SQL get data for ->%s<- did not return 1 line but %s"%(str(mid),str(result["COUNT(*)"])))
					p.err(req)
				#rint(result)
		except:
			self.he()
			result = -2
		self.close()
		return result
	#############################################################
	def update_location(self, login, location):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `location` = %s WHERE  `ws`.`login` = %s"
				cursor.execute(req, (location,login))
				req = "INSERT INTO  `history` (`id` ,`timestamp` ,`user` ,`action`)VALUES (NULL,'"+str(int(time.time()))+"',%s,%s)"
				cursor.execute(req, (login,location))
			self.connection.commit()
			result = 0
		except:
			self.he()
			result = -2
		self.close()
		return result
	#############################################################
	def update_color(self, m2m, r, g, b, brightness_pos, color_pos):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `mRed` =  %s, `mGreen` =  %s,`mBlue` =  %s, `color_pos` =  %s, `brightness_pos` =  %s WHERE  `m2m`.`mid` = %s"
				cursor.execute(req, (str(r), str(g), str(b), str(color_pos), str(brightness_pos), str(m2m.mid)) )
			self.connection.commit()
			result = 0
		except:
			self.he()
			result = 1
		self.close()
		return result
	#############################################################
	def update_det(self, login, account, area, state):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM area_state WHERE `account` = %s AND `area`=%s"
				cursor.execute(req, (str(account), str(area)) )
				result = cursor.fetchone()
				#rint(result)
				if(result["COUNT(*)"] == 1):
					req = "UPDATE  `area_state` SET  `state` = %s, `login` = %s, `updated` = '"+str(int(time.time()))+"'  WHERE  `account` = %s AND `area` = %s"
					#rint(req)
					cursor.execute(req, (str(state), str(login), str(account), str(area)) )
					self.connection.commit()
					result = 0
				elif(result["COUNT(*)"] == 0):
					req = "INSERT INTO  `area_state` (`id` ,`area` ,`account` ,`state` ,`updated` ,`login`) VALUES (NULL,%s,%s,%s,'"+str(int(time.time()))+"',%s)"
					#rint(req)
					cursor.execute(req, (str(area), str(account), str(state), str(login)) )
					self.connection.commit()
					result = 0
				else: 
					result = -1
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_areas_state(self, account, area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM area_state WHERE `account` = %s AND `area`=%s"
				cursor.execute(req, (str(account), str(area)) )
				result = cursor.fetchone()
				#rint(result)
				if(result["COUNT(*)"] == 0):
					req = "INSERT INTO  `area_state` (`id` ,`area` ,`account` ,`state` ,`updated` ,`login`) VALUES (NULL,%s,%s,'0','"+str(int(time.time()))+"','create')"
					#rint(req)
					cursor.execute(req, (str(area), str(account)) )
					self.connection.commit()
					result = 0

				# Create a new record
				req = "SELECT `updated`,`state` FROM  `area_state` WHERE  `account` = %s and `area`= %s"
				cursor.execute(req, (str(account), str(area)) )
				result = cursor.fetchone()
		except:
			self.he()
			result = -1
		self.close()
		return result

	#############################################################
	def get_areas_for_account(self, account):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req2 = "SELECT distinct `area`, `id`, `latitude`, `longitude` FROM  `area_state` WHERE  `account` = %s"
				cursor.execute(req2, str(account))
				result = cursor.fetchall()
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_state(self, area, account):
		if(area=="" or account==""):
			p.err("get_state was callen with area and or account empty")
			return -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM area_state WHERE `account` = %s AND `area`=%s"
				cursor.execute(req, (str(account), str(area)) )
				result = cursor.fetchone()
				#rint(result)
				if(result["COUNT(*)"] == 1):
					req = "SELECT `state` FROM  `area_state` WHERE  `account` = %s AND `area`=%s"
					cursor.execute(req, (str(account), str(area)) )
					result = cursor.fetchone()
				else: 
					p.rint("get state Count was "+str(result["COUNT(*)"])+"!=1", "d")
					p.rint(req%(str(account), str(area)), "d")
					result = -1
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def user_count_on_area(self, account, area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM  `ws` WHERE  `account` = %s and `location` LIKE %s" 
				#rint(req)
				cursor.execute(req, (str(account), "%"+str(area)+"%"))
				result = cursor.fetchone()
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def user_on_area(self, account, area):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT login FROM  `ws` WHERE  `account` = %s and `location` like %s"
				#rint(req)
				cursor.execute(req, (str(account), "%"+str(area)+"%"))
				result = cursor.fetchall()
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def update_last_seen_m2m(self, mid, ip):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `m2m` SET  `last_seen` =  %s, `last_ip` = %s WHERE  `m2m`.`mid` =%s"
				cursor.execute(req, (str(time.time()), str(ip), str(mid)))
			
			self.connection.commit()
			result = 0
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def update_last_seen_ws(self, login, ip):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "UPDATE  `ws` SET  `update` =  %s, `ip` = %s WHERE  `ws`.`login` =%s"
				cursor.execute(req, (str(time.time()), str(ip), str(login)))
				self.connection.commit()
			result = 0
		except:
			self.he()
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
	def get_m2m4account(self, account):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT  * FROM  `m2m` WHERE `account` =  %s"
				# Create a new record
				cursor.execute(req, str(account))
				result = cursor.fetchall()

				# avoid showning the PW
				for r in result:
					r.pop("pw")

					# area is just an id, lets replace it with a name and som location data
					req2 = "SELECT  area, longitude, latitude FROM area_state WHERE id= %s"
					cursor.execute(req2, str(r["area"]))
					result2 = cursor.fetchone()
				
					r["latitude"]=result2["latitude"]
					r["longitude"]=result2["longitude"]
					r["area"]=result2["area"]

		except:
			self.he()
			result = -1
		self.close()
		return result

	#############################################################
	def get_logins4account(self, account):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT  * FROM  `ws` WHERE `account` =  %s"
				# Create a new record
				cursor.execute(req, str(account))
				result = cursor.fetchall()

				# avoid showning the PW
				for r in result:
					r.pop("pw")
					r.pop("location")
					r.pop("update")
					r.pop("ip")
					r.pop("account")
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def create_alert(self, m2m, rm_string):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`alerts` (`id`, `f_ts`, `mid`, `area`, `account`, `rm_string`, `ack`, `ack_ts`, `ack_by`) VALUES (NULL, %s, %s, %s, %s, %s, '0', '0', '')"
				cursor.execute(req, (str(time.time()), str(m2m.mid), str(m2m.area), str(m2m.account), str(rm_string)) )
				self.connection.commit()
				
				req = "SELECT LAST_INSERT_ID()"
				#rint(req)
				cursor.execute(req)
				result = cursor.fetchone()
				result = result['LAST_INSERT_ID()']
		except:
			self.he()
			result = -1

		self.close()
		return result
	############################################################# 
	def append_alert_photo(self, m2m, des_location):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "INSERT INTO `alert`.`alert_pics` (`id`, `alert_id`, `path`,`ts`) VALUES (NULL, %s, %s, '"+str(time.time())+"')"
				#rint(req)
				cursor.execute(req, (str(m2m.alert.id),str(des_location)) )
				self.connection.commit()
				result = 0
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_open_alert_count(self, account, mid):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  COUNT(*) FROM  `alerts` WHERE  `account` =  %s and `ack`=0 and `mid`=%s and (`del_by`='' or `del_by` is NULL)"
				cursor.execute(req, (str(account), str(mid)) )
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_closed_alert_count(self, account, mid):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  COUNT(*) FROM  `alerts` WHERE  `account` =  %s and `ack`!=0 and `mid`=%s and (`del_by`='' or `del_by` is NULL)"
				cursor.execute(req, (str(account), str(mid)) )
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_open_alert_ids(self, account, mid, a, b):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `id` FROM  `alerts` WHERE  `account` =  %s and `ack`=0 and `mid`=%s  and (`del_by`='' or `del_by` is NULL) ORDER BY `f_ts` DESC LIMIT "+str(a)+","+str(b)
				cursor.execute(req, (str(account), str(mid)) )
				result = cursor.fetchall()
		except:
			result = -1
			self.he()
		self.close()
		return result
	#############################################################
	def get_closed_alert_ids(self, account, mid, a, b):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `id` FROM  `alerts` WHERE  `account` =  %s and `ack`!=0 and `mid`=%s  and (`del_by`='' or `del_by` is NULL) ORDER BY `f_ts` DESC LIMIT "+str(a)+", "+str(b)
				cursor.execute(req, (str(account), str(mid)) )
				result = cursor.fetchall()
		except:
			result = -1
			self.he()
		self.close()
		return result
	#############################################################
	def get_alert_details(self, account, alert_id):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `f_ts`,`mid`,`area`,`rm_string`,`ack`,`ack_ts`,`ack_by` FROM  `alerts` WHERE  `account` =  %s and `id`=%s  and (`del_by`='' or `del_by` is NULL)"
				#rint(req)
				cursor.execute(req, (str(account), str(alert_id)) )
				result = cursor.fetchone()
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_img_count_for_alerts(self, alert_id):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT COUNT(*) FROM  `alert_pics` WHERE  `alert_id` =%s"
				cursor.execute(req, str(alert_id))
				result = cursor.fetchone()
				result = result['COUNT(*)']
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_img_for_alerts(self, alert_id, century):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# Create a new record
				if(int(century) >= 0 and int(century) < 100):
					req = "SELECT  `path` , `ts` FROM  `alert_pics` WHERE  `alert_id` =%s ORDER BY `id` DESC LIMIT "+str(int(century)*10)+", "+str((int(century)+1)*20)
					cursor.execute(req, (str(alert_id)) )
					result = cursor.fetchall()
					#rint(req)
					#rint(result)
				else:
					result = -1
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def get_account_for_path(self, path):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT `account` FROM `alerts` WHERE `id`=(SELECT `alert_id` FROM `alert_pics` WHERE `path`=%s)"
				cursor.execute(req, str(path))
				result = cursor.fetchone()
				result=result['account']
		except:
			self.he()
			result = -1
		self.close()
		return result
	#############################################################
	def ack_alert(self, mid, aid, login):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`alerts` SET  `ack` =  '1',`ack_ts` =  '"+str(int(time.time()))+"',`ack_by` =  %s WHERE  `id` =%s and `mid`=%s"
				cursor.execute(req, (str(login), str(aid), str(mid)) )
			self.connection.commit()
			result = 0
		except:
			result = -1
			self.he()
		self.close()
		return result
	#############################################################
	def del_alert(self, mid, aid, login):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`alerts` SET  `del_by` =  %s WHERE  `id` =%s and `mid`=%s"
				print(req%(str(login), str(aid), str(mid)))
				cursor.execute(req, (str(login), str(aid), str(mid)) )
			self.connection.commit()
			result = 0
		except:
			result = -1
			self.he()
		self.close()
		return result
	#############################################################
	def ack_all_alert(self, mid, login):
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`alerts` SET  `ack` =  '1',`ack_ts` =  '"+str(int(time.time()))+"',`ack_by` =  %s WHERE  `ack`=0  and `mid`=%s"
				cursor.execute(req, (str(login), str(mid)))
			self.connection.commit()
			result = 0
		except:
			result = -1
			self.he()
		self.close()
		return result

	
	#############################################################
	def register_m2m(self, mid, m2m_pw, account, alias):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				# delete old entries for cam
				req = "DELETE FROM  `alert`.`m2m`  WHERE  `mid`=%s"
				cursor.execute(req, str(mid))
				# get area cound for cam
				req = "SELECT `id` FROM `alert`.`area_state` WHERE `account`=%s ORDER BY `id` ASC"
				cursor.execute(req, str(account))				
				if(cursor.rowcount == 0):
					# oh oh, user doesn't have an area
					req = "INSERT INTO `alert`.`area_state` (`area`, `account`, `login`) VALUES ('home', %s,  'create');"
					cursor.execute(req, (str(account),) )
					#rint(req)
					req = "SELECT LAST_INSERT_ID()"
					cursor.execute(req)
					result = cursor.fetchone()
					area = result['LAST_INSERT_ID()']
				else:
					result = cursor.fetchone()
					area = result['id']


				req = "INSERT INTO `alert`.`m2m` (`mid`, `pw`, `area`, `account`, `alias`) VALUES (%s, %s, %s, %s, %s)"
				cursor.execute(req, (str(mid), str(m2m_pw), str(area), str(account), str(alias)) )
			self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1

		return ret

	#############################################################
	def register_ws(self, login, pw, email):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT COUNT(*) FROM  `alert`.`ws`  WHERE  `login`=%s"
				cursor.execute(req, str(login))
				result = cursor.fetchone()
				result = result['COUNT(*)']
				if(result>0):
					ret = -2 # user already existed
				else:
					account_prefix = "acc"
					account_counter = 1
					result = 1
					while(result > 0):
						account_counter = account_counter + 1
						account_full = account_prefix + str(account_counter)
						req = "SELECT COUNT(*) FROM  `alert`.`ws`  WHERE  `account`=%s"
						cursor.execute(req, str(account_full))
						result = cursor.fetchone()
						result = result['COUNT(*)']

					# final step ... insert the data
					req = "INSERT INTO  `alert`.`ws` (`id`,`login`,`pw`,`location`,`update`,`ip`,`account`,`email`) VALUES "
					req += "(NULL , %s, %s,  '',  '1',  '', %s,  %s)"
					cursor.execute(req, (str(login), str(pw), str(account_full), str(email)) )
					
					self.connection.commit()
					ret = 0
		except:
			self.he()
			ret = -1

		return ret
	#############################################################
	def update_cam_parameter(self, mid, frame_space, resolution, alarm_while_stream, area, alarm_ws, name):
		ret = -1
		try:
			if(float(frame_space)>0):
				# translate
				if(alarm_while_stream=="no_alarm"):
					alarm_while_stream=0
				else:
					alarm_while_stream=1

				self.connect()
				with self.connection.cursor() as cursor:
					req = "UPDATE  `alert`.`m2m` SET  `frame_dist` =  %s, `alarm_ws` =  %s, `alarm_while_streaming` =  %s, `resolution` = %s, `area` = %s, `alias` = %s  WHERE  `m2m`.`mid` = %s"
					#rint("UPDATE  `alert`.`m2m` SET  `frame_dist` =  %s, `alarm_ws` =  %s, `alarm_while_streaming` =  %s, `resolution` = %s  WHERE  `m2m`.`mid` = %s" % (str(frame_space), str(alarm_ws), str(alarm_while_stream), str(resolution), str(mid)))
					cursor.execute(req, (str(frame_space), str(alarm_ws), str(alarm_while_stream), str(resolution), str(area), str(name), str(mid)) )
					self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1

		return ret
	#############################################################
	def update_area(self, id, name, latitude, longitude, account):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT COUNT(*) FROM  `alert`.`area_state`  WHERE  `id`=%s"
				cursor.execute(req, str(id))
				result = cursor.fetchone()
				result = result['COUNT(*)']
				if(result>0):
					req = "UPDATE  `alert`.`area_state` SET  `area` =  %s, `latitude` =  %s, `longitude` =  %s WHERE  `id` = %s"
					cursor.execute(req, (str(name), str(latitude), str(longitude), str(id)) )
				else:
					req = "INSERT INTO  `area_state` (`area` ,`account`, `latitude`, `longitude` ,`login`) VALUES (%s, %s, %s, %s, 'create')"
					print(req %  (str(name), str(account), str(latitude), str(longitude)) )
					cursor.execute(req, (str(name), str(account), str(latitude), str(longitude)) )
				self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1

		return ret
	#############################################################
	def update_login(self, id, name, pw, email, account):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "SELECT COUNT(*) FROM  `alert`.`ws`  WHERE  `id`=%s"
				cursor.execute(req, str(id))
				result = cursor.fetchone()
				result = result['COUNT(*)']
				if(result>0):
					req = "UPDATE  `alert`.`ws` SET  `pw` =  %s, `login` = %s, `email` = %s  WHERE  `id` = %s and `account` = %s"
					print(req % (str(pw), str(name), str(email), str(id), str(account)) )
					cursor.execute(req, (str(pw), str(name), str(email), str(id), str(account)) )
					ret = 0
				else:
					# is the user name taken
					req = "SELECT COUNT(*) FROM  `alert`.`ws`  WHERE  `login`=%s"
					cursor.execute(req, str(name))
					result = cursor.fetchone()
					result = result['COUNT(*)']

					if(result == 0):
						req = "INSERT INTO  `ws` (`login` ,`pw`, `email`, `account`) VALUES (%s, %s, %s, %s)"
						cursor.execute(req, (str(name), str(pw), str(email), str(account)) )
						ret = 0
					else:
						ret = -2
				self.connection.commit()
		except:
			self.he()
			ret = -1

		return ret
	#############################################################
	def remove_area(self, id):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "DELETE FROM `area_state` WHERE `id`=%s"
				cursor.execute(req, (str(id),) )
				self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1

		return ret
	#############################################################
	def remove_login(self, id, account):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "DELETE FROM `ws` WHERE `id`=%s and `account`=%s"
				cursor.execute(req, (str(id),str(account)) )
				self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1
		return ret
	
	#############################################################
	def update_m2m_version(self, mid, v_short, v_hash):
		ret = -1
		try:
			self.connect()
			with self.connection.cursor() as cursor:
				req = "UPDATE  `alert`.`m2m` SET  `v_short` =  %s, `v_hash` =  %s WHERE  `m2m`.`mid` = %s"
				cursor.execute(req, (str(v_short), str(v_hash), str(mid)) )
				self.connection.commit()
			ret = 0
		except:
			self.he()
			ret = -1

		return ret
		
