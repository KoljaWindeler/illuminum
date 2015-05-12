#sudo uv4l --driver raspicam  --auto-video_nr --width 320 --height 240 --framerate 5
export LD_PRELOAD=/usr/lib/uv4l/uv4lext/armv6l/libuv4lext.so
python3 client.py
