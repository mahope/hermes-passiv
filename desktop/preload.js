/**
 * preload.js — context bridge between Electron main and renderer
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Scanning
  scanUrl: (url) => ipcRenderer.invoke('scan-url', url),
  crawlSite: (url, maxPages) => ipcRenderer.invoke('crawl-site', url, maxPages),
  onCrawlProgress: (fn) => {
    const handler = (_e, data) => fn(data);
    ipcRenderer.on('crawl-progress', handler);
    return () => ipcRenderer.removeListener('crawl-progress', handler);
  },

  // Reports
  savePdf: () => ipcRenderer.invoke('save-pdf'),
  saveJsonReport: (data) => ipcRenderer.invoke('save-json-report', data),
  saveCsvReport: (data) => ipcRenderer.invoke('save-csv-report', data),

  // External
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // License
  getLicense: () => ipcRenderer.invoke('get-license'),
  activateLicense: (key) => ipcRenderer.invoke('activate-license', key),
  deactivateLicense: () => ipcRenderer.invoke('deactivate-license'),
  onShowLicenseDialog: (fn) => {
    const handler = () => fn();
    ipcRenderer.on('show-license-dialog', handler);
    return () => ipcRenderer.removeListener('show-license-dialog', handler);
  },

  // Batch scan (Pro)
  batchScan: (urls) => ipcRenderer.invoke('batch-scan', urls),
  onBatchProgress: (fn) => {
    const handler = (_e, data) => fn(data);
    ipcRenderer.on('batch-progress', handler);
    return () => ipcRenderer.removeListener('batch-progress', handler);
  },

  // Version
  getVersion: () => ipcRenderer.invoke('get-version'),
});