#!/bin/sh
# Install, set up, and start Flux

. ./ci/env.sh

# Install dependencies as listed in https://github.com/flux-framework/flux-core/blob/master/scripts/install-deps-deb.sh
sudo apt-get install -y \
    autoconf \
    automake \
    libtool \
    make \
    p-config \
    libc6-dev \
    libzmq3-dev \
    libczmq-dev \
    uuid-dev \
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

# Install flux-core
git clone --depth 1 -b v${FLUX_VERSION} git@github.com:flux-framework/flux-core.git
(cd flux-core
 ./autogen.sh
 ./configure --prefix=/usr
 make
 sudo make install)
# Install the python API
pip install --user wheel
pip install --user flux-python==$FLUX_VERSION
