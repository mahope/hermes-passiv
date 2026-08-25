/**
 * main.js — Electron main process
 * EAA Compliance Scanner Desktop
 */
const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 720,
    minWidth: 640,
    minHeight: 480,
    title: 'EAA Compliance Scanner',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile('index.html');
  mainWindow.on('closed', () => { mainWindow = null; });
}

const menuTemplate = [
  {
    label: 'File',
    submenu: [
      { label: 'Save Report as PDF', accelerator: 'CmdOrCtrl+P', click: () => mainWindow?.webContents?.printToPDF({}).then(data => {
        dialog.showSaveDialog(mainWindow, {
          defaultPath: `eaa-scan-report-${Date.now()}.pdf`,
          filters: [{ name: 'PDF', extensions: ['pdf'] }],
        }).then(r => {
          if (!r.canceled && r.filePath) {
            fs.writeFileSync(r.filePath, data);
          }
        });
      }) },
      { type: 'separator' },
      { role: 'quit' },
    ],
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
      { role: 'cut' }, { role: 'copy' }, { role: 'paste' },
    ],
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' }, { role: 'toggleDevTools' }, { type: 'separator' },
      { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
    ],
  },
  {
    label: 'Help',
    submenu: [
      { label: 'About EAA Scanner', click: () => {
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: 'EAA Compliance Scanner',
          message: 'EAA Compliance Scanner v1.1.1',
          detail: 'WCAG 2.1 AA automated scanner for web developers and QA.\n\nBuilt by Mahope · https://hermes-passiv.pages.dev',
        });
      }},
    ],
  },
];

app.whenReady().then(() => {
  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

// IPC: single-page scan
ipcMain.handle('scan-url', async (event, url) => {
  const { scanUrl } = require('./scanner.js');
  try {
    const result = await scanUrl(url);
    return result;
  } catch (e) {
    return { ok: false, error: e.message, score: null, findings: [], summary: {} };
  }
});

// IPC: whole-site crawl (maxPages clamped to sane range)
ipcMain.handle('crawl-site', async (event, url, maxPages) => {
  const { crawlSite } = require('./scanner.js');
  const n = Math.max(1, Math.min(200, Number(maxPages) || 10));
  try {
    const result = await crawlSite(url, n, 15000,
      (rep, done, total) => {
        try {
          event.sender.send('crawl-progress', { target: rep.target, done, total });
        } catch { /* window may be gone */ }
      });
    return result;
  } catch (e) {
    return { ok: false, error: e.message, pages: [], aggregate: {} };
  }
});

// IPC: handle save PDF
ipcMain.handle('save-pdf', async () => {
  if (!mainWindow) return { ok: false, error: 'no window' };
  try {
    const data = await mainWindow.webContents.printToPDF({});
    const r = await dialog.showSaveDialog(mainWindow, {
      defaultPath: `eaa-scan-report-${Date.now()}.pdf`,
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
    });
    if (!r.canceled && r.filePath) {
      fs.writeFileSync(r.filePath, data);
      return { ok: true, path: r.filePath };
    }
    return { ok: false, error: 'cancelled' };
  } catch (e) {
    return { ok: false, error: e.message };
  }
});

// IPC: handle open external link
ipcMain.handle('open-external', async (event, url) => {
  const { shell } = require('electron');
  await shell.openExternal(url);
  return { ok: true };
});