cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python", "/home/bee/cwl2/read_dataset.py"]

inputs:
  x:
    type: string
    inputBinding:
      position: 1

stdout: output_read_dataset.txt

outputs:
  answer:
    type: stdout
