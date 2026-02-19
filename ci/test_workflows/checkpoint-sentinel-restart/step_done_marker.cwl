class: CommandLineTool
cwlVersion: v1.0

baseCommand: [echo, "Checkpoint test completed"]

stdout: done_marker_stdout.txt

inputs:
  iterations:
    type: int
  sentinel_mode:
    type: string
    default: "done_marker"
  checkpoint_dir:
    type: string

hints:
  beeflow:ScriptRequirement:
    enabled: true
    pre_script: "run_checkpoint_test_done_marker.sh"
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
      glob: checkpoint_output_done_marker
  restart_markers:
    type: File
    outputBinding:
      glob: restart_marker_0.txt
