"""Flux worker interface."""

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)

log = bee_logging.setup(__name__)


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
        # TODO: This has a lot of code in command with the other worker build_text's
        crt_res = self.crt.run_text(task)
        script = [
            '#!/bin/bash',
            'set -e',
            crt_res.env_code,
        ]
        # TODO: This doesn't handle MPI jobs
        for cmd in crt_res.pre_commands:
            script.append(' '.join(cmd.args))
        script.append(' '.join(crt_res.main_command.args))
        for cmd in crt_res.post_commands:
            script.append(' '.join(cmd.args))
        return '\n'.join(script)

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state."""
        script = self.build_text(task)
        f = self.flux.Flux()
        jobspec = self.job.JobspecV1.from_batch_command(script, task.name)
        job_id = self.job.submit(f, jobspec)
        info = self.job.get_job(job_id)
        return job_id, info['state']

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state."""
        f = self.flux.Flux()
        self.job.cancel(f, job_id)

    def query_task(self, job_id):
        """Query job state for the task."""
        f = self.flux.Flux()
        return self.job.get_job(f, job_id)['state']
