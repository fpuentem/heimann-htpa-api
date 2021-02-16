# heimann-api

## Build docker image 
$ docker build -f jetson.Dockerfile -t "vt/heimann-api:latest-jetson-xavier" .

## Run docker image
docker run -it --device /dev/i2c-1:/dev/i2c-1 --runtime nvidia -p 0.0.0.0:5050:5050 -v "$PWD":/repo vt/heimann-api:latest-jetson-xavier
