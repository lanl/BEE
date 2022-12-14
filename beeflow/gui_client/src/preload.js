// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

const { contextBridge, ipcRenderer } = require('electron');

// Expose API calls between the renderer and the background process
contextBridge.exposeInMainWorld('beeflow', {
  submitWorkflow: (data) => ipcRenderer.invoke('submitWorkflow', data),
  startWorkflow: (data) => ipcRenderer.invoke('startWorkflow', data),
  // deleteWorkflow: (data) => ipcRenderer.invoke('deleteWorkflow', data),
  cancelWorkflow: (data) => ipcRenderer.invoke('cancelWorkflow', data),
  getWorkflowStatus: (data) => ipcRenderer.invoke('getWorkflowStatus', data),
  getWorkflows: (data) => ipcRenderer.invoke('getWorkflows', data),

  getClusters: (data) => ipcRenderer.invoke('getClusters', data),
  createCluster: (data) => ipcRenderer.invoke('createCluster', data),
  deleteCluster: (data) => ipcRenderer.invoke('deleteCluster', data),
  updateCluster: (data) => ipcRenderer.invoke('updateCluster', data),
  connectCluster: (data) => ipcRenderer.invoke('connectCluster', data),
});
