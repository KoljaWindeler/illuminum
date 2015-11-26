
mkdir /dev/shm/mjpeg/ 2>/dev/null
killall raspimjpeg 2>/dev/null

locationOfScript=$(dirname "$(readlink -e "$0")")
$locationOfScript/gpucam/raspimjpeg -v --config $locationOfScript/gpucam/raspimjpeg.config
