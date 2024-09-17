"""Flux worker interface."""

import io
import os
from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import Worker

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
        import flux   # noqa this is necessary since flux may not be installed
        from flux import job  # noqa
        self.flux = flux
        self.job = job

    def build_text(self, task):
        """Build text for task script."""
        # TODO: Not used for the Flux worker

    def build_jobspec(self, task):
        """Build the job spec for a task."""
        # TODO: This has a lot of code in common with the other worker's build_text
        crt_res = self.crt.run_text(task)
        shell = task.get_requirement('beeflow:ScriptRequirement', 'shell', default='/bin/bash')
        script = [
            f'#!{shell}',
        ]

        if shell == "/bin/bash":
            script.append('set -e')
        script.append(crt_res.env_code)

        # TODO: Should this entire model, saving stdout and stderr to files, be
        # redone for Flux? It seems to provide some sort of KVS for storing
        # output but I don't quite understand it.

        # Get resource requirements
        nodes = task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)
        # TODO: 'ntasks' may not mean the same thing as with Slurm
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=nodes)
        # TODO: What to do with the MPI version?
        # mpi_version = task.get_requirement('beeflow:MPIRequirement', 'mpiVersion',
        #                                    default='pmi2')
        scripts_enabled = task.get_requirement('beeflow:ScriptRequirement', 'enabled',
                                               default=False)
        if scripts_enabled:
            # We use StringIO here to properly break the script up into lines with readlines
            pre_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                     'pre_script')).readlines()
            post_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                      'post_script')).readlines()

        # Pre commands
        if scripts_enabled:
            for cmd in pre_script:
                script.append(cmd)

        for cmd in crt_res.pre_commands:
            if cmd.type == 'one-per-node':
                cmd_args = ['flux', 'run', '-N', str(nodes), '-n', str(nodes), ' '.join(cmd.args)]
            else:
                cmd_args = ['flux', 'run', ' '.join(cmd.args)]
            script.append(' '.join(cmd_args))

        # Main command
        args = ['flux', 'run', '-N', str(nodes), '-n', str(ntasks)]
        if task.stdout is not None:
            args.extend(['--output', task.stdout])
        if task.stderr is not None:
            args.extend(['--error', task.stderr])
        args.extend(crt_res.main_command.args)
        log.info(args)
        script.append(' '.join(args))

        # Post commands
        for cmd in crt_res.post_commands:
            if cmd.type == 'one-per-node':
                cmd_args = ['flux', 'run', '-N', str(nodes), '-n', str(nodes), ' '.join(cmd.args)]
            else:
                cmd_args = ['flux', 'run', ' '.join(cmd.args)]
            script.append(' '.join(cmd_args))

        if scripts_enabled:
            for cmd in post_script:
                script.append(cmd)

        script = '\n'.join(script)
        jobspec = self.job.JobspecV1.from_batch_command(script, task.name,
                                                        num_slots=ntasks,
                                                        num_nodes=nodes)
        task_save_path = self.task_save_path(task)
        jobspec.stdout = f'{task_save_path}/{task.name}-{task.id}.out'
        jobspec.stderr = f'{task_save_path}/{task.name}-{task.id}.err'
        jobspec.environment = dict(os.environ)
        # Save the script for later reference
        with open(f'{task_save_path}/{task.name}-{task.id}.sh', 'w', encoding='utf-8') as f_path:
            f_path.write(script)
        return jobspec

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state."""
        log.info(f'Submitting task: {task.name}')
        jobspec = self.build_jobspec(task)
        flux = self.flux.Flux()
        job_id = self.job.submit(flux, jobspec)
        return job_id, self.query_task(job_id)

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state."""
        log.info(f'Cancelling task with ID: {job_id}')
        flux = self.flux.Flux()
        self.job.cancel(flux, job_id)
        return 'CANCELED'

    def query_task(self, job_id):
        """Query job state for the task."""
        # TODO: How does Flux handle TIMEOUT/TIMELIMIT? They don't seem to have
        # a state for this
        log.info(f'Querying task with job_id: {job_id}')
        flux = self.flux.Flux()
        info = self.job.get_job(flux, job_id)
        log.info(info)

        # TODO: May need to check for return codes other than 0 if
        # specified by the task (although I'm not sure how we can keep
        # track of this with job ID alone)

        # Note: using 'status' here instead of 'state'
        return BEE_STATES[info['status']]
# Ignoring W0511: TODO's are needed here to indicate parts of the code that may
#                 need more work or thought
# pylama:ignore=W0511
