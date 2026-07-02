#!/bin/sh
# Install and Set Up Flux

set -e
. ./ci/env.sh

# Install flux-security
git clone --depth 1 -b v${FLUX_SECURITY_VERSION} https://github.com/flux-framework/flux-security.git
(cd flux-security
 ./autogen.sh
 PYTHON=/usr/bin/python3.11 ./configure --prefix=$GITHUB_WORKSPACE/deps
 make
 sudo make install
 sudo ldconfig)

# Install flux-core
git clone --depth 1 -b v${FLUX_CORE_VERSION} https://github.com/flux-framework/flux-core.git
(cd flux-core
 ./autogen.sh
 PYTHON=/usr/bin/python3.11 ./configure --prefix=$GITHUB_WORKSPACE/deps
 make
 sudo make install
 sudo ldconfig)
