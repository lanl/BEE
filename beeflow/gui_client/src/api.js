// import * as axios from 'axios';
import fetch from 'node-fetch';
import * as FormData from 'form-data';
import * as fs from 'fs'
import {Readable} from 'stream';
import * as settings from './settings.js';
import {Tunnel} from './tunnel.js';

let workflows = [];

// Start a cluster tunnel and invoke the callback, passing it wfmPort and
// gdbPort. This then kills the tunnel on completion of the callback.
function startClusterTunnel(clusterName, callback) {
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

  return settings.read()
    // Get the proper cluster config
    .then(config => config.clusters.find(cluster => cluster.hostname == clusterName))
    // Start the tunnel
    .then(cluster => {
      let tunnel = new Tunnel(cluster.hostname, cluster.moniker, [
        {
          localPort: wfmPort,
          remoteSocket: cluster.wfmSocketPath,
        },
        {
          localPort: gdbPort,
          remotePort: cluster.gdbPort,
        },
      ]);
      return tunnel.start();
    })
    // Wait 3 seconds
    .then(tunnel => wait(3 * 1000).then(() => tunnel))
    // Call the callback, and return a promise
    .then(tunnel => {
      let result = callback(wfmPort, gdbPort);
      console.log(tunnel);
      // Now kill the tunnel
      tunnel.kill();
      return result;
    });
}

// Create a config for an axios call
function request(method, url, body = null) {
  let headers = {
    'Authorization': 'Bearer ...',
  };
  if (body !== null) {
    Object.assign(headers, body.getHeaders());
  }
  console.log(url);
  let opts = {
    method,
    headers,
    // adapter: require('axios/lib/adapters/http'),
    body,
    // For 'no_proxy', if set incorrectly
    proxy: false,
  };
  return fetch(url, opts).then(resp => resp.json());
}

function resource(wfmPort, tag = '') {
  return `http://127.0.0.1:${wfmPort}/bee_wfm/v1/jobs/${tag}`;
}

export function submitWorkflow(ev, data) {
  console.log('submitWorkflow()');
  let result = startClusterTunnel(data.cluster, (wfmPort, gdbPort) => {
    let formData = new FormData();
    // formData.append('workflow_archive', Readable.from(new Uint8Array(data.tarball.data)));
    formData.append('workflow_archive', fs.createReadStream(data.tarball.path));
    formData.append('wf_filename', data.tarball.fname);
    formData.append('main_cwl', data.mainCwl);
    formData.append('yaml', data.yaml);
    formData.append('workdir', data.workdir);
    formData.append('wf_name', data.wfName);
    return request('post', resource(wfmPort), formData);
    // console.log(config);
    // return fetch(config);
  });
  return result
    .then(data => {
      let wfID = data['wf_id'];
      console.log(`Submitted workflow ${wfID}`);
      return {
        wfID,
        tasks: data['tasks'],
      };
    })
    .catch(error => {
      console.log(error);
      return error;
    });
}

export function startWorkflow(ev, data) {
  console.log('startWorkflow()');
}

export function cancelWorkflow(ev, data) {
  console.log('cancelWorkflow()');
}

export function getWorkflowStatus(ev, data) {
  console.log('getWorkflowStatus()');
}

export function getWorkflows(ev, data) {
  console.log('getWorkflows()');
  return workflows;
}

export function getClusters(ev, data) {
  return settings.read().then(info => info.clusters);
}

export function createCluster(ev, data) {
  console.log(`createCluster(${data})`);
  return settings.read()
    .then(info => {
      info.clusters.push(data);
      return settings.write(info);
    })
}

export function deleteCluster(ev, data) {
  console.log('deleteCluster()');
}

export function updateCluster(ev, data) {
  console.log('updateCluster()');
  return settings.read()
    .then(info => {
      console.log(`data.hostname: ${data.hostname}`);
      console.log(info.clusters.map(cluster => cluster.hostname));
      let i = info.clusters.findIndex(cluster => cluster.hostname == data.hostname);
      if (i == -1) {
        info.clusters.push(data);
      } else {
        info.clusters[i] = data;
      }
      console.log(info);
      return settings.write(info);
    })
  // TODO: fs stuff
}

const wfmPort = 18293;
const gdbPort = 12344;

export function connectCluster(ev, data) {
  console.log('connectCluster()');
  let tunnel = new Tunnel(data.hostname, data.moniker, [
    {
      localPort: wfmPort,
      remoteSocket: data.wfmSocketPath,
    },
    {
      localPort: gdbPort,
      remotePort: data.gdbPort,
    },
  ]);
  tunnel.start();
}

// Initialize the API exposed to the browser in the main process
export function initAPI(ipc) {
  ipc.handle('submitWorkflow', submitWorkflow);
  ipc.handle('startWorkflow', startWorkflow);
  ipc.handle('cancelWorkflow', cancelWorkflow);
  ipc.handle('getWorkflowStatus', getWorkflowStatus);
  ipc.handle('getWorkflows', getWorkflows);
  ipc.handle('getClusters', getClusters);
  ipc.handle('createCluster', createCluster);
  ipc.handle('deleteCluster', deleteCluster);
  ipc.handle('updateCluster', updateCluster);
  ipc.handle('connectCluster', connectCluster);
}
