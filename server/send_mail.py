import smtplib, os

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
import threading
import time

CONST_DEBUG=0

def send( subject, text, files=[], send_to="KKoolljjaa@gmail.com",send_from="koljasspam493@gmail.com", server="localhost"):
	#print("setting sendmail to 1")
	threading.Thread(target = send_now, args = (subject,text,files,send_to,send_from,server)).start()

def send_now( subject, text, files=[], send_to="KKoolljjaa@gmail.com",send_from="koljasspam493@gmail.com", server="localhost"):
	#print("virtually send a mail")
	#return 0
	#assert isinstance(send_to, list)
	#assert isinstance(files, list)
	#print("send now")
	msg = MIMEMultipart()
	msg['From'] = send_from
	msg['To'] =  COMMASPACE.join(send_to)
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject
	
	msg.attach( MIMEText(text) )
	
	for f in files:
		part = MIMEBase('application', "octet-stream")
		fo=open(f,"rb").read()
		part.set_payload(fo)
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
		msg.attach(part)

	if CONST_DEBUG:
		print("--> Connecting...")	
	smtp = smtplib.SMTP('smtp.gmail.com',587)
	smtp.ehlo()
	smtp.starttls()
	smtp.ehlo()

	if CONST_DEBUG:
		print("--> Login...")
	smtp.login("koljasspam493", "raspberrypi")

	if CONST_DEBUG:
		print("--> Sending...")
	smtp.sendmail(send_from, send_to, msg.as_string())

	if CONST_DEBUG:
		print("--> Done")
	smtp.close()
	if CONST_DEBUG:
		print("[A_E   "+time.strftime("%H:%M:%S")+"] Email send")
	return 0
