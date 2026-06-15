const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('gema', {
  enableMouse:  ()      => ipcRenderer.send('mouse-enable'),
  disableMouse: ()      => ipcRenderer.send('mouse-disable'),
  dragWindow:   (pos)   => ipcRenderer.send('drag-window', pos),
  getWinPos:    ()      => ipcRenderer.invoke('get-win-pos'),
  getConfig:    ()      => ipcRenderer.invoke('get-config'),
  saveConfig:   (data)  => ipcRenderer.send('save-config', data),
  quit:         ()      => ipcRenderer.send('quit-app'),
});
