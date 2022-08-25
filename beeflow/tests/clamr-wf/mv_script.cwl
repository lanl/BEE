# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

# Script has to be discoverable in PATH
baseCommand: [mv_script.sh]
stdout: cwl.output.json
inputs:
  script_input:
    type: Directory
    inputBinding:
      position: 1

outputs:
  stdout:
    type: string
