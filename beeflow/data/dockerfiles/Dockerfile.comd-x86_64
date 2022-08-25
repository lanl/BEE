FROM debian:11

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
    apt-get -y install git cmake gcc g++ gfortran libopenmpi-dev openmpi-bin \
                       libpmix-dev libpmix-bin

# Build the MPI version
ARG REPO=https://github.com/ECP-copa/CoMD.git
RUN git clone $REPO && \
    cd CoMD && \
    cp src-mpi/Makefile.vanilla src-mpi/Makefile && \
    make -C src-mpi
