const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
    'electron',
    {
        // Environment variables
        env: {
            NODE_ENV: process.env.NODE_ENV
        },
        // IPC communication
        send: (channel, data) => {
            // Whitelist channels
            const validChannels = ['settings:updated', 'project:changed', 'screenshot:start', 'screenshot:stop'];
            if (validChannels.includes(channel)) {
                ipcRenderer.send(channel, data);
            }
        },
        receive: (channel, func) => {
            const validChannels = ['voice:status'];
            if (validChannels.includes(channel)) {
                ipcRenderer.on(channel, (event, ...args) => func(...args));
            }
        },
        onScreenshotAnalysis: (callback) => {
            ipcRenderer.on('screenshot:analysis', (event, data) => callback(data));
        },
        onScreenshotError: (callback) => {
            ipcRenderer.on('screenshot:error', (event, data) => callback(data));
        },
    }
);

contextBridge.exposeInMainWorld('darkMode', {
  toggle: () => ipcRenderer.invoke('dark-mode:toggle'),
  system: () => ipcRenderer.invoke('dark-mode:system')
})


// Expose voice chat functionality to renderer
contextBridge.exposeInMainWorld('voiceChat', {
  startListening: () => ipcRenderer.invoke('voice:start-listening'),
  stopListening: () => ipcRenderer.invoke('voice:stop-listening'),
  toggleMute: () => ipcRenderer.invoke('voice:toggle-mute'),
  setOutputDevice: (deviceId) => ipcRenderer.invoke('voice:set-output-device'),
  getDevices: () => ipcRenderer.invoke('voice:get-devices')
});
