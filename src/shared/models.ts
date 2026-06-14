export type AppMode = 'chat' | 'agent'
export const APP_MODE_STORAGE_KEY = 'chainplate:app-mode'

export const AGENT_TOOLS = [
  {
    id: 'read_file',
    label: 'Read File',
    description: 'Read the contents of a file at a given path.'
  },
  {
    id: 'write_file',
    label: 'Write File',
    description: 'Write content to a file, creating it if it does not exist.'
  },
  {
    id: 'list_directory',
    label: 'List Directory',
    description: 'List files and subdirectories in a directory.'
  },
  {
    id: 'execute_command',
    label: 'Execute Command',
    description: 'Run a shell command and return its stdout/stderr output.'
  }
] as const

export type AgentToolId = (typeof AGENT_TOOLS)[number]['id']

export const ENABLED_TOOLS_STORAGE_KEY = 'chainplate:enabled-tools'

export const ALL_TOOL_IDS: AgentToolId[] = AGENT_TOOLS.map((t) => t.id) as AgentToolId[]

export function readEnabledTools(): AgentToolId[] {
  if (typeof localStorage === 'undefined') return ALL_TOOL_IDS
  try {
    const raw = localStorage.getItem(ENABLED_TOOLS_STORAGE_KEY)
    if (!raw) return ALL_TOOL_IDS
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return ALL_TOOL_IDS
    return parsed.filter((id): id is AgentToolId =>
      ALL_TOOL_IDS.includes(id as AgentToolId)
    )
  } catch {
    return ALL_TOOL_IDS
  }
}

export const ANTHROPIC_MODELS = [
  { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6', contextWindow: 200_000 },
  { id: 'claude-opus-4-6', label: 'Claude Opus 4.6', contextWindow: 200_000 },
  { id: 'claude-haiku-4-5', label: 'Claude Haiku 4.5', contextWindow: 200_000 }
] as const

export type AnthropicModelId = (typeof ANTHROPIC_MODELS)[number]['id']

export const DEFAULT_ANTHROPIC_MODEL: AnthropicModelId = 'claude-sonnet-4-6'

export const OPENAI_MODELS = [
  { id: 'gpt-4.1', label: 'GPT-4.1', contextWindow: 1_047_576 },
  { id: 'gpt-4.1-mini', label: 'GPT-4.1 Mini', contextWindow: 1_047_576 },
  { id: 'gpt-4o', label: 'GPT-4o', contextWindow: 128_000 },
  { id: 'o3-mini', label: 'o3-mini', contextWindow: 200_000 }
] as const

export type OpenAIModelId = (typeof OPENAI_MODELS)[number]['id']

export const DEFAULT_OPENAI_MODEL: OpenAIModelId = 'gpt-4.1'

export const CONTEXT_WINDOW_SIZE = 200_000

export const MODEL_STORAGE_KEY = 'chainplate:anthropic-model'

export type ProviderType = 'anthropic' | 'openai' | 'openai-compatible'

export type ModelEntry = {
  id: string
  label: string
  contextWindow?: number
}

export type ProviderConfig = {
  id: string
  type: ProviderType
  label: string
  baseUrl?: string
  models: ModelEntry[]
  isBuiltIn: boolean
}

export type ProviderConfigStatus = ProviderConfig & {
  hasApiKey: boolean
  configured: boolean
}

export type ProviderSelection = {
  providerId: string
  modelId: string
  contextWindow?: number
}

export const PROVIDER_SELECTION_STORAGE_KEY = 'chainplate:provider-selection'

export const DEFAULT_PROVIDER_ID = 'anthropic'

export const DEFAULT_PROVIDER_SELECTION: ProviderSelection = {
  providerId: DEFAULT_PROVIDER_ID,
  modelId: DEFAULT_ANTHROPIC_MODEL,
  contextWindow: CONTEXT_WINDOW_SIZE
}

export const BUILT_IN_PROVIDERS: ProviderConfig[] = [
  {
    id: 'anthropic',
    type: 'anthropic',
    label: 'Anthropic',
    models: ANTHROPIC_MODELS.map((model) => ({
      id: model.id,
      label: model.label,
      contextWindow: model.contextWindow
    })),
    isBuiltIn: true
  },
  {
    id: 'openai',
    type: 'openai',
    label: 'OpenAI',
    models: OPENAI_MODELS.map((model) => ({
      id: model.id,
      label: model.label,
      contextWindow: model.contextWindow
    })),
    isBuiltIn: true
  }
]

export const SYSTEM_PROMPT_STORAGE_KEY = 'chainplate:system-prompt'

export const KNOWLEDGE_LOCATION_STORAGE_KEY = 'chainplate:knowledge-location'

export const WORKSPACES_STORAGE_KEY = 'chainplate:workspaces'

export const WORKSPACE_COLLAPSED_STORAGE_KEY = 'chainplate:workspace-collapsed'

export const RAG_ENABLED_STORAGE_KEY = 'chainplate:rag-enabled'

export const RAG_MAX_CHUNKS_STORAGE_KEY = 'chainplate:rag-max-chunks'

export const DEFAULT_RAG_MAX_CHUNKS = 10

export const RAG_SIMILARITY_CUTOFF_STORAGE_KEY = 'chainplate:rag-similarity-cutoff'

export const DEFAULT_RAG_SIMILARITY_CUTOFF = 0.1

export function isAnthropicModelId(value: unknown): value is AnthropicModelId {
  return (
    typeof value === 'string' &&
    ANTHROPIC_MODELS.some((model) => model.id === value)
  )
}

export function resolveAnthropicModelId(value: unknown): AnthropicModelId {
  return isAnthropicModelId(value) ? value : DEFAULT_ANTHROPIC_MODEL
}

export function readStoredModelId(): AnthropicModelId {
  if (typeof localStorage === 'undefined') {
    return DEFAULT_ANTHROPIC_MODEL
  }

  return resolveAnthropicModelId(localStorage.getItem(MODEL_STORAGE_KEY))
}

export function isProviderSelection(value: unknown): value is ProviderSelection {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<ProviderSelection>
  return (
    typeof candidate.providerId === 'string' &&
    candidate.providerId.length > 0 &&
    typeof candidate.modelId === 'string' &&
    candidate.modelId.length > 0
  )
}

export function resolveContextWindow(
  selection: ProviderSelection,
  providers: ProviderConfig[]
): number {
  if (typeof selection.contextWindow === 'number' && selection.contextWindow > 0) {
    return selection.contextWindow
  }

  const provider = providers.find((entry) => entry.id === selection.providerId)
  const model = provider?.models.find((entry) => entry.id === selection.modelId)
  return model?.contextWindow ?? CONTEXT_WINDOW_SIZE
}

export function resolveProviderSelection(
  value: unknown,
  providers: ProviderConfig[] = BUILT_IN_PROVIDERS
): ProviderSelection {
  if (!isProviderSelection(value)) {
    return DEFAULT_PROVIDER_SELECTION
  }

  const provider = providers.find((entry) => entry.id === value.providerId)
  if (!provider) {
    return DEFAULT_PROVIDER_SELECTION
  }

  const model = provider.models.find((entry) => entry.id === value.modelId)
  if (!model) {
    return {
      providerId: provider.id,
      modelId: provider.models[0]?.id ?? DEFAULT_PROVIDER_SELECTION.modelId,
      contextWindow: provider.models[0]?.contextWindow ?? CONTEXT_WINDOW_SIZE
    }
  }

  return {
    providerId: provider.id,
    modelId: model.id,
    contextWindow: model.contextWindow ?? CONTEXT_WINDOW_SIZE
  }
}

function migrateLegacyModelSelection(): ProviderSelection | null {
  if (typeof localStorage === 'undefined') return null

  const legacyModel = localStorage.getItem(MODEL_STORAGE_KEY)
  if (!legacyModel || !isAnthropicModelId(legacyModel)) return null

  const model = ANTHROPIC_MODELS.find((entry) => entry.id === legacyModel)
  return {
    providerId: DEFAULT_PROVIDER_ID,
    modelId: legacyModel,
    contextWindow: model?.contextWindow ?? CONTEXT_WINDOW_SIZE
  }
}

export function readStoredProviderSelection(
  providers: ProviderConfig[] = BUILT_IN_PROVIDERS
): ProviderSelection {
  if (typeof localStorage === 'undefined') {
    return DEFAULT_PROVIDER_SELECTION
  }

  try {
    const raw = localStorage.getItem(PROVIDER_SELECTION_STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as unknown
      return resolveProviderSelection(parsed, providers)
    }
  } catch {
    // fall through to migration/default
  }

  const migrated = migrateLegacyModelSelection()
  if (migrated) {
    localStorage.setItem(PROVIDER_SELECTION_STORAGE_KEY, JSON.stringify(migrated))
    return resolveProviderSelection(migrated, providers)
  }

  return DEFAULT_PROVIDER_SELECTION
}

export function writeStoredProviderSelection(selection: ProviderSelection): void {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(PROVIDER_SELECTION_STORAGE_KEY, JSON.stringify(selection))
}
