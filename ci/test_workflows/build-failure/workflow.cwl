# Dummy workflow designed to fail at the container build stage
class: Workflow
cwlVersion: v1.2

inputs:
  fname: string

outputs:
  step0_stdout:
    type: File
    outputSource: step0/step0_stdout

steps:
  step0:
    run:
      class: CommandLineTool
      baseCommand: ls
      stdout: step0_stdout.txt
      inputs:
        fname:
          type: string
          inputBinding: {}
      outputs:
        step0_stdout:
          type: stdout
    in:
      fname: fname
    out: [step0_stdout]
    hints:
      DockerRequirement:
        dockerFile: "Dockerfile.build-failure"
        beeflow:containerName: "build-failure"
