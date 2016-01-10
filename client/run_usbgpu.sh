locationOfScript=$(dirname "$(readlink -e "$0")")

screen -S "mylittlescreen" -d -m
screen -r "mylittlescreen" -X stuff $locationOfScript'/start_usbgpucam.sh&\n'
screen -r "mylittlescreen" -X stuff $locationOfScript'/start_python.sh\n'
