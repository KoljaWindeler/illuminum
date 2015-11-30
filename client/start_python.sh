locationOfScript=$(dirname "$(readlink -e "$0")")
cd $locationOfScript/python;
echo "30 sec start delay to give the unit time to connect to the WiFi"
sleep 10
echo "20 sec remaining ..."
sleep 10
echo "10 sec remaining ..."
sleep 5
echo "5..."
sleep 1
echo "4..."
sleep 1
echo "ready..."
sleep 1
echo "set..."
sleep 1
echo "go..."

python3 client.py
