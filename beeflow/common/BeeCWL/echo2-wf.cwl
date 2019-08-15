#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow

requirements:
  StepInputExpressionRequirement: {}

inputs: 
   message1: string
   message2: string

outputs: []

steps:
   echo1:
     in:
       message: message1

     out: []
     run: echo.cwl

   echo2:
     in:
       message: message2

     out: []
     run: echo.cwl

