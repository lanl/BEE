#!/bin/bash
mkdir -p vpic_share
srun cp -R /var/tmp/vpic/usr/local/paraview.bin/lib /var/tmp/vpic/usr
srun cp -R /var/tmp/vpic/usr/local/lib /var/tmp/vpic/usr

ch-run --no-home -b vpic_share:/mnt/docker_share /var/tmp/vpic -- \
	/home/beeuser/launch.sh
