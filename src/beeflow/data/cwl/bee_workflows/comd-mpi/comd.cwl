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
    run:
      class: CommandLineTool
      baseCommand: [/CoMD/bin/CoMD-mpi, -e]
      stdout: comd_stdout.txt
      inputs:
        i:
          type: int
          inputBinding:
            prefix: -i
        j:
          type: int
          inputBinding:
            prefix: -j
        k:
          type: int
          inputBinding:
            prefix: -k
        x:
          type: int
          inputBinding:
            prefix: -x
        y:
          type: int
          inputBinding:
            prefix: -y
        z:
          type: int
          inputBinding:
            prefix: -z
        pot_dir:
          type: string
          inputBinding:
            prefix: --potDir
      outputs:
        comd_stdout:
          type: stdout
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
        dockerPull: "jtronge/comd:latest"
        # copyContainer: "...path to comd tarball..."
      beeflow:MPIRequirement:
        nodes: 8
        ntasks: 8
