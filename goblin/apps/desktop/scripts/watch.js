// scripts/watch.js
const electronConnect = require('electron-connect').server;
const path = require('path');

// Create our electron-connect server
const electron = electronConnect.create({
    logLevel: 0, // Reduce console noise
    stopOnClose: true, // Ensure everything closes properly
});

// Start the Electron process
electron.start();

// Watch main process files
const mainFiles = [
    path.join(__dirname, '../main.js'),
    path.join(__dirname, '../preload.js')
];

// Watch renderer process files
const rendererFiles = [
    path.join(__dirname, '../index.html'),
    path.join(__dirname, '../src/**/*'),
    path.join(__dirname, '../styles/**/*')
];

// Restart the main process when main files change
require('chokidar')
    .watch(mainFiles, { ignoreInitial: true })
    .on('change', () => {
        console.log('Main process file changed - restarting...');
        electron.restart();
    });

// Reload renderer process when those files change
require('chokidar')
    .watch(rendererFiles, { ignoreInitial: true })
    .on('change', () => {
        console.log('Renderer process file changed - reloading...');
        electron.reload();
    });

// Handle process termination gracefully
process.on('SIGTERM', () => {
    electron.stop();
    process.exit(0);
});

process.on('SIGINT', () => {
    electron.stop();
    process.exit(0);
});
