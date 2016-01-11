locationOfScript=$(dirname "$(readlink -e "$0")")

screen -S "illuminum_cam" -d -m
screen -r "illuminum_cam" -X stuff $locationOfScript'/start_usbneoncam.sh&\n'
screen -S "illuminum_python" -d -m
screen -r "illuminum_python" -X stuff $locationOfScript'/start_python.sh\n'
