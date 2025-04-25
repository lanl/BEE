cwlVersion: v1.0
class: Workflow

inputs:
  input_file: File
  word0: string
  word1: string
  tarball_fname: string

outputs:
  cat_stderr:
    type: File
    outputSource: cat/cat_stderr
  tarball:
    type: File
    outputSource: tar/tarball

steps:
  cat:
    run:
      class: CommandLineTool
      baseCommand: cat
      stdout: cat.txt
      stderr: cat.err
      inputs:
        input_file:
          type: File
          inputBinding:
            position: 1
      outputs:
        contents:
          type: stdout
        cat_stderr:
          type: stderr
    in:
      input_file: input_file
    out: [contents, cat_stderr]
  grep0:
    run:
      class: CommandLineTool
      baseCommand: grep
      stdout: occur0.txt
      inputs:
        word0:
          type: string
          inputBinding:
            position: 1
        text_file:
          type: File
          inputBinding:
            position: 2
      outputs:
        occur:
          type: stdout
    in:
      word0: word0
      text_file: cat/contents
    out: [occur]
  grep1:
    run:
      class: CommandLineTool
      baseCommand: grep
      stdout: occur1.txt
      inputs:
        word1:
          type: string
          inputBinding:
            position: 1
        text_file:
          type: File
          inputBinding:
            position: 2
      outputs:
        occur:
          type: stdout
    in:
      word1: word1
      text_file: cat/contents
    out: [occur]
  tar:
    run:
      class: CommandLineTool
      baseCommand: tar
      stdout: occur1.txt
      inputs:
        tarball_fname:
          type: string
          inputBinding:
            position: 1
            prefix: -cf
        file0:
          type: File
          inputBinding:
            position: 2
        file1:
          type: File
          inputBinding:
            position: 3
      outputs:
        tarball:
          type: File
          outputBinding:
            glob: $(inputs.tarball_fname)
    in:
      tarball_fname: tarball_fname
      file0: grep0/occur
      file1: grep1/occur
    out: [tarball]

