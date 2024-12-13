const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

// Store the main window as a global reference to prevent garbage collection
let mainWindow;

// Configuration for our window
const windowConfig = {
    width: 400,
    height: 600,
    minWidth: 300, // Prevent window from becoming too small
    minHeight: 400,
    webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        // Enable remote module for easier IPC if needed later
        enableRemoteModule: true,
        // Disable web security in development only
        webSecurity: !isDev,
        allowRunningInsecureContent: true,
        experimentalFeatures: true
    },
    // Window styling
    alwaysOnTop: true,
    frame: true, // Show window frame
    backgroundColor: '#1a1a1a', // Match your dark theme to prevent white flash
    show: false // Don't show until ready
};


// Add these to your existing main.js
function setupVoiceIPC() {
  let recognitionProcess = null;

  ipcMain.handle('voice:start-listening', async () => {
    if (mainWindow) {
      // Notify renderer that we're starting to listen
      mainWindow.webContents.send('voice:status', { isListening: true });
    }
  });

  ipcMain.handle('voice:stop-listening', async () => {
    if (mainWindow) {
      mainWindow.webContents.send('voice:status', { isListening: false });
    }
  });

  ipcMain.handle('voice:get-devices', async () => {
    if (mainWindow) {
      const devices = await mainWindow.webContents.executeJavaScript(`
        navigator.mediaDevices.enumerateDevices()
      `);
      return devices;
    }
    return [];
  });
}

function createWindow() {
    // Create browser window with our config
    mainWindow = new BrowserWindow(windowConfig);

    // Load the app
    mainWindow.loadFile('index.html');

    // Show window when ready to prevent white flash
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    if (isDev) {
        // Set up electron-connect for live reload
        require('electron-connect').client.create(mainWindow);
        mainWindow.webContents.openDevTools();

        // Watch for crashes in development
        mainWindow.webContents.on('crashed', (event) => {
            console.error('Renderer process crashed:', event);
        });
    }

    setupVoiceIPC();

    // Add permissions for microphone
    mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
        const allowedPermissions = ['media', 'microphone'];
        if (allowedPermissions.includes(permission)) {
        callback(true);
        } else {
        callback(false);
        }
    });

    // Handle window closed event
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Log any load failures
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.error('Failed to load:', errorCode, errorDescription);
    });

}

// Create window when Electron is ready
app.whenReady().then(() => {
    createWindow();

    // Handle MacOS activation
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Quit when all windows are closed, except on MacOS
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});

// Handle any unhandled promise rejections
process.on('unhandledRejection', (error) => {
    console.error('Unhandled rejection:', error);
});
