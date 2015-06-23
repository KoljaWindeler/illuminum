cd /home/pi/python/illumino/client;
uv4l --driver raspicam  --auto-video_nr --width 1280 --height 7200 --framerate 10
export LD_PRELOAD=/usr/lib/uv4l/uv4lext/armv6l/libuv4lext.so
python3 client.py
