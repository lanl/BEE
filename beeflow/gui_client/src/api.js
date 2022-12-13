import * as settings from './settings.js';
import {Tunnel} from './tunnel.js';

let workflows = [];

// Connect to bee on the remote system
export function connect(ev, data) {
  return `connecting to ${data.moniker}@${data.hostname}`;
}

export function submitWorkflow(ev, data) {
  console.log('submitWorkflow()');
  let wfID = workflows.length;
  workflows.push({
    wfID,
    name: data.workflowName,
  });
  return {
    wfID,
  };
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
  ipc.handle('connect', connect);
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
