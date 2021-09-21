#  Dockerfile for VASP application

# On Galton:
#  docker build --build-arg http_proxy="http://proxyout.lanl.gov:8080" \
#               --build-arg https_proxy="https://proxyout.lanl.gov:8080" \
#               . -t losalamosal/vasp

FROM losalamosal/ch-base-deb9ompi
MAINTAINER Allen McPherson <mcpherson@lanl.gov>

ENV USER vasp

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/${USER}
    
RUN adduser --disabled-password --gecos "" ${USER} && \
    echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    
# Some of these may have been installed by base image but are listed
# here for completeness.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        openssh-server make build-essential gfortran g++ python \
        libblas-dev liblapack-dev libscalapack-mpi-dev libfftw3-dev && \
    apt-get clean && apt-get purge && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set up SSH
RUN mkdir /var/run/sshd
RUN echo 'root:${USER}' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# The link explains why this bit of code is here
# https://stackoverflow.com/questions/36292317/why-set-visible-now-in-etc-profile
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Set-Up SSH with our BEE application keys.
ENV SSHDIR ${HOME}/.ssh/

RUN mkdir -p ${SSHDIR}

ADD ./keys/config ${SSHDIR}/config
ADD ./keys/id_rsa ${SSHDIR}/id_rsa
ADD ./keys/id_rsa.pub ${SSHDIR}/id_rsa.pub
ADD ./keys/id_rsa.pub ${SSHDIR}/authorized_keys

RUN chmod -R 600 ${SSHDIR}* && \
    chown -R ${USER}:${USER} ${SSHDIR}

# Build VASP
COPY ./makefile.include ${HOME}
COPY ./vasp.5.4.4.tar.gz ${HOME}
COPY ./symbol.inc-5.4.4.patch ${HOME}
WORKDIR ${HOME}
RUN zcat vasp.5.4.4.tar.gz | tar xf -
COPY ./makefile.include vasp.5.4.4
WORKDIR ${HOME}/vasp.5.4.4
RUN patch -p0 < ${HOME}/symbol.inc-5.4.4.patch
# Install Scalapack and dependencies
WORKDIR ${HOME}
RUN wget http://www.netlib.org/scalapack/scalapack_installer.tgz
RUN tar xzf scalapack_installer.tgz
WORKDIR ${HOME}/scalapack_installer
RUN ./setup.py --downall --mpirun='/usr/local/bin/mpirun --allow-run-as-root'
# VASP makefiles error if concurrent compiles are used
# RUN make -j$(getconf _NPROCESSORS_ONLN) std gam ncl
WORKDIR ${HOME}/vasp.5.4.4
RUN make -j1 std gam ncl
# RUN rm vasp.5.4.4.tar.gz
# RUN rm -Rf vasp.5.4.4/src

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
