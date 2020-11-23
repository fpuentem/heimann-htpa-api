FROM balenalib/rpi-raspbian:latest


# Installing numpy and its dependecies
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        make \
        gcc \
    && apt-get remove -y --purge make gcc build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Installing Flask and python-periphery
RUN apt-get install -y --fix-missing \
	# python3-matplotlib \
	python3-pip \
	# python3-scipy \
	python3-wget
    
COPY ./requirements.txt /
RUN pip3 install -r requirements.txt 

COPY . /repo/
WORKDIR /repo
ENTRYPOINT ["bash", "start_services.bash"]