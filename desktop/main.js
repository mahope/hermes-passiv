/**
 * main.js — Electron main process
 * EAA Compliance Scanner Desktop
 */
const { app, BrowserWindow, Menu, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
const http = require('http');
const crypto = require('crypto');

let mainWindow = null;
const VERSION = '1.3.0';

// License file path (user data dir, persisted across restarts)
function licensePath() {
  return path.join(app.getPath('userData'), 'license.json');
}

function readLicense() {
  try {
    const raw = fs.readFileSync(licensePath(), 'utf8');
    return JSON.parse(raw);
  } catch { return null; }
}

function writeLicense(data) {
  const dir = path.dirname(licensePath());
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(licensePath(), JSON.stringify(data, null, 2), 'utf8');
}

// Device ID: stable per machine, hash of machine-id-ish data
function getDeviceId() {
  const seed = app.getPath('userData') + app.getVersion();
  return crypto.createHash('sha256').update(seed).digest('hex').slice(0, 16);
}

// Call the Cloudflare Worker license API
function apiLicenseCall(endpoint, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const url = new URL(`https://hermes-passiv.pages.dev/api/license/${endpoint}`);
    const mod = url.protocol === 'https:' ? https : http;
    const req = mod.request(url.href, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
        'User-Agent': 'EAA-ComplianceScanner/1.3 (desktop)',
      },
      timeout: 10000,
    }, (res) => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch { resolve({ ok: false, error: 'Invalid response from server.' }); }
      });
    });
    req.on('error', e => resolve({ ok: false, error: e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, error: 'Request timed out.' }); });
    req.write(data);
    req.end();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 960,
    height: 780,
    minWidth: 640,
    minHeight: 560,
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
      {
        label: 'Activate Pro License…',
        click: () => mainWindow?.webContents?.send('show-license-dialog'),
      },
      { type: 'separator' },
      {
        label: 'About EAA Scanner', click: () => {
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: 'EAA Compliance Scanner',
          message: `EAA Compliance Scanner v${VERSION}`,
          detail: 'WCAG 2.1 AA automated scanner for web developers and QA.\n\nFree tier: single-page and whole-site scanning, PDF reports.\nPro: batch URL scanning, CSV/JSON export, unlimited crawl depth.\n\nBuilt by Mahope · https://hermes-passiv.pages.dev',
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

// IPC: whole-site crawl
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

// IPC: save PDF
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

// IPC: open external link
ipcMain.handle('open-external', async (event, url) => {
  const { shell } = require('electron');
  await shell.openExternal(url);
  return { ok: true };
});

// IPC: get license status
ipcMain.handle('get-license', async () => {
  const lic = readLicense();
  if (!lic || !lic.key) return { ok: false, activated: false };
  // Validate locally: check expiry
  if (lic.expires_at && new Date(lic.expires_at) < new Date()) {
    return { ok: false, activated: false, expired: true };
  }
  return { ok: true, activated: true, plan: lic.plan || 'pro-yearly', expires_at: lic.expires_at || null };
});

// IPC: activate license
ipcMain.handle('activate-license', async (event, licenseKey) => {
  const key = String(licenseKey || '').trim().toLowerCase();
  if (!/^[a-f0-9]{32}$/.test(key)) {
    return { ok: false, error: 'Invalid license key format. Keys are 32 hex characters.' };
  }

  const deviceId = getDeviceId();
  const result = await apiLicenseCall('validate', {
    license_key: key,
    device_id: deviceId,
  });

  if (result.ok && result.valid) {
    writeLicense({
      key,
      plan: result.plan || 'pro-yearly',
      expires_at: result.expires_at || null,
      activated_at: new Date().toISOString(),
      device_id: deviceId,
    });
    return { ok: true, plan: result.plan, expires_at: result.expires_at };
  }

  return {
    ok: false,
    error: result.error || 'License activation failed. Check your key and try again.',
  };
});

// IPC: deactivate license (remove local file — the key stays valid for other devices)
ipcMain.handle('deactivate-license', async () => {
  try {
    fs.unlinkSync(licensePath());
    return { ok: true };
  } catch { return { ok: true }; }
});

// IPC: save JSON report (Pro feature)
ipcMain.handle('save-json-report', async (event, reportData) => {
  const r = await dialog.showSaveDialog(mainWindow, {
    defaultPath: `eaa-scan-report-${Date.now()}.json`,
    filters: [{ name: 'JSON', extensions: ['json'] }],
  });
  if (!r.canceled && r.filePath) {
    try {
      const data = typeof reportData === 'string' ? reportData : JSON.stringify(reportData, null, 2);
      fs.writeFileSync(r.filePath, data, 'utf8');
      return { ok: true, path: r.filePath };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }
  return { ok: false, error: 'cancelled' };
});

// IPC: save CSV report (Pro feature)
ipcMain.handle('save-csv-report', async (event, csvContent) => {
  const r = await dialog.showSaveDialog(mainWindow, {
    defaultPath: `eaa-scan-report-${Date.now()}.csv`,
    filters: [{ name: 'CSV', extensions: ['csv'] }],
  });
  if (!r.canceled && r.filePath) {
    try {
      fs.writeFileSync(r.filePath, csvContent, 'utf8');
      return { ok: true, path: r.filePath };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }
  return { ok: false, error: 'cancelled' };
});

// IPC: batch scan — scan multiple URLs sequentially (Pro feature)
ipcMain.handle('batch-scan', async (event, urlList) => {
  const { scanUrl } = require('./scanner.js');
  const urls = (Array.isArray(urlList) ? urlList : [urlList])
    .map(u => u.trim())
    .filter(u => u.length > 0)
    .slice(0, 100); // max 100 URLs

  if (urls.length === 0) return { ok: false, error: 'No valid URLs provided.' };

  const results = [];
  for (let i = 0; i < urls.length; i++) {
    const url = urls[i].startsWith('http') ? urls[i] : 'https://' + urls[i];
    try {
      const rep = await scanUrl(url);
      rep.target = url;
      results.push(rep);
    } catch (e) {
      results.push({ ok: false, error: e.message, target: url });
    }
    // Send progress
    try {
      event.sender.send('batch-progress', { done: i + 1, total: urls.length, current: url });
    } catch { /* ignore */ }
    await new Promise(r => setTimeout(r, 100)); // be polite
  }

  // Build aggregate
  const okPages = results.filter(p => p.ok);
  const totals = { errors: 0, warnings: 0, notices: 0 };
  for (const p of okPages) {
    totals.errors += p.summary.errors || 0;
    totals.warnings += p.summary.warnings || 0;
    totals.notices += p.summary.notices || 0;
  }
  const avgScore = okPages.length
    ? Math.round(okPages.reduce((s, p) => s + p.score, 0) / okPages.length) : null;

  return { ok: true, results, aggregate: {
    total: results.length,
    succeeded: okPages.length,
    failed: results.length - okPages.length,
    averageScore: avgScore,
    totalErrors: totals.errors,
    totalWarnings: totals.warnings,
    totalNotices: totals.notices,
  }};
});

// IPC: get version
ipcMain.handle('get-version', () => VERSION);