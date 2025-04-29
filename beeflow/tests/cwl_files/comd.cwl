cwlVersion: v1.0
class: Workflow

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
      baseCommand: /CoMD/bin/CoMD-mpi -e
      stdout: comd.txt
      stderr: comd.err
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
          type: File
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
      beeflow:MPIRequirement:
        nodes: 4
        ntasks: 8
      beeflow:ScriptRequirement:
        pre_script: comd_pre.sh
        enabled: true
        shell: /bin/bash
      beeflow:SlurmRequirement:
        timeLimit: 500
      DockerRequirement:
        dockerFile: Dockerfile.comd-x86_64
        beeflow:containerName: comd-mpi

