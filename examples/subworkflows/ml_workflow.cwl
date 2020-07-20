#!/usr/bin/env cwl-runner
id: ml_workflow
label: ml_workflow
class: Workflow
cwlVersion: v1.0
class: CommandLineTool
baseCommand: python

inputs:
  id:train.csv
  type: File
  inputBinding: 
    position:1
  default:
    class: File
    location:/train.csv
    
    
  id:model.py
    type: File
    inputBinding:
        position: 2
    default:
      class: File
      location:/model.py

  id:app.py
    type: File
    inputBinding: 
        position: 3
    default:
      class: File
      location: /app.py

arguments:
    -coeff
    position:1
 
outputs:
  out:
    type:
      type: String
      items: File
      outputSource: result_out
      
