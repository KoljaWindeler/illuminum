mkdir /dev/shm/mjpeg/
killall raspimjpeg
/home/pi/python/illumino/client/gpucam/raspimjpeg -v --config /home/pi/python/illumino/client/gpucam/raspimjpeg.config
