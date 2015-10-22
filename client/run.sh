screen -S "mylittlescreen" -d -m
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/client/start_cam.sh&\n'
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/client/start_python.sh&\n'

