FROM OSOS:TAGTAG
#proxy for LANL
#ENV http_proxy=http://proxyout.lanl.gov:8080
#ENV https_proxy=http://proxyout.lanl.gov:8080

#set docker's UID/GID to be same as vm and host for dir sharing
#when build, append: "--build-arg uid=$(id -u),gid=$(id -g)"
#ARG uid=1000
#ARG gid=1000

#RUN echo $uid
#RUN echo $gid

USER root

#RUN apt-get -y update
#RUN apt-get -y install \
#    emacs24 \
#    openssh-client \
#    openssh-server \
#    gcc \
#    g++ \
#    build-essential \
#    autoconf \
#    cmake \
#    git \
#    gfortran \
#    libtool \
#    libva-dev \
#    pkg-config \
#    python \
#    python-dev \
#    python-pip \
#    xutils-dev \
#    wget

#RUN groupadd -r albuntu -g $gid && useradd -r -m -g albuntu -u $uid albuntu -s /bin/bash

#RUN useradd -ms /bin/bash  beeuser
 


#Install SSH
RUN mkdir /var/run/sshd
RUN sed -ri 's/^session\s+required\s+pam_loginuid.so$/session optional pam_loginuid.so/' /etc/pam.d/sshd

RUN mkdir /home/BEEUSER/.ssh/
#COPY ~/.ssh/id_rsa /home/BEEUSER/.ssh/
#COPY ~/.ssh/id_rsa.pub /home/BEEUSER/.ssh/
#COPY config /home/BEEUSER/.ssh/
RUN chmod 0700 /home/BEEUSER/.ssh; chmod 0600 /home/BEEUSER/.ssh/*
#RUN cat /home/BEEUSER/.ssh/id_rsa.pub >> /home/BEEUSER/.ssh/authorized_keys
RUN sed -i 's/Port 22/Port 9222/' /etc/ssh/sshd_config
RUN chown -R BEEUSER:BEEUSER /home/BEEUSER/.ssh

RUN mkdir /mnt/docker_share
RUN chown -R BEEUSER:BEEUSER /mnt


