FROM balenalib/rpi-raspbian:latest


# Installing numpy and its dependecies
RUN apt update && \
    apt install -y \
        build-essential \
        make \
        gcc \
    && apt remove -y --purge make gcc build-essential \
    && apt autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Installing Flask and python-periphery
RUN apt install -y --fix-missing \
	# python3-matplotlib \
	python3-pip \
	# python3-scipy \
	python3-wget
    
COPY ./requirements.txt /
RUN pip3 install -r requirements.txt 

COPY . /repo/
WORKDIR /repo
ENTRYPOINT ["bash", "start_services.bash"]