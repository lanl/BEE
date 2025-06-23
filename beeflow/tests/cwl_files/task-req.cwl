cwlVersion: v1.0
class: Workflow

inputs:
  input_file: File
  word: string

outputs:
  cat_stderr:
    type: File
    outputSource: cat/cat_stderr

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
    hints:
      beeflow:TaskRequirement:
        workdir: cat_workdir
  grep:
    run:
      class: CommandLineTool
      baseCommand: grep
      stdout: occur.txt
      inputs:
        word:
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
      word: word
      text_file: cat/contents
    out: [occur]

