#!/bin/bash

# Copy vpic to shared dir
cp -r /root/* /mnt/vpicrun

# Create bin dir for vpic
mkdir -p /mnt/vpicrun/vpic.bin

# Compile vpic
cd /mnt/vpicrun/vpic.bin
cmake \
  -DUSE_CATALYST=ON \
  -DCMAKE_BUILD_TYPE=Release \
  /mnt/vpicrun/vpic
make -j16

cp /root/8preconnection.cxx ../vpic/sample

export CPLUS_INCLUDE_PATH=/mnt/vpicrun/vpic/src/util/catalyst/
./bin/vpic ../vpic/sample/8preconnection.cxx
mkdir -p /mnt/vpicrun/vpicrun2
cd /mnt/vpicrun/vpicrun2
export LD_LIBRARY_PATH=/usr/local/paraview.bin/lib
echo "Sleeping 5 to wait for filehandle."
sleep 5
echo "Launching 8preconnection"

mkdir /mnt/vpicrun/darshan_logs
/usr/projects/darshan/sw/darwin/bin/darshan-mk-log-dirs.pl
export LD_PRELOAD=/usr/projects/darshan/sw/darwin/lib/libdarshan.so


LD_LIBRARY_PATH=/usr/local/paraview.bin/lib mpirun --allow-run-as-root --mca btl_tcp_if_include eth0 -np 8 /mnt/vpicrun/vpic.bin/8preconnection.Linux
