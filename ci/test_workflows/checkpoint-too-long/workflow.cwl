# Test workflow that will run forever, causing a failure when it is restarted
# more than 'num_tries'.
class: Workflow
cwlVersion: v1.0

inputs:
  # Dummy input for the first step
  fake_input: int
outputs:
  step0_stdout:
    type: File
    outputSource: step0/step0_stdout

steps:
  step0:
    run: step0.cwl
    in:
      fake_input: fake_input
    out: [step0_output]
    hints:
      beeflow:CheckpointRequirement:
        enabled: true
        file_path: checkpoint_output
        container_path: checkpoint_output
        file_regex: backup[0-9]*.crx
        restart_parameters: -R
        num_tries: 1
      beeflow:SchedulerRequirement:
        timeLimit: 00:00:10
      DockerRequirement:
        dockerFile: "Dockerfile"
        beeflow:containerName: "checkpoint-failure"
