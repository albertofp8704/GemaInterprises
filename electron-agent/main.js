const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const fs   = require('fs');

let win;

// Config lives in %APPDATA%\GEMA Agent\config.json  (no manual file needed)
function configPath() {
  return path.join(app.getPath('userData'), 'config.json');
}

function loadConfig() {
  try {
    const p = configPath();
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch(e) {}
  return {};
}

function saveConfig(data) {
  try {
    const p = configPath();
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, JSON.stringify(data, null, 2));
  } catch(e) {}
}

function createWindow() {
  const cfg = loadConfig();
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  const defX = width  - 500;
  const defY = height - 840;
  const posX = (cfg.windowPosition?.x != null) ? cfg.windowPosition.x : defX;
  const posY = (cfg.windowPosition?.y != null) ? cfg.windowPosition.y : defY;

  win = new BrowserWindow({
    width:  480,
    height: 820,
    x: posX,
    y: posY,
    transparent:   true,
    frame:         false,
    alwaysOnTop:   true,
    skipTaskbar:   false,
    resizable:     false,
    movable:       false,
    hasShadow:     false,
    backgroundColor: '#00000000',
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      nodeIntegration:  false,
      contextIsolation: true,
    }
  });

  // If no API key configured → show setup screen
  if (!cfg.anthropicApiKey) {
    win.loadFile('setup.html');
  } else {
    win.loadFile('agent.html');
  }

  win.setIgnoreMouseEvents(true, { forward: true });

  // Persist position on move (debounced 800ms)
  let savePosTm;
  win.on('moved', () => {
    clearTimeout(savePosTm);
    savePosTm = setTimeout(() => {
      const [x, y] = win.getPosition();
      const cur = loadConfig();
      saveConfig({ ...cur, windowPosition: { x, y } });
    }, 800);
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());

// ── IPC ──────────────────────────────────────────────────────────
ipcMain.on('mouse-enable',  () => win && win.setIgnoreMouseEvents(false));
ipcMain.on('mouse-disable', () => win && win.setIgnoreMouseEvents(true, { forward: true }));
ipcMain.on('drag-window', (_, pos) => {
  if (!win || !pos) return;
  const x = Math.round(Number(pos.x));
  const y = Math.round(Number(pos.y));
  if (Number.isFinite(x) && Number.isFinite(y)) win.setPosition(x, y);
});
ipcMain.handle('get-win-pos', () => win ? win.getPosition() : [0, 0]);
ipcMain.handle('get-config',  () => loadConfig());
ipcMain.on('save-config', (_, data) => {
  saveConfig(data);
  // Reload main agent after saving
  win.loadFile('agent.html');
});
ipcMain.on('quit-app', () => app.quit());
