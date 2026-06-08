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
  { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
  { id: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
  { id: 'claude-haiku-4-5', label: 'Claude Haiku 4.5' }
] as const

export type AnthropicModelId = (typeof ANTHROPIC_MODELS)[number]['id']

export const DEFAULT_ANTHROPIC_MODEL: AnthropicModelId = 'claude-sonnet-4-6'

export const CONTEXT_WINDOW_SIZE = 200_000

export const MODEL_STORAGE_KEY = 'chainplate:anthropic-model'

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
