// Modules
const {app, BrowserWindow, ipcMain} = require('electron')
//const  lib = require('lib')

// Used to handle error in MacOS systems
if (app.getGPUFeatureStatus().gpu_compositing.includes("disabled")) {
    app.disableHardwareAcceleration();
}

// Need global reference to window object so it doesn't 
// get garbage collected and close the window
let mainWindow

// Creates the main application window
function createWindow () {
  mainWindow = new BrowserWindow({
    // TODO Change width and height so it's proportionl to the screen size
    width: 1400, height: 1000,
    webPreferences: {
      // --- !! IMPORTANT !! ---
      // Disable 'contextIsolation' to allow 'nodeIntegration'
      // 'contextIsolation' defaults to "true" as from Electron v12
      contextIsolation: false,
      nodeIntegration: true
    }
  })

  // Load main.html into the new BrowserWindow
  mainWindow.loadFile('renderer/main.html')

  //let wc = mainWindow.webContents

  // Open DevTools - Remove for PRODUCTION!
  mainWindow.webContents.openDevTools();

  // Listen for window being closed
  mainWindow.on('closed',  () => {
    mainWindow = null
  })
}

// Create app window when ready
app.on('ready', createWindow)

// Close applicaition when all windows are closed unless on macOS 
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

// When app icon is clicked and app is running, (macOS) recreate the BrowserWindow
app.on('activate', () => {
  if (mainWindow === null) createWindow()
})
