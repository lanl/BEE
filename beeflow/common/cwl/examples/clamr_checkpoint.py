"""COMD driver for CWL generator."""

import pathlib
from beeflow.common.cwl.workflow import (
    Task,
    Input,
    Output,
    MPI,
    Charliecloud,
    Workflow,
    Slurm,
    Script,
    Checkpoint,
)


def main():
    clamr_task = Task(
        name="clamr",
        base_command="/CLAMR/clamr_cpuonly",
        stdout="clamr.txt",
        stderr="clamr.err",
        inputs=[
            Input("max_levels", "int", 3, prefix="-l"),
            Input("grid_resolution", "int", 32, prefix="-n"),
            Input("steps_between_output", "int", 10, prefix="-i"),
            Input("steps_between_graphics", "int", 25, prefix="-g"),
            Input("time_steps", "int", 10000, prefix="-t"),
            Input("graphics_type", "string", "png", prefix="-G"),
            Input("checkpoint_disk_interval", "int", 50, prefix="-c"),
        ],
        outputs=[
            Output("clamr_stdout", "File", source="clamr/clamr_stdout"),
            Output("outdir", "Directory", glob="graphics_output/graph%05d.png"),
            Output(
                "checkpoint_dir", "Directory", glob="checkpoint_output/backup%05d.crx"
            ),
            Output(
                "clamr_time_log",
                "File",
                source="clamr/time_log",
                glob="total_execution_time.log",
            ),
        ],
        hints=[
            Checkpoint(
                enabled=True,
                file_path="checkpoint_output",
                container_path="checkpoint_output",
                file_regex="backup[0-9]*.crx",
                restart_parameters="-R",
                num_tries=3,
            ),
            Slurm(time_limit="00:00:10"),
            Charliecloud(
                docker_file="Dockerfile.clamr-ffmpeg", container_name="clamr-ffmpeg"
            ),
        ],
    )
    workflow = Workflow("clamr", [clamr_task])
    workflow.write_wf("clamr")
    workflow.write_yaml("clamr")


if __name__ == "__main__":
    main()
