#!/usr/bin/env python3

from beeflow.common.cwl.workflow import Task, Input, Output, MPI, Workflow, Slurm, Script

def main():
    sim_runner_setup = Task(
        name="sim_runner_setup",
        base_command="./sim_runner setup",
        stdout="sim_runner_setup.out",
        stderr="sim_runner_setup.err",
        inputs=[Input("input_deck", "File", value="input.text", position=1)],
        outputs=[
            Output("config_file", "File", source="sim_runner_setup/config_file",
                   glob="conf.json"),
            Output("setup_stdout", "File", source="sim_runner_setup/setup_stdout",
                   glob="sim_runner_setup.out"),
        ],
        hints=[MPI(nodes=1, ntasks=1), Slurm(time_limit="00:30:00"),
               Script(pre_script="load_env.sh", enabled=True, shell="/bin/bash")],
    )

    sim_runner_run = Task(
        name="sim_runner_run",
        base_command="./sim_runner run",
        stdout="sim_runner_run.out",
        stderr="sim_runner_run.err",
        inputs=[
            Input("config_file", "File", value="sim_runner_setup/config_file")
        ],
        outputs=[
            Output("run_stdout", "File", source="sim_runner_run/run_stdout",
                   glob="sim_runner_run.out")
        ],
        hints=[MPI(load_from_file="config_file"), Slurm(time_limit="00:30:00"),
               Script(pre_script="load_env.sh", enabled=True, shell="/bin/bash")]
    )

    wf = Workflow("sim_runner_wf", [sim_runner_setup, sim_runner_run])
    wf.dump_wf(".")
    wf.dump_yaml(".")

if __name__ == "__main__":
    main()

