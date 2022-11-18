# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  infile: File

outputs:
  clamr_dir:
    type: File
    outputSource: clamr/outfile
  ffmpeg_movie:
    type: File
    outputSource: ffmpeg/outfile

steps:
  clamr:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          default: ""
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: $HOME/graphics_output
      baseCommand: "/CLAMR/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png"
      hints:
        DockerRequirement:
          dockerPull: "git.lanl.gov:5050/qwofford/containerhub/clamr-lanl-x86_64:latest"
    in:
      infile: infile
    out: [outfile]

  ffmpeg:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: CLAMR_movie.mp4
      baseCommand: "ffmpeg -y -f image2 -i $HOME/graphics_output/graph%05d.png -r 12 -s 800x800 -pix_fmt yuv420p $HOME/CLAMR_movie.mp4 && ls -ld"
      hints:
    in:
      infile: clamr/outfile
    out: [outfile]
