#!/bin/bash
mount -o remount,rw / > /dev/null &2>1; #will fail on all "non-kolja" raspberrys .. but thats ok

pushd `dirname $0` > /dev/null
DIR=`pwd -P`
popd > /dev/null

cd $DIR/python
sudo -u pi git pull
