#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow
inputs:
  num1: int
  num2: int
outputs:
  final_answer:
    outputSource: multiply/answer
    type: int
steps:
  add:
    run: /Users/raginigupta/PythonCodes/cwl/add.cwl
    in:
      x: num1
      y: num2
    out:
    - answer
  multiply:
    run: /Users/raginigupta/PythonCodes/cwl/multiply.cwl
    in:
      x: add/answer
      y: num2
    out:
    - answer
