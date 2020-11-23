# heimann-api

## Build docker
$ docker build -f rpi-zero.Dockerfile -t "projects/heimann-api:latest" .

## Run docker
docker run --device /dev/video0 -v /repo/logs -it -d -p 0.0.0.0:5000:5000 projects/heimann-api:latest