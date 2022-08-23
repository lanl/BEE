import pytest
import jsonpickle
from wf_manager import app

"""This module tessts the JobsList REST Endpoint"""

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.app_context():
        with app.test_client() as client:
            yield client

def test_submit_workflow(client):
    workflow_info = {
        'wf_name': 'sample_wf',
        'wf_filename': 'clamr-wf.tgz',
        'main_cwl': 'clamr_wf.cwl'
    }
    workflow_file = {'workflow': open('clamr-wf.tgz', 'rb')}
    
    response = client.post("/bee_wfm/v1/jobs/", data=workflow_file, 
            json=workflow_info)
    print(response.json)
    print(response)

def test_list_jobs_empty(client):
    response = client.get("/bee_wfm/v1/jobs/")
    # resp = requests.post(_url(), files=files)
    job_list = jsonpickle.decode(response.json['job_list'])
    assert job_list == []
