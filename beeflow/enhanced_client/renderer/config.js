const db = require('./database.js');
const tunnel = require('./tunnel.js');
config = null;

function init(hostname, moniker, bolt_port, wfm_sock) {
    config = new Config(hostname, moniker, bolt_port, wfm_sock);
    db.add_config(moniker, bolt_port, wfm_sock);
    // tunnel.start_tunnel(9999, moniker, hostname, remote_socket = wfm_sock);
    // tunnel.start_tunnel(9995, moniker, hostname, remote_port = bolt_port);
    let tun = new tunnel.Tunnel(hostname, moniker, [
        {
            local_port: 9999,
            remote_socket: wfm_sock,
        },
        {
            local_port: 9995,
            remote_port: bolt_port,
        },
    ]);
    tun.start();
}

function getWFMTunnel() {
    return config.wfm_tunnel_port;
}

function configLoaded() {
    if (config !== null) {
        return true;
    }
    else {
        return false;
    }
}

class Config {
    constructor(hostname, moniker, bolt_port, wfm_sock) {
        this.hostname = hostname;
        this.moniker = moniker;
        this.bolt_port = bolt_port;
        this.wfm_sock = wfm_sock;
    }
}

module.exports = { init }
