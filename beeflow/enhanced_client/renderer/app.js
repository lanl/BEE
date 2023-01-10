// Renderer script
const {ipcRenderer} = require('electron');

// Helper function for showing an error message in the page sidebar
function showErrorMessage(containerId, message) {
  let div = document.createElement('div');
  div.className = 'notification is-danger mb-4';
  // Button to remove old error messages
  let deleteButton = document.createElement('button');
  deleteButton.className = 'delete';
  deleteButton.addEventListener('click', ev => {
    div.remove();
  });
  div.appendChild(deleteButton);
  div.appendChild(document.createTextNode(message));
  // Add it to the container
  let container = document.getElementById(containerId);
  container.appendChild(div);
}

const control = require('./control.js');
control.setup({
  showErrorMessage: (message) => showErrorMessage('error', message),
  hostname: 'settings-hostname',
  hostnameError: 'settings-hostname-error',
  moniker: 'settings-moniker',
  monikerError: 'settings-moniker-error',
  boltPort: 'settings-bolt_port',
  boltPortError: 'settings-bolt_port-error',
  submitButton: 'settings-submit',
  reloadButton: 'reload-button',
  vizContainer: 'viz',
});

/*
let viz = require('./viz.js');
viz.draw('viz', 34273);
*/
