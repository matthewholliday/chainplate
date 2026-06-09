"use strict";
const electron = require("electron");
const preload = require("@electron-toolkit/preload");
const electronAppAPI = {
  getChatApiUrl: () => electron.ipcRenderer.invoke("chat:getApiUrl"),
  selectKnowledgeFolder: () => electron.ipcRenderer.invoke("dialog:selectFolder"),
  indexKnowledge: (workspaceId, folderPath) => electron.ipcRenderer.invoke("knowledge:index", workspaceId, folderPath),
  getIndexMeta: (workspaceId) => electron.ipcRenderer.invoke("knowledge:getIndexMeta", workspaceId),
  searchChunks: (workspaceId, query) => electron.ipcRenderer.invoke("knowledge:searchChunks", workspaceId, query)
};
if (process.contextIsolated) {
  try {
    electron.contextBridge.exposeInMainWorld("electron", preload.electronAPI);
    electron.contextBridge.exposeInMainWorld("electronAPI", electronAppAPI);
  } catch (error) {
    console.error(error);
  }
} else {
  window.electron = preload.electronAPI;
  window.electronAPI = electronAppAPI;
}
