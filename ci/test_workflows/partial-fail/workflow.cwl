#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
inputs:
  source: string
  word0: string
  text_file: File

outputs:
  occur0:
    type: File
    outputSource: grep0/occur0
  occur1:
    type: File
    outputSource: grep1/occur1

steps:
  printf:
    run: printf.cwl
    in:
      source: source
    out: [contents]
  grep0:
    run: grep0.cwl
    in:
      word: word0
      text_file: printf/contents
    out: [occur0]
  cat:
    run: cat.cwl
    in:
      text_file: text_file
    out: [cat_out]
  grep1:
    run: grep1.cwl
    in:
      word: word0
      text_file: cat/cat_out
    out: [occur1]
