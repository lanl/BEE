#!/usr/bin/env bash
export OMPI_MCA_btl_vader_single_copy_mechanism=none
mkdir -p output

ch-run -w --no-home -b output --cd /mnt/0 /var/tmp/flecsale\
  -- /home/flecsi/flecsale/build/apps/hydro/2d/hydro_2d\
  -m /home/flecsi/flecsale/specializations/data/meshes/2d/square/square_32x32.g

