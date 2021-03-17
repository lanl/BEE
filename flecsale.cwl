# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  infile: File

outputs:
  clamr_dir:
    type: File
    outputSource: flecsale_hydro_3d/outfile
  ffmpeg_movie:
    type: File
    outputSource: save/outfile

steps:
  flecsale_hydro_3d:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          default: src/beeflow/data/lorem.txt
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: shock_box_3d_*
      # TODO: Need to figure out how to specify the shock_box input in CWL
      # This should be run in /tmp
      baseCommand: "/home/flecsi/flecsale/build/apps/hydro/3d/hydro_3d -m /home/flecsi/flecsale/build/apps/hydro/3d/shock_box_3d_rank000001.000200.exo"
      hints:
        DockerRequirement:
          # dockerImageId: "/home/cc/laristra.flecsale.ubuntu_mpi_master.tar.gz"
          dockerImageId: "/home/jaket/bee/laristra.flecsale.ubuntu_mpi_master.tar.gz"
    in:
      infile: infile
    out: [outfile]

  # Save the resulting *.exo files
  save:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          default: graphics_output
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: save.tar.xz
      # TODO: This needs to be run in /tmp
      baseCommand: "cd /tmp; find . -name '*.exo' | tar -cf save.tar.xz -T -"
      hints:
    in:
      infile: flecsale_hydro_3d/outfile
    out: [outfile]

  # TODO: Perhaps need to push `save.tar.xz` up to a cloud location
