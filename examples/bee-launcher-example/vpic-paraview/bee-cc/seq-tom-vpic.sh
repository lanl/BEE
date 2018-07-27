#!/bin/bash

VPIC_CH=/var/tmp/vpic
VPIC_OUT=~/vpic_share
LAUNCH_LOC=/home/beeuser/launch.sh

ch-run --no-home -b $VPIC_OUT:/mnt/docker_share $VPIC_CH -- sh $LAUNCH_LOC
