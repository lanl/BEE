const { spawn } = require('child_process');
const fs = require('fs')

// Spawn an SSH tunnel connection
function connect(opts) {
  let out = fs.openSync('./out.log', 'a');
  let args = [
    '-fN',
    '-L',
    `${opts.port}:localhost:${opts.port}`,
    `${opts.moniker}@${opts.hostname}`,
  ];

  const tunnel = spawn('ssh', args, {
    stdio: ['ignore', out, out],
    shell: false,
    detach: true,
  });

  process.on('exit', () => {
    tunnel.kill();
  });
}

module.exports = { connect };
