// Renderer script
const {ipcRenderer} = require('electron')
//var components = require('./components.js')
var display = require('./display.js')
var workflows = require('./workflows.js')

// Load up data from database

// Initialize component objects and set listeners 
display.addComponent('welcomeMessage')
// display.addComponent('currentWorkflow')
display.addComponent('addWorkflow', 'add-wf_button', 'add-wf_submit')
display.addComponent('deleteWorkflow', 'delete-wf_button')
// display.addComponent('archiveWorkflow', 'archive-wf_button')
// display.addComponent('settings', 'settings-button')

// Initialize content
display.initContent()

// Load workflows from gdb
workflows.loadWorkflows()

