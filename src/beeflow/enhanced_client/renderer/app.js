// Renderer script
const {ipcRenderer} = require('electron')
//var components = require('./components.js')
var display = require('./display.js')
var workflows = require('./workflows.js')
//var database = require('./database.js')

// Load up data from database

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
workflows.loadWorkflows()
//database.initialize()


// This will be enabled when we set nodeIntegration and contextIsolation to false/true
// Need to do it carefully so commenting this out for now
// (async () => {
//     const response = await window.api.dbAdd([1,2,3]);
//     console.log(response); // we now have the response from the main thread without exposing
//                            // ipcRenderer, leaving the app less vulnerable to attack    
// })();
