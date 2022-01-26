// Renderer script
const {ipcRenderer} = require('electron')
//var components = require('./components.js')
var display = require('./display.js')
var workflows = require('./workflows.js')
var database = require('./database.js')

// Start up data from database
database.init()

// Initialize component objects and set listeners 
display.addComponent('welcomeMessage')
// display.addComponent('currentWorkflow')
display.addComponent('addWorkflow', 'add-wf_button', 'add-wf_submit')
display.addComponent('deleteWorkflow', 'delete-wf_button')
display.addComponent('archiveWorkflow', 'archive-wf_button')
display.addComponent('settings', 'settings-button')

// Initialize content
display.initContent()

// Load workflows from gdb
workflows.initialize('workflowList')
//workflows.add_workflow('clamr', 'oww', 'fog', 'pathu');
//workflows.add_workflow('vasp', 'oww', 'fog', 'pathu');
//database.delete_wf(42)
//database.add_wf(42)
//wfs = database.get_wfs()
//console.log(wfs)
//database.add_task(14, 43, 'Fog', 'ls')
//tasks = database.get_tasks(42)
////console.log(tasks)
//database.add_task(13, 42, 'Fog', 'ls')
//database.add_task(14, 42, 'Fog', 'ls')
//tasks = database.get_tasks(42)
//console.log(tasks)
//database.delete_wf(42)
// database.add_wf(42)
// const wf = database.get_wf(42)
// 
// console.log(wf)
// database.add_task(13, 42, 'Fog', 'cat')


// This will be enabled when we set nodeIntegration and contextIsolation to false/true
// Need to do it carefully so commenting this out for now
// (async () => {
//     const response = await window.api.dbAdd([1,2,3]);
//     console.log(response); // we now have the response from the main thread without exposing
//                            // ipcRenderer, leaving the app less vulnerable to attack    
// })();
