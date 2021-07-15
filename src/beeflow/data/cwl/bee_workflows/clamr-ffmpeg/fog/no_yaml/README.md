# CLAMR-FFMPEG WORKFLOW (Fog)

This workflow executes the `CLAMR` AMR simulation and then runs `ffmpeg`, represented in a single CWL file.

Files:
* cf.cwl - clamr CWL file
* cf-noow.cwl - clamr CWL file no overwrite, ffmpeg to fails if movie file exists, useful to test FAILED step.
