#  Dockerfile for VASP application

#  docker build --build-arg http_proxy="http://proxyout.lanl.gov:8080" \
#               --build-arg https_proxy="https://proxyout.lanl.gov:8080" \
#               . -t vasp:5.4.4
#
#  ch-build --build-arg http_proxy="http://proxyout.lanl.gov:8080" \
#           --build-arg https_proxy="https://proxyout.lanl.gov:8080" \
#           [--force] \
#           . -t vasp:5.4.4

FROM deb9ompi
MAINTAINER Steven Anaya <sanaya@lanl.gov>

ENV USER vasp

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/${USER} \
	WORKDIR=/vasp
    
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
RUN mkdir -p ${WORKDIR}
COPY ./vasp.5.4.4.tar.gz ${WORKDIR}
COPY ./scalapack_installer.tgz ${WORKDIR}
COPY ./symbol.inc-5.4.4.patch ${WORKDIR}
WORKDIR ${WORKDIR}
RUN zcat vasp.5.4.4.tar.gz | tar xf -
COPY ./makefile.include vasp.5.4.4
WORKDIR ${WORKDIR}/vasp.5.4.4
RUN patch -p0 < ${WORKDIR}/symbol.inc-5.4.4.patch
# Install Scalapack and dependencies
WORKDIR ${WORKDIR}
#RUN wget http://www.netlib.org/scalapack/scalapack_installer.tgz
RUN tar xzf scalapack_installer.tgz
WORKDIR ${WORKDIR}/scalapack_installer
RUN mkdir -p build
WORKDIR ${WORKDIR}/scalapack_installer/build
RUN wget http://www.netlib.org/lapack/lapack-3.8.0.tar.gz
RUN tar xzf lapack-3.8.0.tar.gz
RUN rm lapack-3.8.0.tar.gz
RUN mkdir -p download
WORKDIR ${WORKDIR}/scalapack_installer/build/download
RUN wget http://netlib.org/scalapack/scalapack-2.0.0.tgz
RUN mv scalapack-2.0.0.tgz scalapack.tgz
WORKDIR ${WORKDIR}/scalapack_installer
RUN ./setup.py --downall --mpirun='/usr/bin/mpirun --allow-run-as-root' --mpiincdir='/usr/lib/x86_64-linux-gnu/openmpi/include/mpi.h'
# VASP makefiles error if concurrent compiles are used
# RUN make -j$(getconf _NPROCESSORS_ONLN) std gam ncl
WORKDIR ${WORKDIR}/vasp.5.4.4
RUN make -j1 std gam ncl
# Cleanup image size
WORKDIR ${WORKDIR}
RUN rm vasp.5.4.4.tar.gz scalapack_installer.tgz
RUN rm -Rf vasp.5.4.4/src scalapack_installer/
# Add vasp binaries to PATH
RUN echo 'export PATH=${PATH}':"${WORKDIR}/vasp.5.4.4/bin" >> "${HOME}/.bashrc"

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

