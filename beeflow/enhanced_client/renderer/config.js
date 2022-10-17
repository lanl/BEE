const db = require('./database.js');
const tunnel = require('./tunnel.js');
config = null;

function init(moniker, bolt_port, wfm_port) {
    config = new Config(moniker, bolt_port, wfm_port);
    db.add_config(moniker, bolt_port, wfm_port);
    tunnel.start_tunnel(9999, wfm_port, moniker, 'fg-rfe1');
    tunnel.start_tunnel(9995, bolt_port, moniker, 'fg-rfe1');
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
    constructor(moniker, bolt_port, wfm_port) {
        this.moniker = moniker;
        this.bolt_port = bolt_port;
        this.wfm_port = wfm_port;
    }
}

module.exports = { init }
