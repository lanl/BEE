const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld( 'api', {
    dbAdd: async(arg) => {
        return await ipcRender.invoke('db-add', arg)
    }
});
