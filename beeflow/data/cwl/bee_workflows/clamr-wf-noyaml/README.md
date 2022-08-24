# CLAMR-FFMPEG WORKFLOW

This workflow executes the `CLAMR` AMR simulation and then runs `ffmpeg` to produce a video from the `CLAMR` output. These workflows place the command all on one line and were used early in the development of BEE, and are valid for demonstration and testing purposes. We recommend you use the workflows with yaml files as examples for scientific workflows.

The directories are organized as <workload scheduler-container runtime>.


CLAMR workflows for various systems:

* Fog (LANL system) slurm-charliecloud/cf.cwl
* Summit (ORNL system) lsf-charliecloud/cf-summit.cwl
* Darwin (LANL system) slurm-charliecloud/cf-darwin.cwl
* Case (LANL desktop with singularity) slurm-singularity/cf-singularity.cwl

There are also examples using various functions of the build interface in the slurm-charliecloud directory.
