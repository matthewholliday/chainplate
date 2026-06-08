import { ElectronAPI } from '@electron-toolkit/preload'
import type { ChatServerInfo } from './index'

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
