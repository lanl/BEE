cwlVersion: v1.0
class: Workflow

inputs:
  input_deck: File

outputs:
  config_file:
    type: File
    outputSource: sim_runner_setup/config_file
  setup_stdout:
    type: File
    outputSource: sim_runner_setup/setup_stdout
  run_stdout:
    type: File
    outputSource: sim_runner_run/run_stdout

steps:
  sim_runner_setup:
    run:
      class: CommandLineTool
      baseCommand: ./sim_runner setup
      stdout: sim_runner_setup.out
      stderr: sim_runner_setup.err
      inputs:
        input_deck:
          type: File
          inputBinding:
            position: 1
      outputs:
        config_file:
          type: File
          outputBinding:
            glob: conf.json
        setup_stdout:
          type: File
          outputBinding:
            glob: sim_runner_setup.out
    in:
      input_deck: input_deck
    out: [config_file, setup_stdout]
    hints:
      beeflow:MPIRequirement:
        nodes: 1
        ntasks: 1
      beeflow:SlurmRequirement:
        timeLimit: 00:30:00
      beeflow:ScriptRequirement:
        pre_script: load_env.sh
        enabled: true
        shell: /bin/bash
  sim_runner_run:
    run:
      class: CommandLineTool
      baseCommand: ./sim_runner run
      stdout: sim_runner_run.out
      stderr: sim_runner_run.err
      inputs:
        config_file:
          type: File
      outputs:
        run_stdout:
          type: File
          outputBinding:
            glob: sim_runner_run.out
    in:
      config_file: sim_runner_setup/config_file
    out: [run_stdout]
    hints:
      beeflow:MPIRequirement:
        load_from_file: config_file
      beeflow:SlurmRequirement:
        timeLimit: 00:30:00
      beeflow:ScriptRequirement:
        pre_script: load_env.sh
        enabled: true
        shell: /bin/bash

