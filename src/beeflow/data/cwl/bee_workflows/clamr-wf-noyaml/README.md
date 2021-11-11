# CLAMR-FFMPEG WORKFLOW

This workflow executes the `CLAMR` AMR simulation and then runs `ffmpeg` to produce a video from the `CLAMR` output. These workflows place the command all on one line and were used early in the development of BEE. 


Systems with valid CLAMR workflows include

* Fog (LANL system) slurm/charliecloud
* Summit (ORNL system) lsf/charliecloud
* Darwin (LANL system) slurm/charliecloud
* Case (LANL desktop with singularity) slurm/singularity
