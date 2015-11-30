for f in /dev/shm/mjpeg/n/*; do
 mv $f /dev/shm/mjpeg/cam_full.jpg;
done
cp /dev/shm/mjpeg/cam_full.jpg /dev/shm/mjpeg/cam_prev.jpg;
#install imagemagick for the convert, will cost even more cpu but less bandwidth
#convert -resize 640x480 /dev/shm/mjpeg/cam_full.jpg /dev/shm/mjpeg/cam_prev.jpg;
