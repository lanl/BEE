#!/usr/bin/env python3
import argparse
import sys
import os
import requests

import beeflow.common.config_driver as config_driver

workflow_manager = 'bee_wfm/v1/jobs'
bc = config_driver.BeeConfig()

# Returns the url to the resource
def _url():
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port')
    if wfm_listen_port is None:
        sys.exit('wfm_listen_port is missing in the config')
    #if bc.userconfig.has_section('workflow_manager'):
    #    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',WM_PORT)
    #else:
    #    print("[workflow_manager] section not found in configuration file. Default port WM_PORT will be used.")
    #    wfm_listen_port = WM_PORT
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'

def _resource(tag=""): 
    return _url() + str(tag)


# Submit a job to the workflow manager
parser = argparse.ArgumentParser()
# TODO: Add other arguments
parser.add_argument('--workflow-path', required=True, help='CWL workflow file path')
args = parser.parse_args()

print('Creating workflow')
resp = requests.post(_url(), json={'title': 'title', 'filename': os.path.basename(args.workflow_path)})
if resp.status_code != requests.codes.created:
    sys.exit('Workflow Manager returned an error!')
wf_id = resp.json()['wf_id']

# Now submit the workflow
print('Submitting workflow')
files = {
    'workflow': open(args.workflow_path, 'rb'),
}
resp = requests.put(_resource("submit/" + wf_id), files=files)
if resp.status_code != requests.codes.created:
    sys.exit('Workflow Manager returned an error!')

# Now start the workflow
print('Starting workflow')
resp = requests.post(_resource(wf_id), json={'wf_id': wf_id})
if resp.status_code != requests.codes.okay:
    sys.exit('Workflow Manager failed to start workflow: %i' % (resp.status_code,))
