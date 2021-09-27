# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

# Script has to be discoverable in PATH
# TODO try removing brackets
baseCommand: [./mv_script.sh]
# Matches output with stdout
# Not currently capturing 
# TODO
# cwl.output.json is a special file
stdout: cwl.output.json
inputs:
  script_input:
    type: Directory
    # TODO Position probably not needed since it's the only argument
    inputBinding:
      position: 1

outputs:
  # Output is stdout variable
  # Create json string in mv_script.sh
  # javascript workaround
  # /w javascript the ffmpeg step would have
  # $(self.ffmpeg-input + /graph%05d.png)
  stdout:
    type: string
