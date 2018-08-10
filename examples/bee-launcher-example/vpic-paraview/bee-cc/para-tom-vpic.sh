#!/bin/bash

ch-run --no-home -b vpic_share:/mnt/docker_share -c /mnt/docker_share/mytest /var/tmp/vpic \
-- sh -c ./turbulence_master.Linux
