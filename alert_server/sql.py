import pymysql.cursors, time

class sql:
	def __init__(self):
		self.connection=''
		#print("init done")

	def connect(self):
		# Connect to the database
		self.connection = pymysql.connect(host='localhost',user='root',passwd='123',db='alert',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
		#print("connect done")

	def get_data(self,mid):
		if(self.connection==''):
			print("sql has to be called with connect() first")
			result = -1
		else:
			try:
				with self.connection.cursor() as cursor:
					# Read a single record
					req = "SELECT  `pw`, `area`, `account` FROM `m2m` WHERE `mid`=%s"
					#print(sql)
					cursor.execute(req, (str(mid)))
					result = cursor.fetchone()
			except:
				result = -1
		return result

	def update_last_seen(self,mid,ip):
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

	def close(self):
		self.connection.close()


	def get_m2m4account(self,account):
		try:
			with self.connection.cursor() as cursor:
				# Create a new record
				req = "SELECT  `mid` ,  `area` ,  `last_seen` ,  `last_ip` FROM  `m2m` WHERE  `account` =  %s"
				cursor.execute(req, (str(account)))
				result = cursor.fetchall()
		except:
			result = -1
