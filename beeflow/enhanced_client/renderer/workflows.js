/*
 * This file contains code that manages workflows in the app
 *
 *
 */

const client = require('./client.js');
const db = require('./database.js');
const display = require('./display.js');
const config = require('./config.js');
const viz = require('./viz.js');
//const workflows = new Map();
var workflow_list = null;

currentWorkflow = null

// Load workflows from database and initialize workflowList
function initialize(wf_list_id) {
  // Load all the workflows from the database
  // workflows = db.get_workflows();
  // console.log('Workflows');
  // console.log(workflows);
  // // Setup workflow list and populate it with stuff from database
  workflow_list = new WorkflowList(wf_list_id);
  // for (workflow in workflows) {
  //     workflow_list.add(workflow);
  // }
}

class Workflow {
  // Constructor for workflow object
  constructor(name, main_cwl, yaml, workdir, tarball_path, tarball_fname) {
    this.name = name;
    this.main_cwl = main_cwl;
    this.yaml = yaml;
    this.workdir = workdir;
    this.tarball_path = tarball_path;
    this.tarball_fname = tarball_fname;
    this.id = 'Pending';
    this.status = 'Pending';
  }
}

class WorkflowList {
  constructor(wf_list_id) {
    this.list = document.getElementById(wf_list_id);
    //console.log(this.list);
  }

  add(workflow) {
    var newItem = document.createElement('li');
    newItem.innerHTML = "<a>" + workflow.name + "</a>";
    newItem.className = "is-size-1";
    newItem.id = workflow.id;
    newItem.addEventListener('click', function () {
      // Set the main content area to show this workflow
    });
    this.list.appendChild(newItem);
  }

  delete(wf_id) {
    var elements = this.list.getElementsByTagName("li");
    var len = elements.length;

    for (var i = 0; i < len; i++) {
      if (elements[i].id == wf_id) {
        this.list.removeChild(elements[i]);
        break;
      }
    }
  }
}

// Add a new workflow
async function add_workflow(name, main_cwl, yaml, workdir, tarball_path, tarball_fname) {
  // Submit workflow to workflow manager
  // Create new WF object
  let new_workflow = new Workflow(name, main_cwl, yaml, workdir, tarball_path, tarball_fname);
  let {wf_id, tasks} = await client.submit_workflow(new_workflow);

  new_workflow.id = wf_id;
  //workflows.add(wf_id, new_workflow);
  // Add wf to the navigation list
  workflow_list.add(new_workflow);
  // Add to the database
  db.add_wf(wf_id, name);
  for (task_id in tasks) {
    let name = tasks[task_id]['name'];
    let base_command = tasks[task_id]['command'];
    let task_status = tasks[task_id]['status'];
    db.add_task(task_id, wf_id, name, config.resource, base_command, task_status);
  }

  // Make this workflow appear in the main workflow section
  set_current_workflow(new_workflow);
  // Remove the welcome message if currently displayed
  if (currentContent === welcomeMessage) {
    currentContent = currentWorkflow;
  }

  return wf_id;
}

function start_workflow() {
  wf_id = currentWorkflow.id;
  client.start_workflow(wf_id);
}

function delete_workflow(wf_id) {
  db.delete_wf(wf_id);
  client.cancel_workflow(wf_id);
  workflow_list.delete(wf_id);
  remove_current_workflow(wf_id);
}

function copy_workflow(wf_id, path) {
  client.copy(wf_id, path);
}

function reexecute_workflow(name, tarball_path) {
  (async () => {
    // Create new WF object
    let new_workflow = new Workflow(name, "", "", tarball_path);
    let {wf_id, tasks} = await client.reexecute_workflow(new_workflow);

    new_workflow.id = wf_id;
    //workflows.add(wf_id, new_workflow);
    // Add wf to the navigation list
    workflow_list.add(new_workflow);
    // Add to the database
    db.add_wf(wf_id, name);
    for (task_id in tasks) {
      let name = tasks[task_id]['name'];
      let base_command = tasks[task_id]['command'];
      let task_status = tasks[task_id]['status'];
      db.add_task(task_id, wf_id, name, config.resource, base_command, task_status);
    }

    // Make this workflow appear in the main workflow section
    set_current_workflow(new_workflow);
    // Remove the welcome message if currently displayed
    if (currentContent === welcomeMessage) {
      currentContent = currentWorkflow;
    }
  })();
}

function pause_workflow(wf_id) {
  client.pause_workflow(wf_id);
}

function resume_workflow(wf_id) {
  client.resume_workflow(wf_id);
}

function have_workflows() {
  return workflows.size > 0;
}

function remove_current_workflow(workflow) {
  // We have more workflows set to first one
  if (workflows.size > 0) {
    const new_workflow = [...workflows][0];
    set_current_workflow(workflow);
  }
}

function create_task_list(tasks) {
  for (task_id in tasks) {
    let name = tasks[task_id]['name'];
    let base_command = tasks[task_id]['command'];
    let task_status = tasks[task_id]['status'];
    var newTask = document.createElement('li');
    newTask.innerHTML = "<p>" + name + "  " + task_status + "</p>";
    taskList.appendChild(newTask);
  }
}

// Set the current workflow
function set_current_workflow(workflow) {
  (async () => {
    currentWorkflow = workflow;
    let current_wf_status = document.getElementById('current-wf_status');
    let current_wf_resource = document.getElementById('current-wf_resource');
    let current_wf_name = document.getElementById('current-wf_name');
    let current_wf_id = document.getElementById('current-wf_id');

    // Modify the variables used for the current workflow
    current_wf_status.innerHTML = workflow.status;
    current_wf_resource.innerHTML = 'fg-rfe1';
    current_wf_name.innerHTML = workflow.name;
    current_wf_id.innerHTML = workflow.id;

    // Need to add some additional logic here and make this truly asynchronous
    let {wf_status, tasks} = await client.query_workflow(workflow.id);

    // Set visualiation
    document.getElementById('viz').src = "viz.html";
    current_wf_status.innerHTML = wf_status;
    taskList = document.getElementById('taskList');
    taskList.innerHTML = '';

    for (task_id in tasks) {
      let name = tasks[task_id]['name'];
      let base_command = tasks[task_id]['command'];
      let task_status = tasks[task_id]['status'];
      var newTask = document.createElement('li');
      newTask.innerHTML = "<p>" + name + "  " + task_status + "</p>";
      taskList.appendChild(newTask);
    }
  })();
}

function download_current_archive() {
  wf_id = currentWorkflow.id;
  client.download_archive(wf_id);
  console.log(wf_id)
}

function update_current_workflow() {
  (async () => {
    // Query status of tasks
    wf_id = currentWorkflow.id;
    let {wf_status, tasks} = await client.query_workflow(wf_id);

    // Update visualization
    document.getElementById('viz').contentWindow.location.reload();
    let current_wf_status = document.getElementById('current-wf_status');
    current_wf_status.innerHTML = wf_status;

    taskList = document.getElementById('taskList');
    taskList.innerHTML = '';

    for (task_id in tasks) {
      let name = tasks[task_id]['name']
      let base_command = tasks[task_id]['command']
      let task_status = tasks[task_id]['status']
      var newTask = document.createElement('li');
      newTask.innerHTML = "<p>" + name + "  " + task_status + "</p>";
      taskList.appendChild(newTask)
    }
  })();
}

// Set the things we want to export
module.exports = { initialize, workflows, add_workflow, start_workflow,
                   update_current_workflow, Workflow, have_workflows,
                   pause_workflow, resume_workflow, delete_workflow, workflows,
                   download_current_archive, reexecute_workflow }
