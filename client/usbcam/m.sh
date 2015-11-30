for f in /dev/shm/mjpeg/n/*; do
 mv $f /dev/shm/mjpeg/cam_full.jpg;
done
cp /dev/shm/mjpeg/cam_full.jpg /dev/shm/mjpeg/cam_prev.jpg;
