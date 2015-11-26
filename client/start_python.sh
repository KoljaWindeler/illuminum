locationOfScript=$(dirname "$(readlink -e "$0")")
cd $locationOfScript/python;
sleep 30
python3 client.py
