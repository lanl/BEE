# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.2

baseCommand: /makeflow-examples/blast/cat_blast

inputs:
  output_filename:
    type: string
    inputBinding:
      position: 1
  input_file1:
    type: File
    inputBinding:
      position: 2
  input_file2:
    type: File
    inputBinding:
      position: 3

outputs:
  blast_output:
    type: File
    outputBinding:
      glob: $(inputs.output_filename)
