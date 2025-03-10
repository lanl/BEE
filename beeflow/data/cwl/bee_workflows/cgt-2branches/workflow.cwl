#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
inputs:
  input_file: File
  word0: string
  word1: string
  tarball_fname: string
  input_file2: File
  word2: string
  word3: string
  tarball_fname2: string

outputs:
  tarball:
    type: File
    outputSource: tar/tarball
  cat_stderr:
    type: File
    outputSource: cat/cat_stderr
  cat_stderr2:
    type: File
    outputSource: cat2/cat_stderr2
  tarball2:
    type: File
    outputSource: tar2/tarball2

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
  cat2:
    run: cat2.cwl
    in:
      input_file2: input_file2
    out: [contents,cat_stderr2]
  grep2:
    run: grep2.cwl
    in:
      word: word2
      text_file: cat2/contents
    out: [occur]
  grep3:
    run: grep3.cwl
    in:
      word: word3
      text_file: cat2/contents
    out: [occur]
  tar2:
    run: tar2.cwl
    in:
      file2: grep2/occur
      file3: grep3/occur
      tarball_fname2: tarball_fname2
    out: [tarball2]

