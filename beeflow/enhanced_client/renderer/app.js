// Renderer script
const {ipcRenderer} = require('electron')
const { spawn } = require('child_process');

//var components = require('./components.js')
var display = require('./display.js')
var workflows = require('./workflows.js')
var database = require('./database.js')
//var tunnel = require('./tunnel.js')

var fs = require('fs');

// Load up data from database
database.init()

// Initialize component objects and set listeners 
display.addComponent('welcomeMessage')
display.addComponent('addWorkflow', 'add-wf_button', 'add-wf_submit')
display.addComponent('deleteWorkflow', 'delete-wf_button', 'delete-wf_submit')
display.addComponent('reexecuteWorkflow', 'reexecute-wf_button', 'reexecute-wf_submit')
display.addComponent('settings', 'settings-button', 'settings-submit')

display.startButton('start-wf_button')
display.resumeButton('resume-wf_button')
display.pauseButton('pause-wf_button')
display.updateButton('update-wf_button')
display.downloadButton('download-archive_button')

// Initialize content
display.initContent()

// Load workflows from gdb
workflows.initialize('workflowList')
