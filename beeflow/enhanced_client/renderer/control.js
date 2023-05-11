const viz = require('./viz.js');
const tunnel = require('./tunnel.js');

// Set up control handlers for the page
function setup(opts) {
  let hostname = document.getElementById(opts.hostname);
  let hostnameError = document.getElementById(opts.hostnameError);
  let moniker = document.getElementById(opts.moniker);
  let monikerError = document.getElementById(opts.monikerError);
  let boltPort = document.getElementById(opts.boltPort);
  let boltPortError = document.getElementById(opts.boltPortError);
  let submitButton = document.getElementById(opts.submitButton);
  let reloadButton = document.getElementById(opts.reloadButton);

  function draw() {
    viz.draw(opts.vizContainer, boltPort.value)
      .catch(err => {
        opts.showErrorMessage('An error occurred while establishing a connection. Please check your configuration.');
        console.log('Connection/Drawing error:');
        console.log(err);
      });
  }

  let validateFields = [
    [hostname, hostnameError, "Hostname"],
    [moniker, monikerError, "Moniker"],
    [boltPort, boltPortError, "Bolt Port"],
  ];
  submitButton.addEventListener('click', ev => {
    // Reset all input error messages
    hostnameError.innerText = "";
    monikerError.innerText = "";
    boltPortError.innerText = "";
    // Check for empty inputs
    let ok = true;
    for (let [field, error, name] of validateFields) {
      if (field.value.trim().length == 0) {
        error.innerText = `* ${name} cannot be empty`;
        ok = false;
      }
    }

    // An error occurred
    if (!ok) {
      return;
    }

    // Set up the tunnel and draw
    tunnel.connect({
      hostname: hostname.value,
      moniker: moniker.value,
      port: boltPort.value,
    });
    // Wait 10 seconds for the tunnel to set up
    let message = opts.showMessage('Connecting...');
    setTimeout(() => {
      message.remove();
      draw();
    }, 10000);
  });

  reloadButton.addEventListener('click', ev => {
    draw();
  });
}

module.exports = { setup };
