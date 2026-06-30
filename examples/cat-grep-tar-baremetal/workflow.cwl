#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
inputs:
  input_file: File
  word0: string
  word1: string
  tarball_fname: string

outputs:
  tarball:
    type: File
    outputSource: tar/tarball
  cat_stderr:
    type: File
    outputSource: cat/cat_stderr

steps:
  cat:
    run: cat.cwl
    in:
      input_file: input_file
    out: [contents, cat_stderr]
  grep0:
    run: grep0.cwl
    in:
      word: word0
      text_file: cat/contents
    out: [occur]
  grep1:
    run: grep1.cwl
    in:
      word: word1
      text_file: cat/contents
    out: [occur]
  tar:
    run: tar.cwl
    in:
      file0: grep0/occur
      file1: grep1/occur
      tarball_fname: tarball_fname
    out: [tarball]
