FROM laristra/flecsi-sp:ubuntu_mpi_master

ARG CC
ARG CXX
ARG CXXFLAGS
ARG BUILD_TYPE
ARG USE_SUBMODULES

#for coverage
ARG CI
ARG TRAVIS
ARG TRAVIS_BRANCH
ARG TRAVIS_JOB_NUMBER
ARG TRAVIS_PULL_REQUEST 
ARG TRAVIS_JOB_ID
ARG TRAVIS_TAG
ARG TRAVIS_REPO_SLUG
ARG TRAVIS_COMMIT


USER root

RUN apt-get -y update
RUN apt-get -y install \
    emacs \
    openssh-client \
    openssh-server \
    gcc \
    g++ \
    build-essential \
    autoconf \
    cmake \
    git \
    gfortran \
    libtool \
    libva-dev \
    pkg-config \
    python \
    python-dev \
    python-pip \
    xutils-dev \
    wget

#Install SSH
RUN mkdir /var/run/sshd
RUN sed -ri 's/^session\s+required\s+pam_loginuid.so$/session optional pam_loginuid.so/' /etc/pam.d/sshd

RUN mkdir /home/flecsi/.ssh/
# Create SSH Key
RUN ssh-keygen -t rsa -f /home/flecsi/.ssh/id_rsa -q -P ""

# Add authorized_keys
RUN cat /home/flecsi/.ssh/id_rsa.pub >> /home/flecsi/.ssh/authorized_keys

# Setup SSH config
RUN echo "Host *" >> /home/flecsi/.ssh/config
RUN echo "     Port 9222" >> /home/flecsi/.ssh/config
RUN echo "     StrictHostKeyChecking no" >> /home/flecsi/.ssh/config
RUN echo "     UserKnownHostsFile=/dev/null" >> /home/flecsi/.ssh/config

#COPY config /home/flecsi/.ssh/
RUN chmod 0700 /home/flecsi/.ssh; chmod 0600 /home/flecsi/.ssh/*
RUN sed -i 's/#Port 22/Port 9222/' /etc/ssh/sshd_config
RUN sed -i 's/Port 22/Port 9222/' /etc/ssh/sshd_config
RUN chown -R flecsi:flecsi /home/flecsi/.ssh
#RUN (echo "LD_LIBRARY_PATH=/usr/local/lib"; echo "") >> /etc/environment

RUN mkdir /mnt/docker_share
RUN chown -R flecsi:flecsi /mnt

#COPY flecsale /home/flecsi/flecsale
WORKDIR /home/flecsi
RUN git clone https://github.com/cjy7117/flecsale.git
WORKDIR /home/flecsi/flecsale
RUN git submodule update --init --recursive
USER root
RUN chown -R flecsi:flecsi /home/flecsi/flecsale
USER flecsi

WORKDIR /home/flecsi/flecsale
RUN mkdir build

WORKDIR build
RUN cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
          -DFLECSI_RUNTIME_MODEL=mpi \
          -DENABLE_UNIT_TESTS=ON \
          ..
RUN make -j2 || make VERBOSE=1
RUN make test ARGS="CTEST_OUTPUT_ON_FAILURE=1"
RUN make install DESTDIR=${PWD}

WORKDIR /home/flecsi