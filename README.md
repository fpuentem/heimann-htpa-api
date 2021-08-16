# heimann-api

## Introduction
REST API that handle the driver of HTPA 32x32 thermophile array sensor [https://www.heimannsensor.com/32x32] for NVIDIA Jetson Xavier. As the driver and framework was implemented entirely in Python, it easily can be moved to other SBC(Single board computer) platforms. There are two endpoints that return raw data(before temperature interpolation) and temperature data.  In case of temperature data calibration must be done to get accurate results, for while all these calibrations values are hard-coded.  
## Pre-requisites
### Hardware
** As host edge device we use NVIDIA Jetson Xavier/Nano.
** As sensor sensor device we use HTPA 32x32 Thermopile Array(I2C protocol).

### Software 
You should have [Docker](https://docs.docker.com/get-docker/) and [post-install](https://docs.docker.com/engine/install/linux-postinstall/) steps.

## Usage
### Creating work directory
All the scripts and repositories must be downloaded in a common directory.
```bash
mkdir -p $HOME/projects/
cd $HOME/projects/
```

### Getting git repository
Make sure your system fulfills the prerequisites and then clone this repository to your local system by running this command:
```bash
git clone https://github.com/fpuentem/heiman-api
cd heimann-api
```
### Building Docker image
* You need to have JetPack 4.4 installed on your Jetson.
```bash
# Build Docker image for Jetson
docker build -f jetson.Dockerfile -t "vt/heimann-api:latest-jetson-xavier" .
```

### Run Docker container
* Make sure that the HTPA sensor is connected physically to correct i2c bus with [i2cdetect](https://manpages.debian.org/unstable/i2c-tools/i2cdetect.8.en.html) tool.
```bash
docker run -it --device /dev/i2c-1:/dev/i2c-1 --runtime nvidia -p 0.0.0.0:5050:5050 -d vt/heimann-api:latest-jetson-xavier
```
### API usage
After you run the software on your Jetson, you can use the exposed API to get temperature data.

The available endpoints are the following:
- `/home`: provides an endpoint of initial page.
- `/raw-data`: provides an  endpoint to get values previous temperature interpolation. It could be used for image generation purposes.
- `/temperature`: provides an  endpoint to get temperature values in Celsius degrees.

## Future improvements
* A configuration file and configuration class to avoid hard-code in sensor calibration.
* Implementaton to handle broken pixels. 