#!/usr/bin/env python3

import logging
import requests
from errors import ApiError
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Returns the url to the resource
def _url():
    return 'http://127.0.0.1:5000/bee_orc/v1/jobs/'

def _resource(id=""): 
    return _url() + str(id)

# Submit a job to the workflow manager
# This creates a workflow on the wfm and returns an ID 
def submit_job(job_title):
    resp = requests.post(_url(), json={'title': job_title})

    if resp.status_code != requests.codes.created:
        raise ApiError("POST /jobs".format(resp.status_code))

    logging.info("Submit job: " + resp.text)

    id = resp.json()['id']
    logging.info("id is " + str(id))
    return id

# Send workflow to wfm using id 
def submit_workflow(id, workflow_path):
    files = {'workflow': open(workflow_path, 'rb')}
    resp = requests.post(_resource(id), files=files)
    if resp.status_code != requests.codes.created:
        raise ApiError("POST /jobs".format(resp.status_code))
    logging.info('Submit workflow: ' + resp.text)

# Start workflow on server
def start_job(id):
    resp = requests.put(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PUT /jobs{}".format(resp.status_code, id))
    logging.info('Start job: ' + resp.text)

# Query the current status of a job
def query_job(id):
    resp = requests.get(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("GET /jobs{}".format(resp.status_code, id))
    logging.info('Query job: ' + resp.text)


# Sends a request to the server to delete the resource 
def cancel_job(id):
    resp = requests.delete(_resource(id), json={'id': id})
    # Returns okay if the resource has been deleted
    # Non-blocking so it returns accepted 
    if resp.status_code != requests.codes.accepted:
        raise ApiError("DELETE /jobs{}".format(resp.status_code, id))
    logging.info('Cancel job: ' + resp.text)

# Pause the execution of a job
def pause_job(id):
    resp = requests.patch(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PAUSE /jobs{}".format(resp.status_code, id))
    logging.info('Pause job: ' + resp.text)

menu_items = [
    { "Submit Job": submit_job },
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
            print(f"Error {answer} is not a valid option")
    return answer

if __name__ == '__main__':
    # Start the CLI loop 
    id = 1
    print("Welcome to BEE! 🐝")
    while True:
        for item in menu_items:
            print(str(menu_items.index(item)) + ") " + list(item.keys())[0])
        choice = safe_input(int)
        try:
            if int(choice) < 0: raise ValueError
            if int(choice) == 0:
                # TODO needs error handling
                print("What will be the name of the job?")
                name = safe_input(str)
                id = submit_job(name)
                print("What's the workflow filename?")
                workflow_path = safe_input(Path)
                submit_workflow(id, workflow_path) 
            else:
                list(menu_items[int(choice)].values())[0](id)
        except (ValueError, IndexError):
            pass
    
    id = submit_job("bam")
    submit_workflow(id)
