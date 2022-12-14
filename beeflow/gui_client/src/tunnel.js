const { spawn } = require('child_process');
const fs = require('fs');

export class Tunnel {
  constructor(hostname, moniker, listeners) {
    this.hostname = hostname;
    this.moniker = moniker;
    this.listeners = listeners;
  }

  /// Start the tunnel
  start() {
    let out = fs.openSync('./out.log', 'a');
    let err = fs.openSync('./out.log', 'a');

    let args = ['-fN'];
    for (const listener of this.listeners) {
      let localPort = listener.localPort;
      args.push('-L');
      if (Object.hasOwn(listener, 'remotePort')) {
        args.push(`${localPort}:localhost:${listener.remotePort}`);
      } else {
        args.push(`${localPort}:${listener.remoteSocket}`);
      }
    }
    args.push(`${this.moniker}@${this.hostname}`);

    const tunnel = spawn('ssh', args, {
        //stdio: ['ignore', out, err],
        stdio: 'ignore',
        shell: false,
        detach: true
      }
    );
    console.log(`Launched 'ssh ${args.join(" ")}' (pid: ${tunnel.pid})`);

    return tunnel;
  }
}
