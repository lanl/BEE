class: CommandLineTool
cwlVersion: v1.0

baseCommand: [echo, "Checkpoint test completed"]

stdout: continue_flag_stdout.txt

inputs:
  iterations:
    type: int
  sentinel_mode:
    type: string
    default: "continue_flag"
  checkpoint_dir:
    type: string

hints:
  beeflow:ScriptRequirement:
    enabled: true
    pre_script: "run_checkpoint_test.sh"
    shell: "/bin/bash"

outputs:
  step_stdout:
    type: stdout
  final_output:
    type: File
    outputBinding:
      glob: final_output.txt
  checkpoint_files:
    type: Directory
    outputBinding:
      glob: checkpoint_output_continue_flag
  restart_markers:
    type: File
    outputBinding:
      glob: restart_marker_0.txt
