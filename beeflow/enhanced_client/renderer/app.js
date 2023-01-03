// Renderer script
const {ipcRenderer} = require('electron');

var display = require('./display.js');
var workflows = require('./workflows.js');
var database = require('./database.js');

var fs = require('fs');

// Load up data from database
database.init();

// Initialize component objects and set listeners
display.addComponent('welcomeMessage');
display.addComponent('addWorkflow', 'add-wf_button', 'add-wf_submit');
display.addComponent('deleteWorkflow', 'delete-wf_button', 'delete-wf_submit');
display.addComponent('reexecuteWorkflow', 'reexecute-wf_button', 'reexecute-wf_submit');
display.addComponent('settingsList', 'settings-button');
display.addComponent('settings', 'settings-create-button', 'settings-submit');
display.addComponent('currentWorkflow');

display.startButton('start-wf_button');
display.resumeButton('resume-wf_button');
display.pauseButton('pause-wf_button');
display.updateButton('update-wf_button');
display.downloadButton('download-archive_button');

// Initialize content
display.initContent();
display.initWorkflows('workflowList');

// Load workflows from gdb
// workflows.initialize('workflowList');
