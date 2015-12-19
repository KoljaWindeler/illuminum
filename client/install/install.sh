#!/bin/bash
pushd `dirname $0` > /dev/null
DIR=`pwd -P`
popd > /dev/null

echo "====================================================="
echo "=============== 1. Updating ========================="
echo "====================================================="
aptitude update


echo "====================================================="
echo "========= 2. Installing required packages ==========="
echo "====================================================="
aptitude install screen build-essential python3-dev git scons swig python3-openssl python-setuptools


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
echo "========= 6. Clone required lib for leds ============"
echo "====================================================="
cd /tmp/
git clone https://github.com/Gadgetoid/WiringPi2-Python.git


echo "====================================================="
echo "============== 7. install lib ======================="
echo "====================================================="
cd WiringPi2-Python
python3 setup.py install


echo "====================================================="
echo "=============== 8. building cam title ==============="
echo "====================================================="
cd $DIR/../gpucam/
echo "Please enter a name for this cam (you hav max 10 chars):";
read line;
echo "annotation ${line:0:10} %04d.%02d.%02d_%02d:%02d:%02d" > annotation.config
echo "anno_background false" >> annotation.config
./generate_config.sh

echo "====================================================="
echo "================= 9. autostart ======================"
echo "====================================================="
echo "shall the cam start automatically on boot? (y/n): ";
read line;
if [ "$line" == "y" ];
then
	T=$DIR"/../run.sh";
	F=/etc/rc.local
	if grep -q $T $F; then
		echo "autostart already present";
	else
		sed -i -e 's|exit 0|'$T'\&;\r\n&|g' $F
		echo "autostart added";
	fi
fi


echo "Setup completed, shall I start the cam? (y/n): ";
read line;
if [ "$line" == "y" ];
then
	echo "====================================================="
	echo "=================== 9. starting ====================="
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

echo "Peace out"

