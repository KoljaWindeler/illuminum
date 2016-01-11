#!/bin/bash
locationOfScript=$(dirname "$(readlink -e "$0")")

killall illuminum_usbgpucam  > /dev/null 2>&1;
mkdir /dev/shm/mjpeg > /dev/null 2>&1;
export LD_LIBRARY_PATH=:/usr/local/lib:/usr/local/lib

$locationOfScript/usbneoncam/illuminum_usbneoncam -W 1280 -H 720 -F 7.5
