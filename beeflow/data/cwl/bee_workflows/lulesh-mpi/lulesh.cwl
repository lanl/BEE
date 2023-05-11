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
    run:
      class: CommandLineTool
      baseCommand: [/lulesh2.0]
      stdout: lulesh_stdout.txt
      inputs:
        size:
          type: int
          inputBinding:
            prefix: -s
        iterations:
          type: int
          inputBinding:
            prefix: -i
      outputs:
        lulesh_stdout:
          type: stdout
    in:
      size: size
      iterations: iterations
    out: [lulesh_stdout]
    hints:
      DockerRequirement:
        beeflow:useContainer: /usr/projects/beedev/mpi/lulesh-x86_64.tgz
        # dockerPull: "jtronge/lulesh"
        # See Dockerfile.lulesh-x86_64
      beeflow:MPIRequirement:
        ntasks: 27
