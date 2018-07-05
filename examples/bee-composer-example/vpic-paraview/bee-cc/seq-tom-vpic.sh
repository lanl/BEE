#!/bin/bash

# BEE Charliecloud example using VPIC -> Paraview

VPIC_SHARE=/home/pbryant/vpic_share

ch-run --nohome -b $VPIC_SHARE  /var/tmp/vpic -- sh /home/beeuser/launch.sh
