# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.2

baseCommand: /makeflow-examples/blast/split_fasta

inputs:
  query_granularity: 
    type: string
    inputBinding:
      position: 1
  input_file:
    type: string
    inputBinding:
      position: 2

outputs:
  split1:
    type: File
    outputBinding:
      glob: /mnt/blast/small.fasta.0
  split2:
    type: File
    outputBinding:
      glob: /mnt/blast/small.fasta.1
