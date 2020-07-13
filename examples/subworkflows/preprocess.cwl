cwlVersion: v1.0
class: CommandLineTool
baseCommand: python3

inputs:
  script:
    type: File
    inputBinding:
        position: 1
    default:
      class: File
      location:train.py

  inputfile:
    type: File
    inputBinding: 
        position: 2
    default:
      class: File
      location: configuration.yml

outputs:
  out:
    type:
      type: array
      items: File
    outputBinding:
      glob: "*.dat"
