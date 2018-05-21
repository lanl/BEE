# Download base image ubuntu 16.04
#FROM ubuntu:16.04
FROM cjy7117/ubuntu-ompi
# Author
MAINTAINER Pascal Grosset

RUN ls /home

# add proxy
#ENV http_proxy http://proxyout.lanl.gov:8080
#ENV https_proxy http://proxyout.lanl.gov:8080

# Define default command.
CMD ["bash"]

# Update and install packages needed
RUN apt-get update
RUN apt-get -y install \
git \
wget \
cmake \
#openssh-server \
build-essential \
python2.7 python-dev \
#libopenmpi-dev openmpi-bin \
freeglut3-dev \
qt4-dev-tools \
libcereal-dev


# Set the default working directory for the container
WORKDIR /home
RUN ls

# Go to home and download Paraview and Catalyst flecsale
RUN wget https://www.paraview.org/files/v5.2/ParaView-v5.2.0.tar.gz 
RUN tar -zxvf ParaView-v5.2.0.tar.gz

RUN git clone --recursive -b flecsale_catalyst https://github.com/laristra/flecsale.git
RUN ls


# Build ParaView 5.2
WORKDIR /home/ParaView-v5.2.0
RUN mkdir build
WORKDIR /home/ParaView-v5.2.0/build
RUN ls
RUN cmake .. -DPARAVIEW_USE_MPI:BOOL=ON -DPARAVIEW_ENABLE_PYTHON:BOOL=ON -DPARAVIEW_ENABLE_CATALYST:BOOL=ON
RUN make -j16
ENV ParaView_DIR=""/home/ParaView-v5.2.0/build""



# Build Flecsale Catalyst
WORKDIR /home/flecsale
RUN mkdir build
WORKDIR /home/flecsale/build
RUN cmake .. -DUSE_CATALYST:BOOL=ON
RUN make -j16

RUN chown -R beeuser:beeuser /home

# Expose the ParaView Catalyst Port
EXPOSE 22222

