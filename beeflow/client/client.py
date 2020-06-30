#!/usr/bin/env python3

import os
import logging
import requests
import sys
import platform
from errors import ApiError
from pathlib import Path
from beeflow.common.config.config_driver import BeeConfig

try:
    bc = BeeConfig(userconfig=sys.argv[1])
except IndexError:
    bc = BeeConfig()

# Set Workflow manager ports, attempt to prevent collisions
WM_PORT = 5000

if platform.system() == 'Windows':
    # Get parent's pid to offset ports. uid method better but not available in Windows
    WM_PORT += os.getppid() % 100
else:
    WM_PORT += os.getuid() % 100

logging.basicConfig(level=logging.WARNING)

workflow_manager = 'bee_wfm/v1/jobs'

# Returns the url to the resource
def _url():
    if bc.userconfig.has_section('workflow_manager'):
        wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',WM_PORT)
    else:
        print("[workflow_manager] section not found in configuration file. Default port WM_PORT will be used.")
        wfm_listen_port = WM_PORT
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'

def _resource(tag=""): 
    return _url() + str(tag)

# Submit a job to the workflow manager
# This creates a workflow on the wfm and returns an ID 
def create_workflow(job_name, workflow_path):
    resp = requests.post(_url(), 
        json= {'title': job_name, 
               'filename': os.path.basename(workflow_path)
        })

    if resp.status_code != requests.codes.created:
        print(f"Returned {resp.status_code}")
        raise ApiError("POST /jobs".format(resp.status_code))

    logging.info("Submit job: " + resp.text)

    wf_id = resp.json()['wf_id']
    logging.info("wf_id is " + str(wf_id))
    return wf_id

# Send workflow to wfm using wf_id 
def submit_workflow(wf_id, workflow_path):
    files = {'workflow': open(workflow_path, 'rb')}
    resp = requests.put(_resource("submit/" + wf_id), files=files)
    if resp.status_code != requests.codes.created:
        print(f"{resp.status_code}")
        raise ApiError("POST /jobs".format(resp.status_code))
    logging.info('Submit workflow: ' + resp.text)

# Start workflow
def start_workflow(wf_id):
    resp = requests.post(_resource(wf_id), json={'wf_id': wf_id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PUT /jobs{}".format(resp.status_code, wf_id))
    logging.info('Start job: ' + resp.text)

# Query the current status of a job
def query_workflow(wf_id):
    resp = requests.get(_resource(wf_id), json={'wf_id': wf_id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("GET /jobs {}".format(resp.status_code, wf_id))
    task_status = resp.json()['msg']
    print("STATUS\n" + task_status)
    logging.info('Query job: ' + resp.text)

# Sends a request to the server to delete the resource 
def cancel_workflow(wf_id):
    resp = requests.delete(_resource(wf_id), json={'wf_id': wf_id})
    # Returns okay if the resource has been deleted
    # Non-blocking so it returns accepted 
    if resp.status_code != requests.codes.accepted:
        raise ApiError("DELETE /jobs{}".format(resp.status_code, wf_id))
    logging.info('Cancel job: ' + resp.text)

# Pause the execution of a job
def pause_workflow(wf_id):
    resp = requests.patch(_resource(wf_id), json={'wf_id': wf_id, 'option' : 'pause' })
    if resp.status_code != requests.codes.okay:
        raise ApiError("PAUSE /jobs{}".format(resp.status_code, wf_id))
    logging.info('Pause job: ' + resp.text)

# Resume the execution of a job
def resume_workflow(wf_id):
    resp = requests.patch(_resource(wf_id), json={'wf_id': wf_id, 'option' : 'resume' })
    if resp.status_code != requests.codes.okay:
        raise ApiError("RESUME /jobs{}".format(resp.status_code, wf_id))
    logging.info('Resume job: ' + resp.text)


menu_items = [
    { "Submit Workflow": create_workflow },
    { "Start Workflow": start_workflow },
    { "Query Workflow": query_workflow },
    { "Pause Workflow": pause_workflow },
    { "Resume Workflow": resume_workflow },
    { "Cancel Workflow": cancel_workflow },
    { "Exit": exit }
]

def safe_input(type):
    while True:
        try:
            answer = input("$ ")
            # Cast it to the specified type
            answer = type(answer)
            break
        except ValueError:
            print(f"Error {answer} is not a valid option")
    return answer

if __name__ == '__main__':
    # Start the CLI loop 
    print("Welcome to BEE Client! 🐝")
    for item in menu_items:
        print(str(menu_items.index(item)) + ") " + list(item.keys())[0])
    choice = safe_input(int)
    try:
        if int(choice) < 0: raise ValueError
        if int(choice) == 0:
            # TODO needs error handling
            print("What will be the name of the job?")
            job_name = safe_input(str)
            print("What is the workflow path?")
            workflow_path = safe_input(Path)
            wf_id = create_workflow(job_name, workflow_path)
            submit_workflow(wf_id, workflow_path) 
            print("Job submitted! Your workflow id is 42.")
        else:
            print("What is the workflow id?")
            wf_id = safe_input(str)
            list(menu_items[int(choice)].values())[0](wf_id)
    except (ValueError, IndexError):
        pass
