#!/bin/bash
locationOfScript=$(dirname "$(readlink -e "$0")")

killall illuminum_usbgpucam  > /dev/null 2>&1;

mkdir /dev/shm/mjpeg > /dev/null 2>&1;

export LD_LIBRARY_PATH=:/usr/local/lib:/usr/local/lib
$locationOfScript/usbgpucam/illuminum_usbgpucam
