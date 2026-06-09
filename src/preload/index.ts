import { contextBridge, ipcRenderer } from 'electron'

import { electronAPI } from '@electron-toolkit/preload'

export type ChatServerInfo = {
  url: string
  configured: boolean
}

const electronAppAPI = {
  getChatApiUrl: (): Promise<ChatServerInfo> => ipcRenderer.invoke('chat:getApiUrl'),
  selectKnowledgeFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:selectFolder'),
  indexKnowledge: (workspaceId: string, folderPath: string): Promise<number> =>
    ipcRenderer.invoke('knowledge:index', workspaceId, folderPath),
  getIndexMeta: (workspaceId: string): Promise<{ chunkCount: number; indexedAt: string; folderPath?: string } | null> =>
    ipcRenderer.invoke('knowledge:getIndexMeta', workspaceId),
  searchChunks: (workspaceId: string, query: string): Promise<Array<{ id: string; text: string; filePath: string; chunkIndex: number; score: number }>> =>
    ipcRenderer.invoke('knowledge:searchChunks', workspaceId, query),
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('electronAPI', electronAppAPI)
  } catch (error) {
    console.error(error)
  }
} else {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(window as any).electron = electronAPI
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(window as any).electronAPI = electronAppAPI
}
