#!/bin/sh
# Install dependencies for Flux 
set -e

# Install dependencies as listed in https://github.com/flux-framework/flux-core/blob/master/scripts/install-deps-deb.sh
sudo apt-get install -y \
    autoconf \
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

# Update the python installation with cffi bindings for flux and purge the system cffi
sudo apt-get purge -y python3-cffi || true
python3 -m pip install "cffi>=1.15" pycparser
