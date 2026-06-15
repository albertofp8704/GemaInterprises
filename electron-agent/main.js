const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const fs   = require('fs');

let win;

function loadConfig() {
  const p = path.join(__dirname, 'config.json');
  try { return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {}; }
  catch(e) { return {}; }
}

function createWindow() {
  const cfg = loadConfig();
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  win = new BrowserWindow({
    width:  480,
    height: 820,
    x: width  - 500,
    y: height - 840,
    transparent:   true,
    frame:         false,
    alwaysOnTop:   true,
    skipTaskbar:   false,
    resizable:     false,
    movable:       false,   // drag handled via IPC
    hasShadow:     false,
    backgroundColor: '#00000000',
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      nodeIntegration:  false,
      contextIsolation: true,
    }
  });

  win.loadFile('agent.html');

  // Transparent areas pass mouse events through to OS
  win.setIgnoreMouseEvents(true, { forward: true });

  // Dev tools (uncomment to debug)
  // win.webContents.openDevTools({ mode: 'detach' });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());

// ── IPC ──────────────────────────────────────────────────────────

// Hover over an element — restore mouse events
ipcMain.on('mouse-enable',  () => win.setIgnoreMouseEvents(false));
// Leave all elements — pass-through again
ipcMain.on('mouse-disable', () => win.setIgnoreMouseEvents(true, { forward: true }));

// Drag the window by moving it manually
ipcMain.on('drag-window', (_, { x, y }) => {
  win.setPosition(Math.round(x), Math.round(y));
});

// Renderer asks where the window is (for drag offset)
ipcMain.handle('get-win-pos', () => win.getPosition());

// Config (API keys live on disk, never hard-coded)
ipcMain.handle('get-config', () => loadConfig());

// Close
ipcMain.on('quit-app', () => app.quit());
