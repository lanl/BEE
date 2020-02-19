#! /usr/bin/env python3
"""Unit test module for BEE slurm worker interface."""

import unittest
import os
import shutil

from beeflow.common.data.wf_data import Task 
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker


class TestSlurmWorker(unittest.TestCase):
    """Unit test case for worker interface."""

    import shutil
    import os
    
    @classmethod
    def setUpClass(cls):
        """Initialize the Worker interface."""
        cls.worker = WorkerInterface(SlurmWorker)

        job_template_file = '~/.beeflow/worker/job.template'
        #check for a template, if not make the scripts without it
        job_template = ''
        try:
            f = open(job_template_file, 'r')
            job_template = f.read()
            f.close()
        except OSError as err:
            print("OS error: {0}".format(err))
            print('No job_template: creating a simple job template!')
            job_template = '#! /bin/bash\n#SBATCH\n'

        #substitute template & add the command (need to add requirements)
        #template = string.Template(job_template)
        #task_script_text = template.substitute(task.__dict__) + ' '.join(task.command)

        good = '#! /bin/bash\n'
        good += '#SBATCH -J slurm-good\n'
        good += '#SBATCH -o slurm-good.log\n\n'
        good += 'echo "Good Job ran with job id:"; echo $SLURM_JOB_ID\n'
        try:
            f = open('good.slr', 'w')
            f.write(good)
            f.close()
        except IOError as error: 
            print('Could not write good.slr!')
            print('I/O error: {0}'.format(error))

        bad = '#! /bin/bash\n'
        bad += '#SBATCH -J slurm-bad\n'
        bad += '#SBATCH -o slurm-bad.log\n\n'
        bad += '#SBATCH BAD_DIRECTIVE\n\n'
        bad += 'echo "Bad job should not run!"\n'
        try:
            f = open('bad.slr', 'w')
            f.write(bad)
            f.close()
        except IOError as error: 
            print('Could not write bad.slr!')
            print('I/O error: {0}'.format(error))

    @classmethod
    def tearDownClass(cls):
        """Deletes files created for tests."""

        try:
            os.remove('good.slr')
        except IOError as error: 
            print('Could not remove good.slr!')
            print('I/O error: {0}'.format(error))

        try:
            os.remove('bad.slr')
        except IOError as error: 
            print('Could not remove bad.slr!')
            print('I/O error: {0}'.format(error))
   
    def test_submit_bad_job(self):
        """Submit a job."""
        job_info = self.worker.submit_job('bad.slr')
        self.assertEqual(job_info[0], -1)
        self.assertIn('error', job_info[1])

    def test_submit_good_job(self):
        """Submit a job."""
        job_info = self.worker.submit_job('good.slr')
        self.assertNotEqual(job_info[0], 1)
        self.assertEqual('PENDING', job_info[1])

    def test_submit_bad_task(self):
        """Build and submit a bad task using  a bad directive."""

        task = Task('bad', command=['#SBATCH', '"BAD_DIRECTIVE"'], hints=None,
            subworkflow=None, inputs=None, outputs=None)
        job_info = self.worker.submit_task(task)
        self.assertEqual(job_info[0], -1)
        self.assertIn('error', job_info[1])
   
    def test_submit_good_task(self):
        """Build and submit a good task, state should be 'PENDING' or 'RUNNING'."""
        task = Task('good', 
            command=['echo', '" Good task ran with job id:"', 
            ';', 'echo', '$SLURM_JOB_ID'], 
        hints=None, subworkflow=None, inputs=None, outputs=None)
        job_info = self.worker.submit_task(task)
        self.assertNotEqual(job_info[0], 1)
        self.assertTrue(job_info[1] == 'PENDING' or job_info[1] == 'RUNNING')

    def test_query_bad_job_id(self):
        """Query a non-existent job."""
        job_info = self.worker.query_job(888)
        self.assertEqual(job_info[0], -1)
        self.assertEqual('Invalid job id specified', job_info[1])

    def test_query_good_job(self):
        """Submit a job and query the state, should be 'PENDING' or 'RUNNING'."""
        job_info = self.worker.submit_job('good.slr')
        job_id = job_info[0]
        job_info = self.worker.query_job(job_id)
        self.assertEqual(job_info[0], True)
        self.assertTrue(job_info[1] == 'PENDING' or job_info[1] == 'RUNNING')

    def test_cancel_good_job(self):
        """Submit a job and cancel it."""
        job_info = self.worker.submit_job('good.slr')
        job_id = job_info[0]
        job_info = self.worker.cancel_job(job_id)
        self.assertEqual(job_info[0], True)
        self.assertTrue(job_info[1] == 'CANCELLED' or job_info[1] == 'CANCELLING')

    def test_cancel_bad_job_id(self):
        """Cancel a non-existent job."""
        job_info = self.worker.cancel_job(888)
        self.assertEqual(job_info[0], -1)
        self.assertEqual('Invalid job id specified', job_info[1])
