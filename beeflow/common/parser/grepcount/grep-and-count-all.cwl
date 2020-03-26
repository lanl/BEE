# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  pattern: string
  infile: File

outputs:
  grep_file:
    type: File
    outputSource: grep/outfile
  count_file:
    type: File
    outputSource: wc/outfile

steps:
  grep:
    run:
      class: CommandLineTool
      inputs:
        pattern:
          type: string
          inputBinding: {position: 0}
        infile:
          type: File
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: grepout.txt
      baseCommand: grep
    in:
      pattern: pattern
      infile: infile
    out: [outfile]

  wc:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: counts.txt
      baseCommand: [wc, -l]
    in:
      infile: grep/outfile
    out: [outfile]
