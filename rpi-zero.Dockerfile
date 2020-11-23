FROM resin/rpi-raspbian:latest

# Installing open-cv dependencies
RUN apt-get -y update && apt-get -y upgrade \
        && apt-get install -y python3-pip \
        python3-numpy \
        libblas-dev \
        liblapack-dev \
        python3-dev \
        libatlas-base-dev \
        gfortran \
        python3-setuptools \
        python3-scipy \
        && apt-get -y update \
        && apt-get -y install python3-h5py \
        libsm6 \
        libxext6 \
        libxrender-dev 

# Installing open-cv and other 
# RUN pip3 install scipy \
#                 cython \
#                 keras \
#                 opencv-python \
#                 scikit-image 

# Installing Flask and python-periphery
COPY ./requirements.txt /
RUN pip3 install -r requirements.txt 

COPY . /repo/
WORKDIR /repo
ENTRYPOINT ["bash", "start_services.bash"]