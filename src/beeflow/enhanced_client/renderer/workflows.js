/* 
 * This file contains code that manages workflows in the app
 *
 *
 */

const client = require('./client.js');
const db = require('./database.js');
//const workflows = new Map();
var workflow_list = null;

// Load workflows from database and initialize workflowList
function initialize(wf_list_id) {
    // Load all the workflows from the database
    workflows = db.get_workflows();
    console.log('Workflows');
    console.log(workflows);
    // Setup workflow list and populate it with stuff from database
    workflow_list = new WorkflowList(wf_list_id);
    for (workflow in workflows) {
        workflow_list.add(workflow);
    }
}

class Workflow {
    // Constructor for workflow object
    constructor(wf_name, wf_cwl, yaml, actual_path) {
        this.name = wf_name;
        this.cwl = wf_cwl;
        this.yaml = yaml;
        this.path = actual_path;
        this.id = 'TBD';
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
            
    }
}

// Add a new workflow 
function add_workflow(wf_name, wf_cwl, yaml, actual_path) {
    // Create new WF object
    let new_workflow = new Workflow(wf_name, wf_cwl, yaml, actual_path);
    // Send the new workflow to the main process which will submit to WFM and add to DB
    // ipcRenderer.send('new-workflow', new_workflow)
    // add the wf object to the wf map keyed on its ID
    //workflows.set(wf_id, new_workflow)

    // Make this workflow appear in the main workflow section
    set_current_workflow(new_workflow);

    // Add wf to the navigation list
    client.submit_workflow(new_workflow);
    workflow_list.add(new_workflow);
    // Remove the welcome message if currently displayed
     if (currentContent === welcomeMessage) {
         currentContent = currentWorkflow;
     }
}

// Delete workflows
function delete_workflow(wf_id) {
   workflow = workflows(wf_id) 
}

function archive_workflow(wf_id) {  
   workflows = workflows(wf_id) 
}

// Set the current workflow
function set_current_workflow(workflow) {
    let current_wf_status = document.getElementById('current-wf_status') 
    let current_wf_location = document.getElementById('current-wf_location') 
    let current_wf_name = document.getElementById('current-wf_name') 

    // Modify the variables used for the current workflow
    // current_wf_status.innerHTML = workflow.status
    current_wf_status.innerHTML = workflow.status
    current_wf_location.innerHTML = workflow.locations
    current_wf_name.innerHTML = workflow.name
}

// Set the things we want to export
module.exports = { initialize, workflows, add_workflow, Workflow }
