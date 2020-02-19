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
    #TODO remove next line if not needed
    import subprocess
    
    @classmethod
    def setUpClass(cls):
        """Initialize the Worker interface."""
        cls.worker = WorkerInterface(SlurmWorker)
        # using fixed directory save original template
        job_template_file = os.path.expanduser('~/.beeflow/worker/job.template')
        template_dir = os.path.dirname(job_template_file)
        os.makedirs(template_dir, exist_ok=True)
        try:
            shutil.copyfile(job_template_file, job_template_file + '_utest')
        except IOError as error:
            errno, strerror = error.args
            if (errno != 2):
                print(job_template_file)
                print('I/O error({0}): {1}'.format(errno,strerror))
                
        #TODO delete the followinglines
        subprocess.call(['ls', '-l'])
        print('job_template_file: ', job_template_file, ' contents: ')
        subprocess.call(['cat', job_template_file])
        print('job_template_file, '_utest (original template)', ' contents: ')
        subprocess.call(['cat', job_template_file+'_utest'])

    def test_submit_bad_task(self):
        """Build and submit a bad task using  a bad directive."""

        #TODO delete next line if BAD_DIRECTIVE works
        #task = Task('bad', command=['echo', '" bad task ran "'], hints=None,
        task = Task('bad', command=['#SBATCH', '"BAD_DIRECTIVE"'], hints=None,
            subworkflow=None, inputs=None, outputs=None)
        print('bad task submitted: ', task)
        job_info = self.worker.submit_task(task)
        # restore original template
        if copy: 
            shutil.move(job_template_file + '_utest', job_template_file)
        else:
            os.remove(job_template_file)
        self.assertEqual(job_info[0], -1)
        self.assertIn('error', job_info[1])

    def test_submit_good_task(self):
        """Build and submit a good task using good.template."""
        # using fixed directory first save original template then copy good.template
        job_template_file = os.path.expanduser('~/.beeflow/worker/job.template')
        template_dir = os.path.dirname(job_template_file)
        os.makedirs(template_dir, exist_ok=True)
        try:
            shutil.copyfile(job_template_file, job_template_file + '_utest')
            copy = True
        except IOError as error:
            errno, strerror = error.args
            if (errno == 2):
                #original template did not exist so didn't copy
                copy = False 
            else:
                print('I/O error({0}): {1}'.format(errno,strerror))
        shutil.copyfile('good.template', job_template_file)
        # The submit task 
        task = Task('good', command=['echo', '" good task ran "'], hints=None,
            subworkflow=None, inputs=None, outputs=None)
        job_info = self.worker.submit_task(task)
        print('good task submitted: ', task)
        # restore original
        if copy: 
            shutil.move(job_template_file + '_utest', job_template_file)
        else:
            os.remove(job_template_file)
        self.assertNotEqual(job_info[0], 1)
        self.assertTrue(job_info[1] == 'PENDING' or job_info[1] == 'RUNNING')

    def test_query_bad_job_id(self):
        """Query a non-existent job."""
        job_info = self.worker.query_job(888)
        self.assertEqual(job_info[0], -1)
        self.assertEqual('Invalid job id specified', job_info[1])

    def test_query_good_job(self):
        """Submit a good job and query the state, should be 'PENDING'."""
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
