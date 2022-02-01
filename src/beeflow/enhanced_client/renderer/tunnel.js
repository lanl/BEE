const { spawn } = require('child_process');
const fs = require('fs')

function start_tunnel(local_port, remote_port, moniker, resource) {

    out = fs.openSync('./out.log', 'a'),
    err = fs.openSync('./out.log', 'a');

    const tunnel = spawn('ssh', [
                '-fN',
                '-L', `${local_port}:localhost:${remote_port}`,
                `${moniker}@${resource}`
    ],  {
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

//function start_tunnel(local_port, remote_port) {
//    cluster = 'fg-rfe1';
//    moniker = 'rustyd';
//
//    // cluster = config.get_cluster()
//    // moniker = config.get_moniker()
//
//    out = fs.openSync('./out.log', 'a'),
//    err = fs.openSync('./out.log', 'a');
//
//    const tunnel = spawn('ssh', [
//                '-fN',
//                '-L', `${local_port}:localhost:${remote_port}`,
//                `${moniker}@${cluster}`
//    ],  {
//            //stdio: ['ignore', out, err],
//            stdio: 'ignore',
//            shell: false
//        }
//    );
//
//
//    console.log(tunnel.pid);
//
//    process.on('exit', () => {
//                tunnel.kill();
//    });
//}

start_tunnel(9999, 5088, 'rustyd', 'fg-rfe1');
module.exports = { start_tunnel }
