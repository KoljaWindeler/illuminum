#!/bin/bash

echo "====================================================="
echo "=============== 1. Updating ========================="
echo "====================================================="
aptitude update


echo "====================================================="
echo "========= 2. Installing required packages ==========="
echo "====================================================="
aptitude install screen build-essential python3-dev git scons swig python3-openssl


echo "====================================================="
echo "========= 3. Clone required lib for leds ============"
echo "====================================================="
cd /tmp/
git clone https://github.com/jgarff/rpi_ws281x.git -b rpi2



echo "====================================================="
echo "============== 4. Building lib ======================"
echo "====================================================="
cd rpi_ws281x
scons


echo "====================================================="
echo "=============== 5. Installing lib ==================="
echo "====================================================="
cd python
python3 setup.py install


echo "====================================================="
echo "=============== 6. building cam title ==============="
echo "====================================================="
DIR=`dirname $0`;
cd $DIR/../gpucam/
echo "Please enter a name for this cam (you hav max 10 chars):";
read line;
echo "annotation ${line:0:10} %04d.%02d.%02d_%02d:%02d:%02d" > annotation.config
echo "anno_background false" >> annotation.config
./generate_config.sh


echo "Setup completed, shall I start the cam? (y/n): ";
read line;
if [ "$line" == "y" ];
then
	echo "====================================================="
	echo "=================== 7. starting ====================="
	echo "====================================================="
	cd ..
	./run.sh

	echo "The programm is running in a screen,"
	echo "It might be a good idea to open the screen to complete setup"
	echo "Remember, to leave the screen press 'strg+a' followed by 'd'"
	echo "Also remember that the client will wait 30sec before it starts!"
	echo "shall I open the screen now (y/n):";
	read line;
	if [ "$line" == "y" ];
	then
		screen -r
	fi
fi

echo "If you want your cam to start after bootup please add this"
echo "/home/pi/python/illuminum/client/run.sh to /etc/rc.local"
echo "before the line ->exit 0<-"
echo "Peace out"
