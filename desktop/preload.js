/**
 * preload.js — context bridge between Electron main and renderer
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  scanUrl: (url) => ipcRenderer.invoke('scan-url', url),
  crawlSite: (url, maxPages) => ipcRenderer.invoke('crawl-site', url, maxPages),
  onCrawlProgress: (fn) => {
    const handler = (_e, data) => fn(data);
    ipcRenderer.on('crawl-progress', handler);
    return () => ipcRenderer.removeListener('crawl-progress', handler);
  },
  savePdf: () => ipcRenderer.invoke('save-pdf'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
});