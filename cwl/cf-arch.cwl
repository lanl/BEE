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
          default: src/beeflow/data/lorem.txt
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: graphics_output
      # baseCommand: "/clamr/CLAMR-master/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png"
      baseCommand: "/CLAMR/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png"
      hints:
        DockerRequirement:
          # dockerImageId: "/home/cc/clamr.tar.gz"
          dockerImageId: "/home/jaket/bee/img/clamr.tar.gz"
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
      hints:
        DockerRequirement:
          dockerImageId: "/home/jaket/bee/img/ffmpeg.tar.gz"
    in:
      infile: clamr/outfile
    out: [outfile]
