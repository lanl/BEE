class: Workflow
cwlVersion: v1.0

inputs:
  i: int
  j: int
  k: int
  x: int
  y: int
  z: int
  pot_dir: string

outputs:
  comd_stdout:
    type: File
    outputSource: comd/comd_stdout

steps:
  comd:
    run: comd_bin.cwl
    in:
      i: i
      j: j
      k: k
      x: x
      y: y
      z: z
      pot_dir: pot_dir
    out: [comd_stdout]
    hints:
      DockerRequirement:
        # dockerPull: "jtronge/comd:latest"
        beeflow:copyContainer: "/usr/projects/beedev/comd/comd-x86_64.tar.gz"
      beeflow:MPIRequirement:
        nodes: 8
        ntasks: 8
