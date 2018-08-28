wget https://www.open-mpi.org/software/ompi/v2.0/downloads/openmpi-2.0.2.tar.gz
tar -xzf openmpi-2.0.2.tar.gz
cd ./openmpi-2.0.2 && ./configure && make -j 8 all && make install
(echo "LD_LIBRARY_PATH=/usr/local/lib"; echo "") >> /etc/environment
