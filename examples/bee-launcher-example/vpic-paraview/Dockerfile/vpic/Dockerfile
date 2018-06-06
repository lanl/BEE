from cjy7117/pvcat

#ENV http_proxy=""
#ENV https_proxy=""

RUN echo '' > /etc/apt/apt.conf.d/docker-clean


RUN apt-get update

#RUN apt-get -y install \
#  vim\
#  python-numpy\
#  emacs24

# follow instructions in https://github.com/docker/docker/issues/5663
#RUN sed -ri 's/^session\s+required\s+pam_loginuid.so$/session optional pam_loginuid.so/' /etc/pam.d/sshd


#RUN useradd -ms /bin/bash  beeuser

# setup ssh keys and config
#COPY id_rsa /home/beeuser/.ssh/
#COPY id_rsa.pub /home/beeuser/.ssh/
#COPY config /home/beeuser/.ssh/
#RUN chmod 0700 /home/beeuser/.ssh; chmod 0600 /home/beeuser/.ssh/*
#RUN sed -i 's/Port 22/Port 9222/' /etc/ssh/sshd_config

# add no password login
#RUN cat /home/beeuser/.ssh/id_rsa.pub >> /home/beeuser/.ssh/authorized_keys





WORKDIR /home/beeuser

RUN git clone https://github.com/Tomyao/vpic.git

RUN mkdir /home/beeuser/vpic.bin
WORKDIR /home/beeuser/vpic.bin
RUN cmake \
    -DUSE_CATALYST=ON \
    -DCMAKE_BUILD_TYPE=Release \
    /home/beeuser/vpic
RUN make -j16


# add the launcher scripts for the docker file
ADD launch.sh /home/beeuser
ADD runvpic.sh /home/beeuser
ADD vpic_config /home/beeuser
ADD vpic_config2 /home/beeuser

#RUN chown -R beeuser:beeuser /home/beeuser/.ssh

USER beeuser

#RUN mkdir /var/run/sshd