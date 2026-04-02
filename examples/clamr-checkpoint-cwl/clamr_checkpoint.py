"""Clamr driver for CWL generator."""

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
    ffmpeg_task = Task(
        name="ffmpeg",
        base_command="ffmpeg -y",
        stdout="ffmpeg.txt",
        stderr="ffmpeg.err",
        inputs=[
            Input("input_format", "string", "image2", prefix="-f", position=1),
            Input(
                "ffmpeg_input",
                "Directory",
                value="clamr/outdir",
                prefix="-i",
                position=2,
                value_from='$("/graph%05d.png")',
            ),
            Input("frame_rate", "int", 12, prefix="-r", position=3),
            Input("frame_size", "string", "800x800", prefix="-s", position=4),
            Input("pixel_format", "string", "yuv420p", prefix="-pix_fmt", position=5),
            Input("output_filename", "string", "CLAMR_movie.mp4", position=6),
        ],
        outputs=[
            Output(
                "clamr_movie",
                "File",
                source="ffmpeg/movie",
                glob="$(inputs.output_file)",
            ),
            Output("ffmpeg_stderr", "stderr", source="ffmpeg/ffmpeg_stderr"),
        ],
        hints=[
            Charliecloud(
                docker_file="Dockerfile.clamr-ffmpeg", container_name="clamr-ffmpeg"
            )
        ],
    )
    workflow = Workflow("clamr", [clamr_task, ffmpeg_task])
    workflow.dump_wf(".")
    workflow.dump_yaml(".")


if __name__ == "__main__":
    main()
