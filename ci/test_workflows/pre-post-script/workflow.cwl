class: Workflow
cwlVersion: v1.0

inputs:
  sleep_time: int

outputs:
  step0_stdout:
    type: File
    outputSource: step0/step0_stdout

steps:
  step0:
    run:
      class: CommandLineTool
      baseCommand: sleep
      stdout: step0_stdout.txt
      inputs:
        sleep_time:
          type: int
          inputBinding:
            position: 0
      outputs:
        step0_stdout:
          type: stdout
    in:
      sleep_time: sleep_time
    out: [step0_stdout]
    hints:
      beeflow:ScriptRequirement:
        enabled: true
        pre_script: "pre.sh"
        post_script: "post.sh"
