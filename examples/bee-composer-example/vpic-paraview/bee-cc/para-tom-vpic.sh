#!/bin/bash

# BEE Charliecloud example using VPIC -> Paraview

VPIC_SHARE=/home/pbryant/vpic_share
VPIC_CH=/var/tmp/vpic

ch-run -b $VPIC_SHARE $VPIC_CH -- sh -c "/mnt/0/mytest/./turbulence_master.Linux"