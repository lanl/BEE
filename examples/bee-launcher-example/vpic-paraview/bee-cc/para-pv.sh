#!/bin/bash

VPIC_CH=/var/tmp/vpic
VPIC_OUT=~/vpic_share

ch-run --no-home -b $VPIC_OUT:/mnt/docker_share $VPIC_CH -- \
    sh -c "/usr/local/paraview.bin/bin/pvserver --server-port=11111 &"
