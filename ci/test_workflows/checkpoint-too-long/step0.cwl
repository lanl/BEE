class: CommandLineTool
cwlVersion: v1.0

baseCommand: /usr/bin/checkpoint-program
stdout: checkpoint_stdout.txt
inputs:
  fake_input:
    type: int?
    inputBinding:
      prefix: -f
outputs:
  step0_output:
    type: stdout
