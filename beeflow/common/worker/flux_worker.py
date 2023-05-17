"""Flux worker interface."""

import os
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)

log = bee_logging.setup(__name__)

# Map from flux states to BEE statuses
BEE_STATES = {
    'NEW': 'PENDING',
    'DEPEND': 'PENDING',
    'PRIORITY': 'PENDING',
    'SCHED': 'PENDING',
    'RUN': 'RUNNING',
    'CLEANUP': 'COMPLETING',
    'INACTIVE': 'COMPLETED',
    'COMPLETED': 'COMPLETED',
    'FAILED': 'FAILED',
    'CANCELED': 'CANCELED',
    'TIMEOUT': 'TIMEOUT',
}


class FluxWorker(Worker):
    """Flux worker code."""

    def __init__(self, **kwargs):
        """Initialize the flux worker object."""
        super().__init__(**kwargs)
        # Only try to import the Flux API if we need it
        import flux
        from flux import job
        self.flux = flux
        self.job = job

    def build_text(self, task):
        """Build text for task script."""
        # TODO: Not used for the Flux worker

    def build_jobspec(self, task):
        """Build the job spec for a task."""
        # TODO: This has a lot of code in common with the other worker's build_text
        crt_res = self.crt.run_text(task)
        script = [
            '#!/bin/bash',
            'set -e',
            'env',
            'source ~/.bashrc',
            'env',
            crt_res.env_code,
        ]
        # TODO: This doesn't handle MPI jobs yet
        # TODO: Should this entire model, saving stdout and stderr to files, be
        # redone for Flux? It seems to provide some sort of KVS for storing
        # output but I don't quite understand it.
        for cmd in crt_res.pre_commands:
            script.append(' '.join(cmd.args))
        # Get resource requirements
        nodes = task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)
        # TODO: 'ntasks' may not mean the same thing as with Slurm
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=1)
        # TODO: What to do with the MPI version?
        mpi_version = task.get_requirement('beeflow:MPIRequirement', 'mpiVersion', default='pmi2')
        # Set up the main command
        args = ['flux', 'run', '-N', str(nodes), '-n', str(ntasks)]
        if task.stdout is not None:
            args.extend(['--output', task.stdout])
        if task.stderr is not None:
            args.extend(['--error', task.stderr])
        args.extend(crt_res.main_command.args)
        log.info(args)
        # script.append(' '.join(crt_res.main_command.args))
        script.append(' '.join(args))
        for cmd in crt_res.post_commands:
            script.append(' '.join(cmd.args))
        script = '\n'.join(script)
        jobspec = self.job.JobspecV1.from_batch_command(script, task.name,
                                                        num_slots=ntasks,
                                                        num_nodes=nodes)
        task_save_path = self.task_save_path(task)
        jobspec.stdout = f'{task_save_path}/{task.name}-{task.id}.out'
        jobspec.stderr = f'{task_save_path}/{task.name}-{task.id}.err'
        jobspec.environment = dict(os.environ)
        # Save the script for later reference
        with open(f'{task_save_path}/{task.name}-{task.id}.sh', 'w') as fp:
            fp.write(script)
        return jobspec

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state."""
        log.info(f'Submitting task: {task.name}')
        jobspec = self.build_jobspec(task)
        f = self.flux.Flux()
        job_id = self.job.submit(f, jobspec)
        return job_id, self.query_task(job_id)

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state."""
        log.info(f'Cancelling task with ID: {job_id}')
        f = self.flux.Flux()
        self.job.cancel(f, job_id)
        return 'CANCELED'

    def query_task(self, job_id):
        """Query job state for the task."""
        # TODO: How does Flux handle TIMEOUT/TIMELIMIT? They don't seem to have
        # a state for this
        log.info(f'Querying task with job_id: {job_id}')
        f = self.flux.Flux()
        info = self.job.get_job(f, job_id)
        log.info(info)

        # TODO: May need to check for return codes other than 0 if
        # specified by the task (although I'm not sure how we can keep
        # track of this with job ID alone)

        # Note: using 'status' here instead of 'state'
        return BEE_STATES[info['status']]
