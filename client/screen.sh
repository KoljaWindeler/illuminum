screen -S "mylittlescreen" -d -m
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/client/prepare.sh\n'
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/client/run.sh\n'
