# CLAMR - FFMPEG workflow using CWL

clamr_wf.cwl - the main cwl.
calmr_job.yml - yaml file for values used by the cwl files.
clamr.cwl - cwl file for the clamr step.
ffmpeg.cwl - cwl file for the ffmpeg step.

The values in these files run on fog a LANL cluster, using the container runtime Charliecloud. Fog uses slurm as the workload scheduler.


