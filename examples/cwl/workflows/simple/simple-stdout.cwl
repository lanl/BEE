# -*- mode: yaml; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  infile: File

outputs:
  step1_file:
    type: File
    outputSource: step1/outfile
  step2_file:
    type: File
    outputSource: step2/outfile

steps:
  step1:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: step1.txt
      baseCommand: cp-file-stdout.py
    in:
      infile: infile
    out: [outfile]

  step2:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: step2.txt
      baseCommand: cp-file-stdout.py
    in:
      infile: step1/outfile
    out: [outfile]
