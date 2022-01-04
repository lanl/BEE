# CLAMR-FFMPEG WORKFLOW

This workflow executes the `CLAMR` AMR simulation and then runs `ffmpeg`, represented in a single CWL file.


* cf-summit.cwl - clamr CWL file, runs on Summit. Both steps run in a container.

Note: The ls command was added to use the output from the first step for the 2nd step.
