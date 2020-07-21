#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

inputs:
  message: string

baseCommand: ["python", "script.py"]

requirements:
  InitialWorkDirRequirement:
    listing:
      - entryname: script.py
        entry: |-
          model = pickle.load(open('model.pkl','rb'))
          print(model.predict([[2, 9, 6]]))

outputs:
  example_out:
    type: stdout
stdout: output.txt
