screen -S "mylittlescreen" -d -m
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/gpucam/client/prepare.sh&\n'
screen -r "mylittlescreen" -X stuff '/home/pi/python/illumino/gpucam/client/run.sh\n'
