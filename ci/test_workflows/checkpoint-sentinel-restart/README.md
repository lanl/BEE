# Checkpoint Sentinel Restart Test Workflow

This test workflow validates the sentinel file-based checkpoint/restart functionality in BEE.

## Overview

The workflow tests two sentinel file scenarios:

1. **continue_file test**: Restarts when sentinel file EXISTS (`restart_on_file_exists: true`)
2. **done_marker test**: Restarts when sentinel file DOES NOT exist (`restart_on_file_exists: false`)

Both tests use `restart_on_failure: false` to test sentinel checking on COMPLETED tasks.

## Files

- `workflow.cwl` - Main workflow with two test steps
- `step_continue_file.cwl` - Step definition for continue_file test
- `step_done_marker.cwl` - Step definition for done_marker test
- `checkpoint_test.sh` - Shell script that simulates checkpoint/restart behavior
- `input.yml` - Input parameters for the workflow

## Test Script Behavior

The `checkpoint_test.sh` script:

1. Creates checkpoint files (backup000.crx, backup001.crx, etc.) at regular intervals
2. Manages sentinel files based on the test mode:
   - **continue_file mode**: Creates `continue.file` to trigger restarts (up to 2 times)
   - **done_marker mode**: Only creates `done.marker` after sufficient restarts
3. Tracks restart attempts using `restart_marker_*.txt` files
4. Creates a `final_output.txt` with completion summary

## Expected Behavior

### Test 1: continue_file

- **First run**: Creates `continue.file` → triggers restart
- **Second run (restart 1)**: Creates `continue.file` → triggers restart
- **Third run (restart 2)**: Removes `continue.file` → no more restarts
- **Expected restarts**: 2

### Test 2: done_marker

- **First run**: Does NOT create `done.marker` → triggers restart
- **Second run (restart 1)**: Does NOT create `done.marker` → triggers restart
- **Third run (restart 2)**: Creates `done.marker` → no more restarts
- **Expected restarts**: 2

## Verification

After the workflow completes, verify:

1. Both tasks complete successfully (not FAILED or DEP_FAIL)
2. Each task has 2 `restart_marker_*.txt` files (indicating 2 restarts occurred)
3. `final_output.txt` exists and indicates successful completion
4. Checkpoint files (`backup*.crx`) were created in the `checkpoint_output` directory

## Running the Test

```bash
beeflow submit -w workflow.cwl -j input.yml -N checkpoint-sentinel-test
```

## Notes

- The workflow does NOT use DockerRequirement, running directly with Slurm
- Time limit is set to 2 minutes per task (should complete in ~10 seconds per run)
- The script uses `num_tries: null` for unlimited restarts (controlled by sentinel logic)
- Sentinel file checking works with COMPLETED tasks because `restart_on_failure: false`
