class: Workflow
cwlVersion: v1.0

# Test workflow for sentinel file-based checkpoint/restart functionality
# Tests two scenarios:
# 1. continue_file: restart when sentinel file EXISTS (restart_on_file_exists: true)
# 2. done_marker: restart when sentinel file DOES NOT exist (restart_on_file_exists: false)

inputs:
  iterations: int
  checkpoint_dir: string

outputs:
  # Outputs from continue_file test
  continue_file_stdout:
    type: File
    outputSource: test_continue_file/step_stdout
  continue_file_output:
    type: File
    outputSource: test_continue_file/final_output
  continue_file_restart_markers:
    type: File
    outputSource: test_continue_file/restart_markers

  # Outputs from done_marker test
  done_marker_stdout:
    type: File
    outputSource: test_done_marker/step_stdout
  done_marker_output:
    type: File
    outputSource: test_done_marker/final_output
  done_marker_restart_markers:
    type: File
    outputSource: test_done_marker/restart_markers

steps:
  # Test 1: Restart when sentinel file EXISTS (continue.file)
  # This simulates applications that create a file when they need to continue
  test_continue_file:
    run: step_continue_file.cwl
    in:
      iterations: iterations
      checkpoint_dir: checkpoint_dir
    out: [step_stdout, final_output, checkpoint_files, restart_markers]
    hints:
      beeflow:CheckpointRequirement:
        enabled: true
        checkpoint_dir: checkpoint_output_continue_file
        file_regex: (backup[0-9]*.crx|restart_count.txt)
        restart_parameters: -R
        num_tries: 3
        sentinel_file_path: continue.file
        restart_on_file_exists: true
        restart_on_failure: false
      beeflow:SlurmRequirement:
        timeLimit: 00:02:00

  # Test 2: Restart when sentinel file DOES NOT exist (done.marker)
  # This simulates applications that only create a marker file when complete
  test_done_marker:
    run: step_done_marker.cwl
    in:
      iterations: iterations
      checkpoint_dir: checkpoint_dir
    out: [step_stdout, final_output, checkpoint_files, restart_markers]
    hints:
      beeflow:CheckpointRequirement:
        enabled: true
        checkpoint_dir: checkpoint_output_done_marker
        file_regex: (backup[0-9]*.crx|restart_count.txt)
        restart_parameters: -R
        num_tries: 3
        sentinel_file_path: done.marker
        restart_on_file_exists: false
        restart_on_failure: false
      beeflow:SlurmRequirement:
        timeLimit: 00:02:00
