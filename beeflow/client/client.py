#!/usr/bin/env python3

import os
import logging
import requests
from errors import ApiError
from pathlib import Path

logging.basicConfig(level=logging.INFO)

workflow_manager = 'bee_wfm/v1/jobs'

# Returns the url to the resource
def _url():
    return f'http://127.0.0.1:5000/{workflow_manager}/'

def _resource(tag=""): 
    return _url() + str(tag)

# Submit a job to the workflow manager
# This creates a workflow on the wfm and returns an ID 
def create_job(job_name, workflow_path):
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

# Start workflow on server
def start_job(wf_id):
    resp = requests.post(_resource(wf_id), json={'wf_id': wf_id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PUT /jobs{}".format(resp.status_code, wf_id))
    logging.info('Start job: ' + resp.text)

# Query the current status of a job
def query_job(wf_id):
    resp = requests.get(_resource(wf_id), json={'wf_id': wf_id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("GET /jobs{}".format(resp.status_code, wf_id))
    logging.info('Query job: ' + resp.text)

# Sends a request to the server to delete the resource 
def cancel_job(wf_id):
    resp = requests.delete(_resource(wf_id), json={'wf_id': wf_id})
    # Returns okay if the resource has been deleted
    # Non-blocking so it returns accepted 
    if resp.status_code != requests.codes.accepted:
        raise ApiError("DELETE /jobs{}".format(resp.status_code, wf_id))
    logging.info('Cancel job: ' + resp.text)

# Pause the execution of a job
def pause_job(wf_id):
    resp = requests.patch(_resource(wf_id), json={'wf_id': wf_id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PAUSE /jobs{}".format(resp.status_code, wf_id))
    logging.info('Pause job: ' + resp.text)

menu_items = [
    { "Submit Job": create_job },
    { "Start Job": start_job },
    { "Query Job": query_job },
    { "Pause Job": pause_job },
    { "Cancel Job": cancel_job },
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
            print(f"Error {answer} is not a valwf_id option")
    return answer

if __name__ == '__main__':
    # Start the CLI loop 
    wf_id = 1
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
            wf_id = create_job(job_name, workflow_path)
            submit_workflow(wf_id, workflow_path) 
        else:
            list(menu_items[int(choice)].values())[0](wf_id)
    except (ValueError, IndexError):
        pass
