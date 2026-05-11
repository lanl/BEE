
"""Simple Worker class for launching tasks on a system with no workload manager."""

import signal
import subprocess

import os
from beeflow.common.worker.worker import Worker


class SimpleWorker(Worker):
    """Worker interface for system with no workload manager."""

    def __init__(self, container_runtime, **kwargs):
        """Create Simple worker object."""
        super().__init__(container_runtime=container_runtime, **kwargs)

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state, job_info.

        :param task: instance of Task
        :rtype: tuple (int, string, dict)
        """
        self.prepare(task)
        script_path = self.write_script(task)
        status_dir = os.path.join(self.workdir, 'simple_worker_status')
        os.makedirs(status_dir, exist_ok=True)
        process = subprocess.Popen([  # pylint: disable=R1732
            '/bin/sh',
            '-c',
            f'/bin/sh "{script_path}"; rc=$?; '
            f'echo "$rc" > "{status_dir}/$$.returncode"; '
            f'touch "{status_dir}/$$.done"; '
            f'exit "$rc"'
        ], start_new_session=True)
        job_id = process.pid
        job_info = {
            'scheduler': 'Simple',
            'pid': job_id,
            'script_path': script_path,
            'status_dir': status_dir,
        }
        return job_id, 'RUNNING', job_info

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype: string
        """
        job_id = int(job_id)
        paths = self._status_paths(job_id)
        os.makedirs(paths['status_dir'], exist_ok=True)
        try:
            os.killpg(job_id, signal.SIGTERM)
        except ProcessLookupError:
            return 'COMPLETED'
        with open(paths['returncode'], 'w', encoding='UTF-8') as fp:
            fp.write('-15\n')
        with open(paths['done'], 'w', encoding='UTF-8') as fp:
            fp.write('cancelled\n')
        return 'CANCELLED'

    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype: tuple (string, dict)
        """
        job_id = int(job_id)
        paths = self._status_paths(job_id)
        job_info = {
            'scheduler': 'Simple',
            'pid': job_id,
            'returncode_path': paths['returncode'],
        }
        if os.path.exists(paths['returncode']):
            with open(paths['returncode'], 'r', encoding='UTF-8') as fp:
                return_code = int(fp.read().strip())

            job_info['return_code'] = return_code

            if return_code == 0:
                return 'COMPLETED', job_info
            return 'FAILED', job_info
        try:
            os.killpg(job_id, 0)
        except ProcessLookupError:
            return 'FAILED', job_info
        except PermissionError:
            return 'RUNNING', job_info
        return 'RUNNING', job_info

    def _status_paths(self, job_id):
        """Return status file paths for a SimpleWorker job."""
        status_dir = os.path.join(self.workdir, 'simple_worker_status')
        return {
            'status_dir': status_dir,
            'returncode': os.path.join(status_dir, f'{job_id}.returncode'),
            'done': os.path.join(status_dir, f'{job_id}.done'),
        }

    def build_text(self, task):
        """Build text for task script."""
        crt_res = self.crt.run_text(task)
        shell = task.get_requirement('beeflow:ScriptRequirement', 'shell', default='/bin/bash')
        stdout_path, stderr_path = self.resolve_stdout_stderr(task)
        script = [
            f'#!{shell}',
        ]
        if shell == '/bin/bash':
            script.append('set -e')
        script.append(f'exec > "{stdout_path}" 2> "{stderr_path}"')
        script.append(crt_res.env_code)
        pre_script = None
        post_script = None
        scripts_enabled = task.get_requirement('beeflow:ScriptRequirement', 'enabled',
                                            default=False)
        if scripts_enabled:
            pre_script = task.get_requirement('beeflow:ScriptRequirement', 'pre_script')
            post_script = task.get_requirement('beeflow:ScriptRequirement', 'post_script')
            if pre_script:
                script.extend(pre_script.splitlines())
        # Pre commands
        for cmd in crt_res.pre_commands:
            script.append(' '.join(cmd.args))
        # Main command
        script.append(' '.join(crt_res.main_command.args))
        # Post commands
        for cmd in crt_res.post_commands:
            script.append(' '.join(cmd.args))
        if scripts_enabled and post_script:
            script.extend(post_script.splitlines())
        return '\n'.join(script)
