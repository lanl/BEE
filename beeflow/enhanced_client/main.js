// Modules
const {app, BrowserWindow, ipcMain} = require('electron')

app.allowRendererProcessReuse = true

// Used to handle error in MacOS systems
if (app.getGPUFeatureStatus().gpu_compositing.includes("disabled")) {
  app.disableHardwareAcceleration();
}

// Need global reference to window object so it doesn't
// get garbage collected and close the window
let mainWindow;

// Creates the main application window
function createWindow () {
  mainWindow = new BrowserWindow({
    // TODO Change width and height so it's proportionl to the screen size
    width: 1400, height: 1000,
    webPreferences: {
      // App needs to be modified so these can be changed to true and false
      contextIsolation: false,
      nodeIntegration: true,
      webSecurity: false,
      experimentalFeatures: true
    }
  })

  // Load main.html into the new BrowserWindow
  mainWindow.loadFile('renderer/main.html')

  // Open DevTools
  mainWindow.webContents.openDevTools();

  // Listen for window being closed
  mainWindow.on('closed',  () => {
    mainWindow = null
  })
}

// Create app window when ready
app.on('ready', createWindow)

// Close application when all windows are closed unless on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

// When app icon is clicked and app is running, (macOS) recreate the BrowserWindow
app.on('activate', () => {
  if (mainWindow === null) createWindow()
})

// Will be used to recieve database update messages from renderer when
// nodeIntegration is disabled
// ipcMain.handle('db-add', async (event, arg) => {
//     //  Add data to DB
//     await awaitableProcess();
//     return "Added";
// })
