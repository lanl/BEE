#!/bin/bash
# Checkpoint test script for continue_file mode
# This script is embedded as a pre-script in the CWL workflow

set -e

# Hardcoded values for continue_file mode
CHECKPOINT_DIR="checkpoint_output_continue_file"
ITERATIONS=3
RESTART_FILE=""
SENTINEL_MODE="continue_file"
RESTART_COUNT=0

# Parse command-line arguments (for -R restart parameter)
while getopts "R:i:s:c:" opt; do
  case $opt in
    R)
      RESTART_FILE="$OPTARG"
      ;;
    i)
      ITERATIONS="$OPTARG"
      ;;
    s)
      SENTINEL_MODE="$OPTARG"
      ;;
    c)
      CHECKPOINT_DIR="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Create checkpoint directory if it doesn't exist
mkdir -p "$CHECKPOINT_DIR"

# Determine starting iteration and restart count
START_ITER=0

# Track restarts using a counter file in the checkpoint directory
# This file will be preserved by BEE along with checkpoint files
COUNTER_FILE="$CHECKPOINT_DIR/restart_count.txt"

if [ -f "$COUNTER_FILE" ]; then
  RESTART_COUNT=$(cat "$COUNTER_FILE")
  # Increment for this restart
  RESTART_COUNT=$((RESTART_COUNT + 1))
  echo "$RESTART_COUNT" > "$COUNTER_FILE"
else
  # First run - initialize counter
  RESTART_COUNT=0
  echo "0" > "$COUNTER_FILE"
fi

if [ -n "$RESTART_FILE" ]; then
  echo "Restarting from checkpoint: $RESTART_FILE"
  # Extract iteration number from checkpoint filename (e.g., backup001.crx -> 1)
  if [[ "$RESTART_FILE" =~ backup([0-9]+)\.crx ]]; then
    START_ITER=${BASH_REMATCH[1]}
    # Remove leading zeros
    START_ITER=$((10#$START_ITER))
    echo "Resuming from iteration $START_ITER"
  fi
  echo "This is restart attempt: $((RESTART_COUNT + 1))"
else
  if [ "$RESTART_COUNT" -eq 0 ]; then
    echo "Initial run at $(date)"
  else
    echo "Restart run at $(date) (attempt $((RESTART_COUNT + 1)))"
  fi
fi

# Main simulation loop
for ((i=START_ITER; i<ITERATIONS; i++)); do
  echo "Running iteration $i of $ITERATIONS"

  # Simulate some work
  sleep 2

  # Create checkpoint file with zero-padded iteration number
  CHECKPOINT_FILE="$CHECKPOINT_DIR/backup$(printf "%03d" $i).crx"
  echo "Checkpoint at iteration $i created at $(date)" > "$CHECKPOINT_FILE"
  echo "Created checkpoint: $CHECKPOINT_FILE"
done

echo "Completed all $ITERATIONS iterations"

# Handle sentinel file based on mode
case "$SENTINEL_MODE" in
  continue_file)
    # Mode 1: Create a "continue.file" to indicate more work needed
    # This tests restart_on_file_exists: true
    # If we've done fewer than 2 restarts, create the file to trigger another restart
    if [ "$RESTART_COUNT" -lt 2 ]; then
      touch continue.file
      echo "Created continue.file - task should restart (attempt $((RESTART_COUNT + 1)) of 2)"
    else
      # Remove the file if it exists, indicating work is complete
      rm -f continue.file
      echo "Removed continue.file - no more restarts needed"
    fi
    ;;

  done_marker)
    # Mode 2: Only create "done.marker" when truly finished
    # This tests restart_on_file_exists: false
    # (restart when file does NOT exist)
    if [ "$RESTART_COUNT" -lt 2 ]; then
      # Don't create done marker yet - this will trigger restart
      rm -f done.marker
      echo "done.marker not created - task should restart (attempt $((RESTART_COUNT + 1)) of 2)"
    else
      # Create the done marker to prevent further restarts
      touch done.marker
      echo "Created done.marker - no more restarts needed"
    fi
    ;;

  *)
    echo "Unknown sentinel mode: $SENTINEL_MODE" >&2
    exit 1
    ;;
esac

# Create final output file to verify task completed successfully
echo "Task completed successfully after $((RESTART_COUNT + 1)) attempts" > final_output.txt
echo "Sentinel mode: $SENTINEL_MODE" >> final_output.txt
echo "Total iterations completed: $ITERATIONS" >> final_output.txt

# Create a marker file for workflow output
echo "Completed at $(date) after $((RESTART_COUNT + 1)) attempts" > restart_marker_0.txt

exit 0
