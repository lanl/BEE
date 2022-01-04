#!/usr/bin/env python3

import os
import logging
import requests
import sys
import subprocess
import platform
import jsonpickle
from pathlib import Path
from beeflow.common.config_driver import BeeConfig

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

# Package Workflow
def package_workflow():
    print("What's the directory you want to package: ")  
    package_dir = safe_input(str) 
    if os.path.isdir(package_dir):
        # Just use tar with subprocess. Python's tar library is not performant. 
        # Need to remove trailing slashes
        package_dir = package_dir.rstrip('/')
        if package_dir.find('/') == -1:
            return_code = subprocess.run(['tar', 'czf', f'{package_dir}.tgz' , package_dir]).returncode
        else:
            tar_dir = os.path.basename(os.path.normpath(package_dir))
            tarball = tar_dir + '.tgz'
            parent_dir = package_dir[:-len(tar_dir) - 1]
            return_code = subprocess.run(['tar', '-C', parent_dir, '-czf', tarball, tar_dir]).returncode
        if return_code != 0:
            print("Package failed")
        else:
            print(f"Package {package_dir}.tgz created successfully")
    else:
        print(f"{package_dir} is not a valid directory.")

# Submit a job to the workflow manager
# This creates a workflow on the wfm and returns an ID 
def submit_workflow(wf_name, workflow_path, main_cwl, yaml=None):

    if yaml:
        files = {
                    'wf_name': wf_name.encode(),
                    'wf_filename': os.path.basename(workflow_path).encode(),
                    'workflow': open(workflow_path, 'rb'),
                    'main_cwl': main_cwl,
                    'yaml': yaml
                }
    else:
        files = {
                    'wf_name': wf_name.encode(),
                    'wf_filename': os.path.basename(workflow_path).encode(),
                    'workflow': open(workflow_path, 'rb'),
                    'main_cwl': main_cwl
                }


    resp = requests.post(_url(), files=files)
    if resp.status_code != requests.codes.created:
        print(f"Returned {resp.status_code}")
        #raise ApiError("POST /jobs".format(resp.status_code))

    logging.info("Submit job: " + resp.text)

    wf_id = resp.json()['wf_id']
    logging.info("wf_id is " + str(wf_id))
    return wf_id

# Start workflow on server
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


def copy_workflow(wf_id, archive_path):
    resp = requests.patch(_url(), files={'wf_id': wf_id.encode()})
    if resp.status_code != requests.codes.okay:
        raise ApiError("COPY /jobs{}".format(resp.status_code, wf_id))
    archive_file = jsonpickle.decode(resp.json()['archive_file'])
    archive_filename = resp.json()['archive_filename']
    return archive_file, archive_filename

def reexecute_workflow(archive_path, wf_name):
    files = {
                'filename': os.path.basename(archive_path).encode(),
                'workflow_archive': open(archive_path, 'rb'),
                'wf_name': wf_name.encode()
            }
    resp = requests.put(_url(), files=files)
    if resp.status_code != requests.codes.created:
        raise ApiError("REEXECUTE /jobs{}".format(resp.status_code))

    logging.info("ReExecute Workflow: " + resp.text)

    wf_id = resp.json()['wf_id']
    return wf_id

def list_workflows():
    resp = requests.get(_url())
    if resp.status_code != requests.codes.okay:
        print(f"Returned {resp.status_code}")
        raise ApiError("GET /jobs".format(resp.status_code))

    logging.info("List Jobs: " + resp.text)
    job_list = jsonpickle.decode(resp.json()['job_list'])
    if job_list:
        print(f"Name\tID\t\t\t\t\tStatus")
        for i in job_list:
            print(f"{i[0]}\t{i[1]}\t{i[2]}")
    else:
        print("There are currently no jobs.")

menu_items = [
    { "Package Workflow": package_workflow },
    { "Submit Workflow": submit_workflow },
    { "List Workflows": list_workflows },
    { "Start Workflow": start_workflow },
    { "Query Workflow": query_workflow },
    { "Pause Workflow": pause_workflow },
    { "Resume Workflow": resume_workflow },
    { "Cancel Workflow": cancel_workflow },
    { "Copy Workflow": copy_workflow },
    { "ReExecute Workflow": reexecute_workflow },
    { "Exit": exit }
]


if __name__ == '__main__':
    # Start the CLI loop 
    print("Welcome to BEE Client! 🐝")
    for item in menu_items:
        print(str(menu_items.index(item)) + ") " + list(item.keys())[0])
    choice = safe_input(int)
    try:
        if int(choice) < 0: raise ValueError
        if int(choice) == 0:
            package_workflow()
        elif int(choice) == 1:
            # TODO needs error handling
            print("Workflow name: ")
            wf_name = safe_input(str)
            print("Workflow tarball path:")
            workflow_path = safe_input(Path)
            print("Main cwl file: ")
            main_cwl = safe_input(str)
            print("Does the job have a yaml file (y/n):")
            has_yaml = safe_input(str)
            if has_yaml[0].lower() == "y":
                print("Yaml file: ")
                yaml = safe_input(str)
                print("Submitting")
                try:
                    wf_id = submit_workflow(wf_name, workflow_path, main_cwl, yaml)
                except Exception as e:
                    print(f'Exception {e}')
            else:
                wf_id = submit_workflow(wf_name, workflow_path, main_cwl)
            print(f"Job submitted! Your workflow id is {wf_id}.")
        elif int(choice) == 2:
            list_workflows()
        elif int(choice) < 7:
            print("What is the workflow id?")
            wf_id = safe_input(str)
            list(menu_items[int(choice)].values())[0](wf_id)
        elif int(choice) == 7:
            print("What is the workflow id?")
            wf_id = safe_input(str)
            print("Where do you want to save it?")
            archive_path = safe_input(str)
            archive_file, archive_filename = copy_workflow(wf_id, archive_path)
            with open(os.path.join(archive_path, archive_filename), 'wb') as a:
                a.write(archive_file)
        elif int(choice) == 8:
            print("What is the archive path?")
            archive_path = safe_input(Path)
            print("What will be the name of the job?")
            wf_name = safe_input(str)
            wf_id = reexecute_workflow(archive_path, wf_name)
            print(f"Job submitted! Your workflow id is {wf_id}.")

    except (ValueError, IndexError):
        pass
