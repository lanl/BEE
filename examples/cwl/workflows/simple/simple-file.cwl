# -*- mode: yaml; -*-

# PATH=$PATH:$PWD cwltool simple-file.cwl --infile input.txt --s1outfile s1out.txt
# rm s1out.txt

class: Workflow
cwlVersion: v1.0

requirements:
  InlineJavascriptRequirement: {}

inputs:
  infile: File
  s1outfile: string

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
        s1outfile:
          type: string
          inputBinding: {position: 2}
      outputs:
        outfile:
          type: File
          outputBinding:
            glob: $(inputs.s1outfile)   # could also be "*" without JavaScript
      baseCommand: cp-file-file.py
    in:
      infile: infile
      s1outfile: s1outfile
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
