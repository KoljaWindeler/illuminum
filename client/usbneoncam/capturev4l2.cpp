#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <sys/sysinfo.h>

uint8_t *buffer;
uint16_t width=1280;
uint16_t height=720;
uint8_t quality=80;
uint8_t device=0;
float fps=5.0;
uint8_t brightness = 255;
uint8_t contrast = 255;
uint8_t saturation = 255;
uint8_t auto_white_balance = 255; // on off only
uint8_t gain = 255;
uint8_t power_line_freq = 255; // 0=off,1=50hz,2=60hz
uint8_t sharpness = 255;
uint8_t backlight_compensation = 255; // on off only
uint16_t white_balance_temperature = 255; // on off only

#define CAPTURE_PROTO "illuminum %02d:%02d:%02d:%03d"	// max 54 chars


 // access to device 
static int xioctl(int fd, int request, void *arg){
	int r;
	do r = ioctl (fd, request, arg);
	while (-1 == r && EINTR == errno);
	return r;
}

 
 // set parameter
int setup_cam(int fd){
	struct v4l2_capability caps = {};
	if (-1 == xioctl(fd, VIDIOC_QUERYCAP, &caps)){
		perror("Querying Capabilities");
		return 1;
	}

	printf( "== Configure cam ==\n"
		"  Driver Caps:\n"
		"  Driver: \"%s\"\n"
		"  Card: \"%s\"\n"
		"  Bus: \"%s\"\n"
		"  Version: %d.%d\n"
		"  Capabilities: %08x\n",
		caps.driver,
		caps.card,
		caps.bus_info,
		(caps.version>>16)&&0xff,
		(caps.version>>24)&&0xff,
		caps.capabilities
	);

	// load capability todo, needed?
	struct v4l2_cropcap cropcap = {0};
	cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	if (-1 == xioctl (fd, VIDIOC_CROPCAP, &cropcap)){
		perror("Querying Cropping Capabilities");
		return 1;
	}
	printf( "Camera Cropping:\n"
		"  Bounds: %dx%d+%d+%d\n"
		"  Default: %dx%d+%d+%d\n"
		"  Aspect: %d/%d\n",
		cropcap.bounds.width, cropcap.bounds.height, cropcap.bounds.left, cropcap.bounds.top,
		cropcap.defrect.width, cropcap.defrect.height, cropcap.defrect.left, cropcap.defrect.top,
		cropcap.pixelaspect.numerator, cropcap.pixelaspect.denominator
	);

	// check rgb10 support, todo needed?
	int support_grbg10 = 0;
	struct v4l2_fmtdesc fmtdesc = {0};
	fmtdesc.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	char fourcc[5] = {0};
	char c, e;
	while (0 == xioctl(fd, VIDIOC_ENUM_FMT, &fmtdesc)){
		strncpy(fourcc, (char *)&fmtdesc.pixelformat, 4);
		if (fmtdesc.pixelformat == V4L2_PIX_FMT_SGRBG10){
			support_grbg10 = 1;
		}
		c = fmtdesc.flags & 1? 'C' : ' ';
		e = fmtdesc.flags & 2? 'E' : ' ';
		printf("  %s: %c%c %s\n", fourcc, c, e, fmtdesc.description);
		fmtdesc.index++;
	}

	// == set resolution and format ==
	// todo, request if available
	struct v4l2_format fmt = {0};
	fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	fmt.fmt.pix.width = width;
	fmt.fmt.pix.height = height;
	fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;
	fmt.fmt.pix.field = V4L2_FIELD_NONE;
	if (-1 == xioctl(fd, VIDIOC_S_FMT, &fmt)){
		perror("Setting Pixel Format");
		return 1;
	}

	// == set valid frame rates ==
	struct v4l2_frmivalenum frmival;
	memset(&frmival,0,sizeof(frmival));
	frmival.pixel_format = V4L2_PIX_FMT_MJPEG;
	frmival.width = width;
	frmival.height = height;
	bool found=false;
	bool discrete=false;
	while (xioctl(fd, VIDIOC_ENUM_FRAMEINTERVALS, &frmival) == 0){
		if (frmival.type == V4L2_FRMIVAL_TYPE_DISCRETE) {
			if(1.0*float(frmival.discrete.denominator/frmival.discrete.numerator) == fps){
				// frame rate found
				discrete=true;
				found=true;
				break;
			}
		} else {
			printf("oho non discrete fps mode");
			if(1.0*frmival.stepwise.max.denominator/frmival.stepwise.max.numerator+0.1*frmival.stepwise.min.denominator/frmival.stepwise.min.numerator==fps){
				// frame rate found
				found=true;
				break;
			}
		}
		frmival.index++;
	}
	if(!found){
		// reset iterator
		memset(&frmival,0,sizeof(frmival));
		frmival.pixel_format = V4L2_PIX_FMT_MJPEG;
		frmival.width = width;
		frmival.height = height;

		printf("Can't find requested configuration of %i fps, please choose from the list below and restart\n",fps);
		while (xioctl(fd, VIDIOC_ENUM_FRAMEINTERVALS, &frmival) == 0){
			if (frmival.type == V4L2_FRMIVAL_TYPE_DISCRETE) {
				printf("[%dx%d] %f fps\n", width, height, 1.0*frmival.discrete.denominator/frmival.discrete.numerator);
			} else {
				printf("[%dx%d] [%f,%f] fps\n", width, height, 1.0*frmival.stepwise.max.denominator/frmival.stepwise.max.numerator, 1.0*frmival.stepwise.min.denominator/frmival.stepwise.min.numerator);
			}
			frmival.index++;
		}
		perror("Setting fps failed, stopping");
		return 1;
	} else {
		// set frame rate
		struct v4l2_streamparm setfps;
		memset(&setfps, 0, sizeof(struct v4l2_streamparm));
		setfps.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		if(discrete){
			setfps.parm.capture.timeperframe.numerator=frmival.discrete.numerator;
			setfps.parm.capture.timeperframe.denominator=frmival.discrete.denominator;
		} else {
			// todo
			setfps.parm.capture.timeperframe.numerator=frmival.stepwise.max.numerator;
			setfps.parm.capture.timeperframe.denominator=frmival.stepwise.max.denominator;
			setfps.parm.capture.timeperframe.numerator=frmival.stepwise.min.numerator;
			setfps.parm.capture.timeperframe.denominator=frmival.stepwise.min.denominator;
		};
		if (-1 == xioctl(fd, VIDIOC_S_PARM, &setfps)){
			perror("Setting frame rate failed");
			return 1;
		}
	}

	// iterate through all controls
	printf ("Setting video controls\n");

	struct v4l2_queryctrl queryctrl;
	struct v4l2_querymenu querymenu;
	memset(&queryctrl,0, sizeof (queryctrl));
	struct v4l2_control control;

	for (queryctrl.id = V4L2_CID_BASE; queryctrl.id < V4L2_CID_LASTP1; queryctrl.id++){
		if (0 == xioctl (fd, VIDIOC_QUERYCTRL, &queryctrl)) {
			if (queryctrl.flags & V4L2_CTRL_FLAG_DISABLED){
				continue;
			}
			if(queryctrl.id == V4L2_CID_BRIGHTNESS){
				control.id = queryctrl.id;
				control.value = brightness;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("8error set _CTRL");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_CONTRAST){
				control.id = queryctrl.id;
				control.value = contrast;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("7error set _CTRL");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_SATURATION){
				control.id = queryctrl.id;
				control.value = saturation;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("6error set _CTRL");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_AUTO_WHITE_BALANCE){
				control.id = queryctrl.id;
				control.value = auto_white_balance;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("5error set _CTRL");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_GAIN){
				control.id = queryctrl.id;
				control.value = gain;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("4error set _CTRL");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_POWER_LINE_FREQUENCY){
				control.id = queryctrl.id;
				control.value = power_line_freq;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("3error set _CTRL arg");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_BACKLIGHT_COMPENSATION){
				control.id = queryctrl.id;
				control.value = backlight_compensation;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("2error set _CTRL boom");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_SHARPNESS){
				control.id = queryctrl.id;
				control.value = sharpness;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("1error set _CTRL boom");	exit (EXIT_FAILURE);  }
				printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
			} else if(queryctrl.id == V4L2_CID_WHITE_BALANCE_TEMPERATURE){
				control.id = queryctrl.id;
				control.value = white_balance_temperature;
				if(control.value == 255) { control.value = queryctrl.default_value; };
				if(auto_white_balance == 0){
					if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("0error set _CTRL boom");	exit (EXIT_FAILURE);  }
					printf ("  %3i - %5i, default %5i | set value %5i for Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
				};
			} else {
				control.id = queryctrl.id;
				control.value = queryctrl.default_value;
				printf ("  %3i - %5i, default %5i | set value %5i for UNUSED Control %s\n", queryctrl.minimum, queryctrl.maximum, queryctrl.default_value, control.value, queryctrl.name);
				//if (-1 == ioctl (fd, VIDIOC_S_CTRL, &control)) {	perror ("1error set _CTRL");	exit (EXIT_FAILURE); }
			}

		} else {
			if (errno == EINVAL)
				continue;

			perror ("VIDIOC_QUERYCTRL");
			exit (EXIT_FAILURE);
		}
	}


	// == output ==
	strncpy(fourcc, (char *)&fmt.fmt.pix.pixelformat, 4);
	printf( "Selected Camera Mode:\n"
		"  Width: %d\n"
		"  Height: %d\n"
		"  PixFmt: %s\n"
		"  FPS: %i/%i\n"
		"  Field: %d\n",
		fmt.fmt.pix.width,
		fmt.fmt.pix.height,
		fourcc,
		frmival.discrete.denominator,
		frmival.discrete.numerator,
		fmt.fmt.pix.field
	);
	printf( "== Configure cam done ==\n");


	return 0;
}
 
int init_mmap(int fd){
	printf( "== Configure buffer ==\n");

	struct v4l2_requestbuffers req = {0};
	req.count = 1;
	req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	req.memory = V4L2_MEMORY_MMAP;

	if (-1 == xioctl(fd, VIDIOC_REQBUFS, &req)){
		perror("Requesting Buffer");
		return 1;
	}

	struct v4l2_buffer buf = {0};
	buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf.memory = V4L2_MEMORY_MMAP;
	buf.index = 0;
	if(-1 == xioctl(fd, VIDIOC_QUERYBUF, &buf)){
		perror("Querying Buffer");
		return 1;
	}

	int prot = PROT_READ | PROT_WRITE;
	int flags = MAP_SHARED;
	buffer = (uint8_t*)mmap ((void*)NULL, (size_t)buf.length, prot, flags,fd, (off_t) buf.m.offset);
	printf("Length: %d\nAddress: %p\n", buf.length, buffer);
	printf("Image Length: %d\n", buf.bytesused);

	printf( "== Configure buffer done ==\n");
	return 0;
}

// called by the loop to actually grab the frames
int capture_image(int fd,CvFont *font, int *set_quality, IplImage* frame,CvMat *cvmat,char *capture_title,v4l2_buffer *buf, uint32_t *start_time, uint32_t *image_count){

	// request a new frame
	if(-1 == xioctl(fd, VIDIOC_QBUF, buf)){
		perror("Query Buffer");
		return 1;
	}

	// wait up to 2 sec for a new frame to arive
	fd_set fds;
	FD_ZERO(&fds);
	FD_SET(fd, &fds);
	struct timeval tv = {0};
	tv.tv_sec = 2;
	int r = select(fd+1, &fds, NULL, NULL, &tv);
	if(-1 == r){
		perror("Waiting for Frame");
		return 1;
	}

	// read it
	if(-1 == xioctl(fd, VIDIOC_DQBUF, buf)){
		perror("Retrieving Frame");
		return 1;
	}

	// convert v4l2 buffer to opencv image
	*cvmat = cvMat(height, width, CV_8UC3, (void*)buffer);
	frame = cvDecodeImage(cvmat, 1);

	// add title, reused tv from select-wait
	gettimeofday(&tv, NULL);
	time_t secs = time(0);
	struct tm *local = localtime(&secs);
	sprintf(capture_title, CAPTURE_PROTO, local->tm_hour, local->tm_min, local->tm_sec, (int)((unsigned long long)(tv.tv_usec) / 1000)%1000);

	(*image_count)++;
	printf("%s @ %2.2f fps\n",capture_title, round((float)(*image_count)*100/(time(0)-(*start_time)))/100 );
	cvPutText(frame, capture_title, cvPoint(22, 22), font, cvScalar(0,0,0,0));
	cvPutText(frame, capture_title, cvPoint(24, 24), font, cvScalar(200,200,200,0));

	// save to disk ... well RAM
	cvSaveImage("/dev/shm/mjpeg/cam_full.part.jpg", frame, set_quality);
	rename("/dev/shm/mjpeg/cam_full.part.jpg","/dev/shm/mjpeg/cam_full.jpg");

	// important to avoid mem leakage
	cvReleaseImage(&frame);

	return 0;
}

void parse_parameter(int argc, char* argv[]){
	for (int i = 1; i < argc; i++) {
		if (std::string(argv[i]) == "-W") {
			width = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-H") {
			height = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-Q") {
			quality = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-D") {
			device = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-F") {
			fps = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-B") {
			brightness = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-C") {
			contrast = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-S") {
			saturation = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-AWB") {
			auto_white_balance = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-G") {
			gain = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-PLF") {
			power_line_freq = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-SH") {
			sharpness = atoi(argv[i + 1]);
			i++;
                } else if (std::string(argv[i]) == "-BC") {
			backlight_compensation = atoi(argv[i + 1]);
			i++;
		} else if(std::string(argv[i]) == "-WBT") {
			white_balance_temperature = atoi(argv[i + 1]);
			i++;
                } else {
			printf("didn't understand %s\n",argv[i]);
		};
	}
}


int main(int argc, char* argv[]){
	parse_parameter(argc, argv);

	// prepare some info outside the loop
	int fd;
	CvFont font;
	cvInitFont(&font, CV_FONT_HERSHEY_SIMPLEX, 0.7, 0.7, 0, 2); // 0 shear, 3 px wide

	int set_quality[3] = {CV_IMWRITE_JPEG_QUALITY, quality,  0};
	char capture_title[55];
	IplImage* frame;
	CvMat cvmat;

	// startup
	char dev[20];
	sprintf(dev,"/dev/video%i",device);
	fd = open(dev, O_RDWR);
	if (fd == -1){
		perror("Opening video device");
		return 1;
	}
	if(setup_cam(fd)){
		return 1;
	}
	if(init_mmap(fd)){
		return 1;
	}

	// define buffer and activate streaming on the cam
	struct v4l2_buffer buf = {0};
	buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf.memory = V4L2_MEMORY_MMAP;
	buf.index = 0;
	if(-1 == xioctl(fd, VIDIOC_STREAMON, &buf.type)){
		perror("Start Capture");
		return 1;
	}

	// loop fps measurement
	uint32_t start_time = time(0);
	uint32_t image_count = 0;

  	//for(int i=0; i<100; i++){
	/// run forever
	while(1){
		if(capture_image(fd,&font,set_quality,frame,&cvmat,capture_title,&buf,&start_time,&image_count)){
			return 1;
		}
	}
	
	// todo, close gracefully
	printf("closing fd\n");
	close(fd);
	return 0;
}
