# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.2

baseCommand: /makeflow-examples/blast/blastall

stderr: fasta.0.err

inputs:
  program_name:
    type: string
    inputBinding:
      prefix: -p
  database:
    type: string
    inputBinding:
      prefix: -d
  input_file:
    type: File
    inputBinding:
      prefix: -i
  output_file:
    type: string
    inputBinding:
      prefix: -o


outputs:
  output:
    type: File
    outputBinding:
      glob: fasta.0.out
# Was glob: $(inputs.output_file) but fails

  output_err:
    type: stderr
