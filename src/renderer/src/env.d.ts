/// <reference types="vite/client" />

import type { ElectronAPI } from '@electron-toolkit/preload'

type ChatServerInfo = {
  url: string
  configured: boolean
}

declare global {
  interface Window {
    electron: ElectronAPI
    electronAPI: {
      getChatApiUrl: () => Promise<ChatServerInfo>
      selectKnowledgeFolder: () => Promise<string | null>
      indexKnowledge: (folderPath: string) => Promise<number>
      getIndexMeta: () => Promise<{ chunkCount: number; indexedAt: string } | null>
      searchChunks: (query: string) => Promise<Array<{ id: string; text: string; filePath: string; chunkIndex: number; score: number }>>
    }
  }
}

export {}
