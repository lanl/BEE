FROM ubuntu:22.04

# Install base dependencies and Slurm
RUN apt-get update \
 && apt-get install -y slurmctld \
                       slurmd \
                       slurmrestd \
                       munge \
                       python3 \
                       python3-venv \
                       curl \
                       build-essential \
                       zlib1g-dev \
                       libncurses5-dev \
                       libgdbm-dev \
                       libnss3-dev \
                       libssl-dev \
                       libsqlite3-dev \
                       libreadline-dev \
                       libffi-dev \
                       libbz2-dev \
                       libmunge-dev \
                       libyaml-dev \
                       software-properties-common \
                       python3 \
                       python3-dev \
                       python3-venv

# Install most recent Charliecloud
RUN curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.33/charliecloud-0.33.tar.gz \
 && tar -xvf charliecloud-0.33.tar.gz \
 && cd charliecloud-0.33 \
 && ./configure --prefix=/usr \
 && make \
 && make install

# Install Flux dependencies as listed in https://github.com/flux-framework/flux-core/blob/master/scripts/install-deps-deb.sh
RUN apt-get install -y autoconf \
                       automake \
                       libtool \
                       make \
                       pkg-config \
                       libc6-dev \
                       libzmq3-dev \
                       libczmq-dev \
                       uuid-dev \
                       libjson-glib-dev \
                       libjansson-dev \
                       liblz4-dev \
                       libarchive-dev \
                       libhwloc-dev \
                       libsqlite3-dev \
                       lua5.1 \
                       liblua5.1-dev \
                       lua-posix \
                       python3-dev \
                       python3-cffi \
                       python3-ply \
                       python3-yaml \
                       python3-jsonschema \
                       python3-sphinx \
                       aspell \
                       aspell-en \
                       valgrind \
                       libmpich-dev \
                       jq
# Install flux-security
RUN git clone --depth 1 -b v${FLUX_SECURITY_VERSION} https://github.com/flux-framework/flux-security.git \
 && cd flux-security \
 && ./autogen.sh \
 && ./configure --prefix=/usr \
 && make \
 && sudo make install \
 && sudo ldconfig
# Install flux-core
RUN git clone --depth 1 -b v${FLUX_CORE_VERSION} https://github.com/flux-framework/flux-core.git \
 && cd flux-core \
 && ./autogen.sh \
 && ./configure --prefix=/usr \
 && make \
 && make install \
 && ldconfig
# Install the python API
RUN pip install wheel \
 && pip install --user flux-python==$FLUX_CORE_VERSION
