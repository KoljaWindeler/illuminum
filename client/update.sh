#!/bin/bash
pushd `dirname $0` > /dev/null
DIR=`pwd -P`
popd > /dev/null

cd python
rw > dev/null &2>1; #will fail on all "non-kolja" raspberrys .. but thats ok
echo "====================================================="
echo "=============== 1. Updating ========================="
echo "====================================================="
git pull

echo "====================================================="
echo "=============== 2. Rebooting ========================"
echo "====================================================="
reboot
