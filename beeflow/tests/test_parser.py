#! /usr/bin/env python3
"""Unit test module for the BEE CWL parser module."""

import unittest

from beeflow.common.parser import CwlParser
from beeflow.common.wf_data import generate_workflow_id

# Disable protected member access warning
# pylama:ignore=W0212


class TestParser(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the CWL parser, which connects to the GDB."""
        cls.parser = CwlParser()
        cls.wfi = cls.parser._wfi

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        if self.wfi.workflow_initialized() and self.wfi.workflow_loaded():
            self.wfi.finalize_workflow()

    def test_parse_workflow(self):
        """Test parsing of workflow with an input job file."""
        cwl_wfi_file = "clamr-wf/clamr_wf.cwl"
        cwl_job_yaml = "clamr-wf/clamr_job.yml"
        cwl_job_json = "clamr-wf/clamr_job.json"
        workflow_id = generate_workflow_id()

        # Test workflow parsing with YAML input job file
        wfi = self.parser.parse_workflow(workflow_id, cwl_wfi_file, cwl_job_yaml)
        self.assertTrue(wfi.workflow_loaded())

        wfi.finalize_workflow()
        self.assertFalse(wfi.workflow_loaded())

        # Test workflow parsing with JSON input job file
        wfi = self.parser.parse_workflow(workflow_id, cwl_wfi_file, cwl_job_json)
        self.assertTrue(wfi.workflow_loaded())

    def test_parse_workflow_no_job(self):
        """Test parsing of a workflow without an input job file."""
        cwl_wfi_file = "cf.cwl"
        workflow_id = generate_workflow_id()

        # Test workflow parsing without input job file
        wfi = self.parser.parse_workflow(workflow_id, cwl_wfi_file)
        self.assertTrue(wfi.workflow_loaded())


if __name__ == '__main__':
    unittest.main()
