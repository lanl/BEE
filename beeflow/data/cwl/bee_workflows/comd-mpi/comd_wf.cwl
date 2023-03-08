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
    run: comd.cwl
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
        beeflow:copyContainer: "/usr/projects/beedev/mpi/comd-x86_64.tgz"
        # See Dockerfile.comd-x86_64
      beeflow:MPIRequirement:
        nodes: 4
        ntasks: 8
