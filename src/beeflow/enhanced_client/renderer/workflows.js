/* 
 * This file contains code that manages workflows in the app
 *
 *
 */

// Load workflows from database
function loadWorkflows() {
    // Load all the workflows from the database
}

class Workflow {
    // Constructor for workflow object
    constructor(wf_name, wf_cwl, locations, actual_path) {
        this.name = wf_name
        this.cwl = wf_cwl
        this.locations = locations
        this.path = actual_path
        this.status = 'Pending'
    }
}

// Add a new workflow 
function add_workflow(wf_name, wf_cwl, locations, actual_path) {
    // Create new WF object
    let new_workflow = new Workflow(wf_name, wf_cwl, locations, actual_path);
    wf_id = '42'
    // Send the new workflow to the main process which will submit to WFM and add to DB
    // ipcRenderer.send('new-workflow', new_workflow)
    // add the wf object to the wf map keyed on its ID
    workflows.set(wf_id, new_workflow)

    // Make this workflow appear in the main workflow section
    set_current_workflow(wf_id)

    // Add wf to navigation bar
    navbar_add(wf_id);
    // Remove the welcome message if currently displayed
     if (currentContent === welcomeMessage) {
         currentContent = currentWorkflow
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
function set_current_workflow(wf_id) {
    workflow = workflows.get(wf_id)
    let current_wf_status = document.getElementById('current-wf_status') 
    let current_wf_location = document.getElementById('current-wf_location') 
    let current_wf_name = document.getElementById('current-wf_name') 

    // Modify the variables used for the current workflow
    // current_wf_status.innerHTML = workflow.status
    current_wf_status.innerHTML = workflow.status
    current_wf_location.innerHTML = workflow.locations
    current_wf_name.innerHTML = workflow.name
}

const workflows = new Map();

// Set the things we want to export
module.exports = { workflows, add_workflow, Workflow, loadWorkflows }
