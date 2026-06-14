/// <reference types="vite/client" />

import type { ElectronAPI } from '@electron-toolkit/preload'
import type { ProviderConfig, ProviderConfigStatus } from '@shared/models'

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
      indexKnowledge: (workspaceId: string, folderPath: string) => Promise<number>
      getIndexMeta: (workspaceId: string) => Promise<{ chunkCount: number; indexedAt: string; folderPath?: string } | null>
      searchChunks: (workspaceId: string, query: string) => Promise<Array<{ id: string; text: string; filePath: string; chunkIndex: number; score: number }>>
      getProviderConfigs: () => Promise<ProviderConfigStatus[]>
      saveProviderConfig: (config: ProviderConfig, apiKey?: string) => Promise<ProviderConfigStatus>
      deleteProviderConfig: (providerId: string) => Promise<void>
    }
  }
}

export {}
