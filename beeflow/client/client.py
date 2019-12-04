#!/usr/bin/env python3

import requests
import os

# Returns the url to the resource
def _url():
    return 'http://127.0.0.1:5000/bee_orc/v1/jobs/'

def _resource(id=""): 
    return _url() + str(id)

def submit_job(job_title):
    resp = requests.post(_url(), json={'title': job_title})
    if resp.status_code != requests.codes.created:
        raise ApiError("POST /jobs".format(resp.status_code))
    print(resp.text)
    # TODO not sure if this works the way I want it too
    id = resp.json()['id']
    return id

# TODO Need to figure out how to add the CWL file to this
#curl -i  -X POST -F 'workflow=@workflow.cwl'  http://127.0.0.1:5000/bee_orc/v1/jobs/42
def submit_workflow(id):
    files = {'workflow': open('echo.cwl', 'rb')}
    resp = requests.post(_resource(id), files=files)
    print(resp.text)
    if resp.status_code != requests.codes.created:
        raise ApiError("POST /jobs".format(resp.status_code))

def start_job(id):
    resp = requests.put(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PUT /jobs{}".format(resp.status_code, id))

def query_job(id):
    resp = requests.get(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("GET /jobs{}".format(resp.status_code, id))

# Sends a request to the server to delete the resource 
def cancel_job(id):
    resp = requests.delete(_resource(id), json={'id': id})
    # Returns okay if the resource has been deleted
    # Non-blocking so it returns accepted 
    # TODO Is this what we want? 
    if resp.status_code != requests.codes.accepted:
        raise ApiError("DELTE /jobs{}".format(resp.status_code, id))

def pause_job(id):
    resp = requests.patch(_resource(id), json={'id': id})
    if resp.status_code != requests.codes.okay:
        raise ApiError("PAUSE /jobs{}".format(resp.status_code, id))

menu_items = [
    { "Submit Job": submit_job },
    { "Start Job": start_job},
    { "Query Job": query_job },
    { "Pause Job": pause_job },
    { "Cancel Job": cancel_job },
    { "Exit": exit}
]

if __name__ == '__main__':

    ## Start the CLI loop 
    #while True:
    #    #os.system('clear')
    #    print("Welcome to BEE Client! 🐝")
    #    for item in menu_items:
    #        print(str(menu_items.index(item)) + ") " + list(item.keys())[0])
    #    choice = input("$ ")
    #    try:
    #        if int(choice) < 0: raise ValueError
    #        if int(choice) == 0:
    #            # TODO needs error handling
    #            print("What will be the name of the job?")
    #            name = input("$ ")
    #            submit_job(name)
    #        else:
    #            list(menu_items[int(choice)].values())[0]()
    #    except (ValueError, IndexError):
    #        pass
    
    id = submit_job("bam")
    submit_workflow(id)
