// Database code using the window.localStorage object.

const DB_NAME = 'BeeClient';
const WORKFLOWS = 'workflows';
const CLUSTERS = 'clusters';

let store = window.localStorage;

// *_key() functions are used to determine the key within the localStorage
// object.

function workflow_key(wf_id) {
  return `workflows:${wf_id}`;
}

function is_workflow_key(key) {
  return key.startsWith('workflows:');
}

function task_key(wf_id, task_id) {
  return `tasks:${wf_id}:${task_id}`;
}

// Return true if this is a task for the given workflow
function is_workflow_task_key(key, wf_id) {
  return key.startsWith(`tasks:${wf_id}`);
}

function cluster_key(cluster_id) {
  return `clusters:${cluster_id}`;
}

function init() {
  // TODO: Remove this?
}

// Add a WF
function add_wf(wf_id, name) {
  let completed = 'False';
  let archived = 'False';
  let percentage_complete = 0;
  let status = 'Pending';
  store.setItem(workflow_key(wf_id), {
    wf_id,
    completed,
    archived,
    percentage_complete,
    status,
    name,
  });
}

// Add a cluster configuration
function add_config(hostname, moniker, resource, bolt_port, wfm_sock) {
  let id = store.getItem('next_cluster_id');
  if (id === null) {
    id = 0;
  }
  store.setItem(cluster_key(id), {
    hostname,
    moniker,
    resource,
    bolt_port,
    wfm_sock,
  });
  // Increment the next id
  store.setItem('next_cluster_id', id + 1);
  return id;
}

// Get a parituclar wf
function get_wf(wf_id) {
  return store.getItem(workflow_key(wf_id));
}

// Helper function to make it easier to iterate over elements of the store
function for_each_element(check, body) {
  for (let i = 0; i < store.length; i++) {
    let key = store.key(i);
    if (check(key)) {
      body(key, store.getItem(key));
    }
  }
}

// Get all workflows in the system
function get_workflows() {
  let workflows = [];
  for_each_element(key => is_workflow(key), (key, workflow) => {
    workflows.push(workflow);
  });
  return workflows;
}

// Get all tasks associated with a wf_id
function get_tasks(wf_id) {
  let tasks = [];
  for_each_element(key => is_workflow_task_key(key, wf_id), (key, task) => {
    tasks.push(task);
  });
  return tasks;
}

function update_task_state(task_id, wf_id, status) {
  let key = task_key(wf_id, task_id);
  let task = store.getItem(key);
  task.status = status;
  store.setItem(key, task);
}

function delete_wf(wf_id) {
  // Note: this doesn't delete the tasks
  store.removeItem(workflow_key(wf_id));
}

function add_task(task_id, wf_id, name, resource, base_command, status) {
  let key = task_key(wf_id, task_id);
  store.setItem(key, {
    wf_id,
    task_id,
    completed,
    resource,
    base_command,
    status,
  });
}

function delete_task(wf_id, task_id) {
  store.removeItem(task_key(wf_id, task_id));
}

module.exports = { init, add_wf, get_wf, get_workflows, get_tasks, delete_wf,
                   add_config, add_task, delete_task }
