# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  infile:
    type: File
    default: 'infile'

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
          default: lorem.txt
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: graphics_output
      baseCommand: "/clamr/CLAMR-master/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png"
      hints:
        DockerRequirement:
          dockerImageId: "/usr/projects/beedev/clamr/clamr-toss.tar.gz"
    in:
      infile: infile
    out: [outfile]

  ffmpeg:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          default: graphics_output
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: CLAMR_movie.mp4
      baseCommand: "ffmpeg -f image2 -i $HOME/graphics_output/graph%05d.png -r 12 -s 800x800 -pix_fmt yuv420p $HOME/CLAMR_movie.mp4"
    in:
      infile: clamr/outfile
    out: [outfile]
