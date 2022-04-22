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
