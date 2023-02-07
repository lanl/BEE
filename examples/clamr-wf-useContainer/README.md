# CLAMR - FFMPEG workflow using CWL

clamr_wf.cwl - the main cwl.
calmr_job.yml - yaml file for values used by the cwl files.
clamr.cwl - cwl file for the clamr step.
ffmpeg.cwl - cwl file for the ffmpeg step.

This workflow uses a container already built and available on LANL systems.
in the /usr/projects/BEE/clamr directory.
The container has clamr and ffmpeg executables so no need to have either installed on the system.

