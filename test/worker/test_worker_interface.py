#! /usr/bin/env python3
"""Unit test module for BEE worker interface module."""

import unittest

from beeflow.common.worker.worker_interface import WorkerInterface


class TestWorkerInterface(unittest.TestCase):
    """Unit test case for worker interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the Worker interface."""
        cls.worker = WorkerInterface()

    def test_submit_bad_job(self):
        """Submit a job."""
        job_info = self.worker.submit_job('bad.slr')
        self.assertEqual(job_info[0], 1)
        self.assertIn('error', job_info[1])

    def test_submit_good_job(self):
        """Submit a job."""
        job_info = self.worker.submit_job('good.slr')
        self.assertNotEqual(job_info[0], 1)
        self.assertEqual('PENDING', job_info[1])

    def test_query_bad_job_id(self):
        """Query a non-existent job."""
        job_status = self.worker.query_job(888)
        self.assertEqual(job_status[0], False)
        self.assertEqual('Invalid job id specified', job_status[1])

    def test_query_job(self):
        """Submit a good job and query the state, should be 'PENDING'."""
        job_info = self.worker.submit_job('good.slr')
        job_id = job_info[0]
        job_status = self.worker.query_job(job_id)
        self.assertEqual(job_status[0], True)
        self.assertEqual(job_status[1], 'PENDING')

    def test_cancel_job(self):
        """Submit a job and cancel it."""
        job_info = self.worker.submit_job('good.slr')
        job_id = job_info[0]
        job_status = self.worker.cancel_job(job_id)
        self.assertEqual(job_status[0], True)
        self.assertEqual(job_status[1], 'CANCELLED')

    def test_cancel_bad_job_id(self):
        """Cancel a non-existent job."""
        job_status = self.worker.cancel_job(888)
        self.assertEqual(job_status[0], False)
        self.assertEqual('Invalid job id specified', job_status[1])

