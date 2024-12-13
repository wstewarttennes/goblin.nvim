const { contextBridge, ipcRenderer } = require('electron/renderer')

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

