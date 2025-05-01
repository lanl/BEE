cwlVersion: v1.0
class: Workflow

inputs:
  max_levels: int
  grid_resolution: int
  steps_between_output: int
  steps_between_graphics: int
  time_steps: int
  graphics_type: string
  checkpoint_disk_interval: int

outputs:
  clamr_stdout:
    type: File
    outputSource: clamr/clamr_stdout
  clamr_time_log:
    type: File
    outputSource: clamr/time_log

steps:
  clamr:
    run:
      class: CommandLineTool
      baseCommand: /CLAMR/clamr_cpuonly
      stdout: clamr.txt
      stderr: clamr.err
      inputs:
        max_levels:
          type: int
          inputBinding:
            prefix: -l
        grid_resolution:
          type: int
          inputBinding:
            prefix: -n
        steps_between_output:
          type: int
          inputBinding:
            prefix: -i
        steps_between_graphics:
          type: int
          inputBinding:
            prefix: -g
        time_steps:
          type: int
          inputBinding:
            prefix: -t
        graphics_type:
          type: string
          inputBinding:
            prefix: -G
        checkpoint_disk_interval:
          type: int
          inputBinding:
            prefix: -c
      outputs:
        clamr_stdout:
          type: File
        outdir:
          type: Directory
          outputBinding:
            glob: graphics_output/graph%05d.png
        checkpoint_dir:
          type: Directory
          outputBinding:
            glob: checkpoint_output/backup%05d.crx
        clamr_time_log:
          type: File
          outputBinding:
            glob: total_execution_time.log
    in:
      max_levels: max_levels
      grid_resolution: grid_resolution
      steps_between_output: steps_between_output
      steps_between_graphics: steps_between_graphics
      time_steps: time_steps
      graphics_type: graphics_type
      checkpoint_disk_interval: checkpoint_disk_interval
    out: [clamr_stdout, outdir, checkpoint_dir, clamr_time_log]
    hints:
      beeflow:CheckpointRequirement:
        enabled: true
        file_path: checkpoint_output
        container_path: checkpoint_output
        file_regex: backup[0-9]*.crx
        restart_parameters: -R
        num_tries: 3
      beeflow:SlurmRequirement:
        timeLimit: 00:00:10
      DockerRequirement:
        dockerFile: Dockerfile.clamr-ffmpeg
        beeflow:containerName: clamr-ffmpeg

