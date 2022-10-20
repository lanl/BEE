const { spawn } = require('child_process');
const fs = require('fs')

class Tunnel {
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
            let local_port = listener.local_port;
            args.push('-L');
            if (listener.hasOwnProperty('remote_port')) {
                args.push(`${local_port}:localhost:${listener.remote_port}`);
            } else {
                args.push(`${local_port}:${listener.remote_socket}`);
            }
        }
        args.push(`${this.moniker}@${this.hostname}`);

        console.log(`Launching 'ssh ${args.join(" ")}'`);
        const tunnel = spawn('ssh', args, {
                //stdio: ['ignore', out, err],
                stdio: 'ignore',
                shell: false,
                detach: true
            }
        );

        console.log(tunnel.pid);

        process.on('exit', () => {
            tunnel.kill();
        });
    }
}

module.exports = { Tunnel }
