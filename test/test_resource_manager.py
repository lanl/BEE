import requests
import subprocess
import time
import unittest


class TestResourceManager(unittest.TestCase):
    def setUp(self):
        # Start the server process
        self.proc = subprocess.Popen([
            'python', 'beeflow/resource_manager/resource_manager.py',
            '-p', '5000'
        ])
        # Wait a few seconds for the server to start
        time.sleep(3)

    def tearDown(self):
        # Kill the running server process
        self.proc.kill()

    # Test /jobs
    def test_0000(self):
        r = requests.get('http://localhost:5000/jobs')
        self.assertTrue(r.ok)
        self.assertEqual(r.json(), [])

    # Test /jobs
    def test_0001(self):
        # TODO
        r = requests.post('http://localhost:5000/jobs', data={})

        r = requests.get('http://localhost:5000/jobs')

        self.assertTrue(r.ok)
        self.assertEqual(r.json(), [{}])


    ##################################################################
    # Generate code below

    # Test /jobs fail
    def test_0000_fail(self):
        r = requests.get('http://localhost:5000/jobs')
        # TODO
        self.assertFalse(r.ok)

    # Test /jobs/{job_id}
    def test_0001(self):
        r = requests.get('http://localhost:5000/jobs/{job_id}')
        # TODO
        self.assertTrue(r.ok)
    # Test /jobs/{job_id} fail
    def test_0001_fail(self):
        r = requests.get('http://localhost:5000/jobs/{job_id}')
        # TODO
        self.assertFalse(r.ok)

    # Test /jobs/{job_id}
    def test_0002(self):
        r = requests.put('http://localhost:5000/jobs/{job_id}')
        # TODO
        self.assertTrue(r.ok)
    # Test /jobs/{job_id} fail
    def test_0002_fail(self):
        r = requests.put('http://localhost:5000/jobs/{job_id}')
        # TODO
        self.assertFalse(r.ok)

    # Test /jobs/{job_id}/allocation
    def test_0003(self):
        r = requests.get('http://localhost:5000/jobs/{job_id}/allocation')
        # TODO
        self.assertTrue(r.ok)
    # Test /jobs/{job_id}/allocation fail
    def test_0003_fail(self):
        r = requests.get('http://localhost:5000/jobs/{job_id}/allocation')
        # TODO
        self.assertFalse(r.ok)

    # Test /nodes
    def test_0004(self):
        r = requests.get('http://localhost:5000/nodes')
        # TODO
        self.assertTrue(r.ok)
    # Test /nodes fail
    def test_0004_fail(self):
        r = requests.get('http://localhost:5000/nodes')
        # TODO
        self.assertFalse(r.ok)

    # Test /nodes
    def test_0005(self):
        r = requests.post('http://localhost:5000/nodes')
        # TODO
        self.assertTrue(r.ok)
    # Test /nodes fail
    def test_0005_fail(self):
        r = requests.post('http://localhost:5000/nodes')
        # TODO
        self.assertFalse(r.ok)

    # Test /nodes/{node_id}
    def test_0006(self):
        r = requests.get('http://localhost:5000/nodes/{node_id}')
        # TODO
        self.assertTrue(r.ok)
    # Test /nodes/{node_id} fail
    def test_0006_fail(self):
        r = requests.get('http://localhost:5000/nodes/{node_id}')
        # TODO
        self.assertFalse(r.ok)

    # Test /nodes/{node_id}
    def test_0007(self):
        r = requests.put('http://localhost:5000/nodes/{node_id}')
        # TODO
        self.assertTrue(r.ok)
    # Test /nodes/{node_id} fail
    def test_0007_fail(self):
        r = requests.put('http://localhost:5000/nodes/{node_id}')
        # TODO
        self.assertFalse(r.ok)

    ###############################################################


if __name__ == '__main__':
    unittest.main(verbosity=2)
