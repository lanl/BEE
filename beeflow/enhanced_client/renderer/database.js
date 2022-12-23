// Database code using the window.localStorage object.

const DB_NAME = 'BeeClient';
const WORKFLOWS = 'workflows';
const CLUSTERS = 'clusters';

let store = window.localStorage;

// *_key() functions are used to determine the key within the localStorage
// object.
//
// Database objects are separated by using different key prefixes. For example,
// a key prefixed with 'workflows:' is used for a workflow object.
//

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

function is_cluster_key(key) {
  return key.startsWith('clusters:');
}

function encode(obj) {
  return JSON.stringify(obj);
}

function decode(s) {
  return JSON.parse(s);
}

function init() {
  // TODO: Remove this?
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

// Add a WF
function add_wf(wf_id, name) {
  let wf = {
    wf_id,
    completed: 'False',
    archived: 'False',
    percentage_complete: 0,
    status: 'Pending',
    name,
  };
  store.setItem(workflow_key(wf_id), encode(wf));
}

// Add a cluster configuration
function add_config(hostname, moniker, bolt_port, wfm_sock) {
  let id = store.getItem('next_cluster_id');
  if (id === null) {
    id = 0;
  }
  let config = {
    hostname,
    moniker,
    bolt_port,
    wfm_sock,
  };
  store.setItem(cluster_key(id), encode(config));
  // Increment the next id
  store.setItem('next_cluster_id', id + 1);
  return id;
}

// Get all saved cluster configs
function get_cluster_configs() {
  let clusters = [];
  for_each_element(key => is_cluster_key(key), (key, cluster) => {
    clusters.push(decode(cluster));
  });
  return clusters;
}

// Get a parituclar wf
function get_wf(wf_id) {
  return decode(store.getItem(workflow_key(wf_id)));
}

// Get all workflows in the system
function get_workflows() {
  let workflows = [];
  for_each_element(key => is_workflow_key(key), (key, workflow) => {
    workflows.push(decode(workflow));
  });
  return workflows;
}

// Get all tasks associated with a wf_id
function get_tasks(wf_id) {
  let tasks = [];
  for_each_element(key => is_workflow_task_key(key, wf_id), (key, task) => {
    tasks.push(decode(task));
  });
  return tasks;
}

function update_task_state(task_id, wf_id, status) {
  let key = task_key(wf_id, task_id);
  let task = decode(store.getItem(key));
  task.status = status;
  store.setItem(key, encode(task));
}

function delete_wf(wf_id) {
  // Note: this doesn't delete the tasks
  store.removeItem(workflow_key(wf_id));
}

function add_task(task_id, wf_id, name, resource, base_command, status) {
  let key = task_key(wf_id, task_id);
  let task = {
    wf_id,
    task_id,
    completed,
    resource,
    base_command,
    status,
  };
  store.setItem(key, encode(task));
}

function delete_task(wf_id, task_id) {
  store.removeItem(task_key(wf_id, task_id));
}

// Delete everything
function clear() {
  store.clear();
}

module.exports = { init, add_wf, get_wf, get_workflows, get_tasks, delete_wf,
                   add_config, get_cluster_configs, add_task, delete_task,
                   clear };
