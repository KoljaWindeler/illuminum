#!/bin/bash
locationOfScript=$(dirname "$(readlink -e "$0")")"/usbcam"

killall mjpg_streamer  > /dev/null 2>&1;

mkdir /dev/shm/mjpeg > /dev/null 2>&1;
mkdir /dev/shm/mjpeg/n > /dev/null 2>&1;

$locationOfScript/mjpg_streamer -i $locationOfScript"/input_uvc.so -f 4 -r 1280x720 -n  -quality 60"  -o $locationOfScript"/output_file.so -f /dev/shm/mjpeg/n -c $locationOfScript/m.sh"&
#./mjpg_streamer -i "./input_uvc.so -f 4 -r 1280x720 -n  -quality 75"  -o "./output_file.so -f /dev/shm/mjpeg/n -c ./m.sh"&
#./mjpg_streamer -i "./input_uvc.so -f 4 -r 640x480 -n  -quality 75"  -o "./output_file.so -f /dev/shm/mjpeg/n -c ./m.sh"&
