# heimann-api

## Build docker
$ docker build -f rpi-zero.Dockerfile -t "projects/heimann-api:latest" .

## Run docker
docker run --device /dev/i2c-1 -v /repo/logs -it -d -p 0.0.0.0:5000:5000 projects/heimann-api:latest

 