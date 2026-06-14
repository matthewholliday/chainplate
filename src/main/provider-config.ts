import { app } from 'electron'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import { join } from 'path'
import {
  BUILT_IN_PROVIDERS,
  type ProviderConfig,
  type ProviderConfigStatus,
  type ProviderType
} from '../shared/models'

type StoredProviderData = {
  customProviders: ProviderConfig[]
  apiKeys: Record<string, string>
}

const CONFIG_FILE = 'provider-configs.json'

let cachedData: StoredProviderData | null = null

function getConfigPath(): string {
  const userData = app.getPath('userData')
  return join(userData, CONFIG_FILE)
}

function defaultStoredData(): StoredProviderData {
  const apiKeys: Record<string, string> = {}

  if (process.env.ANTHROPIC_API_KEY) {
    apiKeys.anthropic = process.env.ANTHROPIC_API_KEY
  }
  if (process.env.OPENAI_API_KEY) {
    apiKeys.openai = process.env.OPENAI_API_KEY
  }

  return {
    customProviders: [],
    apiKeys
  }
}

function isProviderType(value: unknown): value is ProviderType {
  return value === 'anthropic' || value === 'openai' || value === 'openai-compatible'
}

function isModelEntry(value: unknown): value is ProviderConfig['models'][number] {
  if (!value || typeof value !== 'object') return false
  const entry = value as { id?: unknown; label?: unknown; contextWindow?: unknown }
  return (
    typeof entry.id === 'string' &&
    entry.id.length > 0 &&
    typeof entry.label === 'string' &&
    entry.label.length > 0 &&
    (entry.contextWindow === undefined || typeof entry.contextWindow === 'number')
  )
}

function isProviderConfig(value: unknown): value is ProviderConfig {
  if (!value || typeof value !== 'object') return false
  const config = value as Partial<ProviderConfig>
  return (
    typeof config.id === 'string' &&
    config.id.length > 0 &&
    isProviderType(config.type) &&
    typeof config.label === 'string' &&
    config.label.length > 0 &&
    Array.isArray(config.models) &&
    config.models.every(isModelEntry) &&
    typeof config.isBuiltIn === 'boolean' &&
    (config.baseUrl === undefined || typeof config.baseUrl === 'string')
  )
}

function sanitizeStoredData(raw: unknown): StoredProviderData {
  const defaults = defaultStoredData()
  if (!raw || typeof raw !== 'object') return defaults

  const data = raw as Partial<StoredProviderData>
  const customProviders = Array.isArray(data.customProviders)
    ? data.customProviders.filter(isProviderConfig).filter((provider) => !provider.isBuiltIn)
    : []

  const apiKeys: Record<string, string> = { ...defaults.apiKeys }
  if (data.apiKeys && typeof data.apiKeys === 'object') {
    for (const [providerId, apiKey] of Object.entries(data.apiKeys)) {
      if (typeof apiKey === 'string' && apiKey.length > 0) {
        apiKeys[providerId] = apiKey
      }
    }
  }

  return {
    customProviders,
    apiKeys
  }
}

function loadStoredData(): StoredProviderData {
  if (cachedData) return cachedData

  const configPath = getConfigPath()
  if (!existsSync(configPath)) {
    cachedData = defaultStoredData()
    persistStoredData(cachedData)
    return cachedData
  }

  try {
    const raw = JSON.parse(readFileSync(configPath, 'utf8')) as unknown
    cachedData = sanitizeStoredData(raw)
    return cachedData
  } catch {
    cachedData = defaultStoredData()
    persistStoredData(cachedData)
    return cachedData
  }
}

function persistStoredData(data: StoredProviderData): void {
  const configPath = getConfigPath()
  mkdirSync(app.getPath('userData'), { recursive: true })
  writeFileSync(configPath, JSON.stringify(data, null, 2), 'utf8')
  cachedData = data
}

export function initializeProviderConfig(): void {
  loadStoredData()
}

export function getAllProviderConfigs(): ProviderConfig[] {
  const data = loadStoredData()
  const builtInIds = new Set(BUILT_IN_PROVIDERS.map((provider) => provider.id))
  const customProviders = data.customProviders.filter((provider) => !builtInIds.has(provider.id))
  return [...BUILT_IN_PROVIDERS, ...customProviders]
}

export function getProviderConfig(providerId: string): ProviderConfig | undefined {
  return getAllProviderConfigs().find((provider) => provider.id === providerId)
}

export function getApiKey(providerId: string): string | undefined {
  const data = loadStoredData()
  return data.apiKeys[providerId]
}

export function isProviderConfigured(provider: ProviderConfig): boolean {
  const apiKey = getApiKey(provider.id)

  if (provider.type === 'openai-compatible') {
    return Boolean(provider.baseUrl && provider.baseUrl.length > 0)
  }

  return Boolean(apiKey && apiKey.length > 0)
}

export function getProviderConfigStatuses(): ProviderConfigStatus[] {
  return getAllProviderConfigs().map((provider) => {
    const hasApiKey = Boolean(getApiKey(provider.id))
    return {
      ...provider,
      hasApiKey,
      configured: isProviderConfigured(provider)
    }
  })
}

export function hasAnyConfiguredProvider(): boolean {
  return getAllProviderConfigs().some((provider) => isProviderConfigured(provider))
}

export function saveProviderConfig(config: ProviderConfig, apiKey?: string): ProviderConfigStatus {
  const data = loadStoredData()
  const normalized: ProviderConfig = {
    ...config,
    isBuiltIn: config.isBuiltIn ?? false
  }

  if (normalized.isBuiltIn) {
    if (typeof apiKey === 'string') {
      if (apiKey.length > 0) {
        data.apiKeys[normalized.id] = apiKey
      } else {
        delete data.apiKeys[normalized.id]
      }
    }
  } else {
    const existingIndex = data.customProviders.findIndex((provider) => provider.id === normalized.id)
    if (existingIndex >= 0) {
      data.customProviders[existingIndex] = normalized
    } else {
      data.customProviders.push(normalized)
    }

    if (typeof apiKey === 'string') {
      if (apiKey.length > 0) {
        data.apiKeys[normalized.id] = apiKey
      } else {
        delete data.apiKeys[normalized.id]
      }
    }
  }

  persistStoredData(data)

  const saved = getProviderConfig(normalized.id)
  if (!saved) {
    throw new Error(`Failed to save provider: ${normalized.id}`)
  }

  return {
    ...saved,
    hasApiKey: Boolean(getApiKey(saved.id)),
    configured: isProviderConfigured(saved)
  }
}

export function deleteProviderConfig(providerId: string): void {
  const builtIn = BUILT_IN_PROVIDERS.some((provider) => provider.id === providerId)
  if (builtIn) {
    throw new Error('Built-in providers cannot be deleted')
  }

  const data = loadStoredData()
  data.customProviders = data.customProviders.filter((provider) => provider.id !== providerId)
  delete data.apiKeys[providerId]
  persistStoredData(data)
}

export function resetProviderConfigForTests(): void {
  cachedData = null
}
