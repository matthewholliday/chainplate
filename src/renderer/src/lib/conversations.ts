import type { ThreadMessage } from '@assistant-ui/react'

export type Workspace = {
  id: string
  name: string
  rootFolder?: string
  createdAt: number
}

export const HOME_WORKSPACE_ID = 'home'
export const HOME_WORKSPACE: Workspace = {
  id: HOME_WORKSPACE_ID,
  name: 'HOME',
  createdAt: 0
}

export type Conversation = {
  id: string
  title: string
  createdAt: number
  workspaceId: string
  messages: ThreadMessage[]
}

const STORAGE_KEY = 'chainplate:conversations'
const WORKSPACES_STORAGE_KEY = 'chainplate:workspaces'

export const CONVERSATIONS_STORAGE_VERSION = 1

type StoredConversations = {
  version: number
  conversations: Conversation[]
}

export type SaveResult =
  | { ok: true }
  | { ok: false; reason: 'quota' | 'serialization' | 'unknown' }

function isStoredConversations(value: unknown): value is StoredConversations {
  return (
    typeof value === 'object' &&
    value !== null &&
    'version' in value &&
    'conversations' in value &&
    Array.isArray((value as StoredConversations).conversations)
  )
}

function normalizeConversation(c: Conversation): Conversation {
  return {
    ...c,
    workspaceId: c.workspaceId ?? HOME_WORKSPACE_ID
  }
}

export function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []

    const parsed: unknown = JSON.parse(raw)

    // Versioned format: { version, conversations }
    if (isStoredConversations(parsed)) {
      return parsed.conversations.map(normalizeConversation)
    }

    // Legacy format: bare Conversation[]
    if (Array.isArray(parsed)) {
      return (parsed as Conversation[]).map(normalizeConversation)
    }

    return []
  } catch {
    return []
  }
}

export function saveConversations(conversations: Conversation[]): SaveResult {
  try {
    const payload: StoredConversations = {
      version: CONVERSATIONS_STORAGE_VERSION,
      conversations
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    return { ok: true }
  } catch (error) {
    if (
      error instanceof DOMException &&
      (error.name === 'QuotaExceededError' || error.code === 22)
    ) {
      return { ok: false, reason: 'quota' }
    }
    if (error instanceof TypeError) {
      return { ok: false, reason: 'serialization' }
    }
    return { ok: false, reason: 'unknown' }
  }
}

export function createConversation(workspaceId: string = HOME_WORKSPACE_ID): Conversation {
  return {
    id: crypto.randomUUID(),
    title: 'New conversation',
    createdAt: Date.now(),
    workspaceId,
    messages: []
  }
}

export function loadWorkspaces(): Workspace[] {
  try {
    const raw = localStorage.getItem(WORKSPACES_STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as Workspace[]
  } catch {
    return []
  }
}

export function saveWorkspaces(workspaces: Workspace[]): void {
  try {
    localStorage.setItem(WORKSPACES_STORAGE_KEY, JSON.stringify(workspaces))
  } catch {
    // Storage full or serialization error — fail silently
  }
}

export function createWorkspace(name: string, rootFolder?: string): Workspace {
  return {
    id: crypto.randomUUID(),
    name,
    rootFolder,
    createdAt: Date.now()
  }
}

export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  const minutes = Math.floor(diff / 60_000)
  const hours = Math.floor(diff / 3_600_000)
  const days = Math.floor(diff / 86_400_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return new Date(timestamp).toLocaleDateString()
}
