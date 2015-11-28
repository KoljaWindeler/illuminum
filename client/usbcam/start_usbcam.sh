#!/bin/bash

mkdir /dev/shm/mjpeg > /dev/null 2>&1;
mkdir /dev/shm/mjpeg/n > /dev/null 2>&1;

./mjpg_streamer -i "./input_uvc.so -f 4 -r 1280x720 -n -y -quality 75"  -o "./output_file.so -f /dev/shm/mjpeg/n -c ./m.sh"&
