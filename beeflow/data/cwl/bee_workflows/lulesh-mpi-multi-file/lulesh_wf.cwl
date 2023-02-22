class: Workflow
cwlVersion: v1.0

inputs:
  size: int
  iterations: int

outputs:
  lulesh_stdout:
    type: File
    outputSource: lulesh/lulesh_stdout

steps:
  lulesh:
    run: lulesh.cwl
    in:
      size: size
      iterations: iterations
    out: [lulesh_stdout]
    hints:
      DockerRequirement:
        beeflow:useContainer: '/usr/projects/beedev/mpi/lulesh-x86_64.tgz'
        # See Dockerfile.lulesh-x86_64
      beeflow:MPIRequirement:
        ntasks: 27
