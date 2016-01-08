#!/bin/bash
locationOfScript=$(dirname "$(readlink -e "$0")")
export LD_LIBRARY_PATH=:/usr/local/lib:/usr/local/lib
$locationOfScript/illuminum_usbgpucam
