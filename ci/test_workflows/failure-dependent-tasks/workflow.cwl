cwlVersion: v1.2
class: Workflow

inputs:
  fname: File
  cat_argument: string

outputs:
  fail_stdout:
    type: File
    outputSource: fail/fail_stdout
  dependent0_stdout:
    type: File
    outputSource: dependent0/dependent_stdout
  dependent1_stdout:
    type: File
    outputSource: dependent1/dependent_stdout
  dependent2_stdout:
    type: File
    outputSource: dependent2/dependent_stdout

steps:
  fail:
    run:
      class: CommandLineTool
      baseCommand: [ls]
      stdout: fail.txt
      inputs:
        fname:
          type: File
          inputBinding:
            position: 1
      outputs:
        fail_stdout:
          type: stdout
    in:
      fname: fname
    out: [fail_stdout]
  # Two duplicate tasks that depend on the task above, which should fail and cause these to not run.
  dependent0:
    run:
      cwlVersion: v1.2
      class: CommandLineTool
      baseCommand: [cat]
      stdout: dependent.txt
      inputs:
        cat_argument:
          type: string
          inputBinding:
            position: 1
        file_to_cat:
          type: File
          inputBinding:
            position: 1
      outputs:
        dependent_stdout:
          type: stdout
    in:
      file_to_cat: fail/fail_stdout
      cat_argument: cat_argument
    out: [dependent_stdout]
  dependent1:
    run:
      cwlVersion: v1.2
      class: CommandLineTool
      baseCommand: [cat]
      stdout: dependent1.txt
      inputs:
        cat_argument:
          type: string
          inputBinding:
            position: 1
        file_to_cat:
          type: File
          inputBinding:
            position: 2
      outputs:
        dependent_stdout:
          type: stdout
    in:
      cat_argument: cat_argument
      file_to_cat: fail/fail_stdout
    out: [dependent_stdout]
  dependent2:
    run:
      cwlVersion: v1.2
      class: CommandLineTool
      baseCommand: [cat]
      stdout: dependent1.txt
      inputs:
        cat_argument:
          type: string
          inputBinding:
            position: 1
        file_to_cat:
          type: File
          inputBinding:
            position: 2
      outputs:
        dependent_stdout:
          type: stdout
    in:
      cat_argument: cat_argument
      file_to_cat: dependent1/dependent_stdout
    out: [dependent_stdout]
