import 'dotenv/config'

import { app, shell, BrowserWindow, ipcMain, Menu, dialog, nativeTheme } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import {
  getChatServerInfo,
  startChatServer,
  stopChatServer,
  type ChatServerInfo
} from './chat-server'
import {
  deleteProviderConfig,
  getProviderConfigStatuses,
  initializeProviderConfig,
  saveProviderConfig
} from './provider-config'
import type { ProviderConfig } from '../shared/models'

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 780,
    minWidth: 640,
    minHeight: 480,
    show: false,
    backgroundColor: '#252525',
    title: 'Chainplate',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
    mainWindow.webContents.on('console-message', (_event, _level, message) => {
      console.log(`[renderer] ${message}`)
    })
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  nativeTheme.themeSource = 'dark'

  Menu.setApplicationMenu(null)

  electronApp.setAppUserModelId('com.chainplate.chat')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.handle('dialog:selectFolder', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog({
      properties: ['openDirectory', 'createDirectory']
    })
    return canceled ? null : filePaths[0]
  })

  ipcMain.handle('knowledge:index', async (_event, workspaceId: string, folderPath: string) => {
    const { indexKnowledge } = await import('./knowledge-indexer')
    return indexKnowledge(workspaceId, folderPath)
  })

  ipcMain.handle('knowledge:getIndexMeta', async (_event, workspaceId: string) => {
    const { getIndexMeta } = await import('./knowledge-indexer')
    return getIndexMeta(workspaceId)
  })

  ipcMain.handle('knowledge:searchChunks', async (_event, workspaceId: string, query: string) => {
    const { searchChunks } = await import('./knowledge-indexer')
    return searchChunks(workspaceId, query)
  })

  ipcMain.handle('chat:getApiUrl', (): ChatServerInfo => {
    const info = getChatServerInfo()
    if (!info) {
      throw new Error('Chat server is not running')
    }
    return info
  })

  ipcMain.handle('provider:getConfigs', () => getProviderConfigStatuses())

  ipcMain.handle(
    'provider:saveConfig',
    (_event, config: ProviderConfig, apiKey?: string) => saveProviderConfig(config, apiKey)
  )

  ipcMain.handle('provider:deleteConfig', (_event, providerId: string) => {
    deleteProviderConfig(providerId)
  })

  initializeProviderConfig()
  await startChatServer()
  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  stopChatServer()
})
