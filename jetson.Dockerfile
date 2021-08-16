# Getting Jetson Containers on NGC 
FROM nvcr.io/nvidia/l4t-base:r32.4.3

# Installing numpy and its dependecies
RUN apt-get update && \
    apt-get install -y \
        python3-numpy \
        python3-scipy \
        python3-pip 

   
COPY ./requirements.txt /
RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt 

COPY . /repo/
WORKDIR /repo
ENTRYPOINT ["bash", "start_services.bash"]