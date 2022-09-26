# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.2

baseCommand: /bin/cat

stdout: output.fasta.err

inputs:
  input_file1:
    type: File
    inputBinding:
      position: 1
  input_file2:
    type: File
    inputBinding:
      position: 2

outputs:
  blast_output_err:
    type: stdout
