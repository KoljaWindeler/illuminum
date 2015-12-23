from sql import *
import os

db=sql()

directory="/tmp/illuminum/"
if not os.path.exists(directory):
	os.makedirs(directory)

pics = db.get_delete_pics()
m=0
for pic in pics:
	src="/home/ubuntu/python/illumino/uploads/"+str(pic['path'])
	dest=os.path.join(directory,str(pic['path']))
	print("move "+src+" to "+dest)
	try:
		os.rename(src,dest)
		m=m+1
	except:
		pass
print(str(m)+"/"+str(len(pics))+" pics found")
db.rem_delete_pics()
exit(0)
