// Renderer script and main app script

// Helper function for showing messages in the page sidebar
function showMessage(containerId, className, message) {
  let div = document.createElement('div');
  div.className = className;
  // Button to remove old messages
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
  return div;
}

const control = require('./control.js');
control.setup({
  showErrorMessage: (message) => showMessage('messages', 'notification is-danger mb-4', message),
  showMessage: (message) => showMessage('messages', 'notification is-primary mb-4', message),
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
