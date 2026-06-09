import { AssistantRuntimeProvider, useAuiState, useThreadRuntime } from '@assistant-ui/react'
import type { ThreadMessage } from '@assistant-ui/react'
import {
  AssistantChatTransport,
  useChatRuntime
} from '@assistant-ui/react-ai-sdk'
import { getExternalStoreMessages } from '@assistant-ui/core'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Thread } from '@/components/assistant-ui/thread'
import { ConversationSidebar } from '@/components/ConversationSidebar'
import { TooltipProvider } from '@/components/ui/tooltip'
import {
  type Conversation,
  type Workspace,
  HOME_WORKSPACE_ID,
  HOME_WORKSPACE,
  createConversation,
  createWorkspace,
  loadConversations,
  loadWorkspaces,
  saveConversations,
  saveWorkspaces
} from '@/lib/conversations'
import { SYSTEM_PROMPT_STORAGE_KEY, APP_MODE_STORAGE_KEY, WORKSPACE_COLLAPSED_STORAGE_KEY, type AppMode, readEnabledTools } from '@shared/models'
import { UsageProvider, useUsage } from '@/lib/usage-context'
import { RagProvider, useRagStore, type RagChunk } from '@/lib/rag-context'
import { cn } from '@/lib/utils'

type ChatServerInfo = {
  url: string
  configured: boolean
}

// Extracts a title string from the first user message content.
// Handles both ThreadMessage (content: ContentPart[]) and UIMessage (parts: UIMessagePart[]) formats.
function extractTitle(messages: readonly ThreadMessage[]): string | undefined {
  const firstUser = messages.find((m) => m.role === 'user')
  if (!firstUser) return undefined
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const msg = firstUser as any
  let text = ''
  // Try parts first (UIMessage / AI SDK v6 format)
  if (Array.isArray(msg.parts)) {
    const part = msg.parts.find((p: { type: string }) => p.type === 'text') as
      | { type: 'text'; text: string }
      | undefined
    text = part?.text ?? ''
  }
  // Fallback to content (ThreadMessage / assistant-ui format)
  if (!text) {
    const content = msg.content
    if (typeof content === 'string') {
      text = content
    } else if (Array.isArray(content)) {
      const part = content.find((p: { type: string }) => p.type === 'text') as
        | { type: 'text'; text: string }
        | undefined
      text = part?.text ?? ''
    }
  }
  return text.slice(0, 50) || undefined
}

type ConversationSyncerProps = {
  conversationId: string
  onSave: (id: string, messages: readonly ThreadMessage[], titleHint?: string) => void
}

type RunningReporterProps = {
  conversationId: string
  onRunningChange: (id: string, isRunning: boolean) => void
}

function RunningReporter({ conversationId, onRunningChange }: RunningReporterProps) {
  const isRunning = useAuiState((s) => s.thread.isRunning)
  const prevRef = useRef(false)
  const onRunningChangeRef = useRef(onRunningChange)
  useEffect(() => {
    onRunningChangeRef.current = onRunningChange
  })

  useEffect(() => {
    if (prevRef.current !== isRunning) {
      prevRef.current = isRunning
      onRunningChangeRef.current(conversationId, isRunning)
    }
  // conversationId is stable for the lifetime of this component
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning])

  return null
}

// Renders nothing; subscribes to thread state changes and persists messages.
// Must be rendered inside AssistantRuntimeProvider.
// Initial messages are loaded via useChatRuntime's `messages` option in ChatApp,
// which passes them directly to useChat and avoids the broken reset() path.
function ConversationSyncer({ conversationId, onSave }: ConversationSyncerProps) {
  const threadRuntime = useThreadRuntime()
  const onSaveRef = useRef(onSave)
  useEffect(() => {
    onSaveRef.current = onSave
  })

  useEffect(() => {
    // Track the last saved snapshot (count + tail ID) to avoid re-saving when
    // the external store adapter notifies subscribers without any real message change.
    const saved = { count: -1, tailId: '' }
    return threadRuntime.subscribe(() => {
      const state = threadRuntime.getState()
      if (state.isRunning) return
      const { messages } = state
      if (messages.length === 0) return
      const tailId = (messages[messages.length - 1] as { id?: string }).id ?? ''
      if (messages.length === saved.count && tailId === saved.tailId) return
      saved.count = messages.length
      saved.tailId = tailId
      // Recover the original UIMessage objects (with `parts`) from the converted
      // ThreadMessage objects via symbolInnerMessage. This ensures we save UIMessages
      // to localStorage instead of assistant-ui ThreadMessages (which lose their content
      // when serialized to JSON because the `parts` field is not on ThreadMessage).
      const uiMessages = messages.flatMap((m) => getExternalStoreMessages(m))
      const messagesToSave = (uiMessages.length === messages.length
        ? uiMessages
        : messages) as unknown as ThreadMessage[]
      onSaveRef.current(conversationId, messagesToSave, extractTitle(messages))
    })
    // conversationId is stable for the lifetime of this component
    // (ChatApp is remounted via key={conversationId} on every switch)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return null
}

// Subscribes to thread state; when the assistant finishes a response, commits the
// pending RAG chunks (if any) to the message ID of the last assistant message.
function RagChunksSyncer() {
  const threadRuntime = useThreadRuntime()
  const { commitPending } = useRagStore()
  const lastCommittedIdRef = useRef('')

  useEffect(() => {
    return threadRuntime.subscribe(() => {
      const state = threadRuntime.getState()
      if (state.isRunning) return
      const { messages } = state
      if (messages.length === 0) return
      const last = messages[messages.length - 1]
      if (last.role !== 'assistant') return
      const id = (last as { id?: string }).id ?? ''
      if (!id || id === lastCommittedIdRef.current) return
      lastCommittedIdRef.current = id
      commitPending(id)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return null
}

type ChatAppProps = {
  chatApiUrl: string
  configured: boolean
  conversationId: string
  workspaceId: string
  initialMessages: ThreadMessage[]
  onSave: (id: string, messages: readonly ThreadMessage[], titleHint?: string) => void
  onRunningChange: (id: string, isRunning: boolean) => void
  mode: AppMode
  workspaceRoot?: string
}

// Fetches usage from the server after each response completes.
// Must be rendered inside AssistantRuntimeProvider and UsageProvider.
function UsageTracker({
  chatApiUrl,
  conversationId
}: {
  chatApiUrl: string
  conversationId: string
}) {
  const isRunning = useAuiState((s) => s.thread.isRunning)
  const wasRunningRef = useRef(false)
  const { setUsage } = useUsage()

  useEffect(() => {
    if (wasRunningRef.current && !isRunning) {
      const params = new URLSearchParams({ conversationId })
      fetch(`${chatApiUrl}/api/usage?${params}`)
        .then((r) => r.json())
        .then((data) => {
          if (data && typeof data.promptTokens === 'number') {
            setUsage({ promptTokens: data.promptTokens, completionTokens: data.completionTokens })
          }
        })
        .catch(() => {})
    }
    wasRunningRef.current = isRunning
  }, [isRunning, chatApiUrl, conversationId, setUsage])

  return null
}

function ChatAppInner({
  chatApiUrl,
  configured,
  conversationId,
  initialMessages,
  onSave,
  onRunningChange,
  mode,
  workspaceRoot
}: ChatAppProps): React.JSX.Element {
  const { pendingRef } = useRagStore()

  const transport = useMemo(
    () =>
      new AssistantChatTransport({
        api: `${chatApiUrl}/api/${mode}`,
        body: () => {
          const systemPrompt = localStorage.getItem(SYSTEM_PROMPT_STORAGE_KEY)
          const chunks: RagChunk[] = pendingRef.current
          let system = systemPrompt || undefined

          if (chunks.length > 0) {
            const contextBlock = chunks
              .map(
                (c, i) =>
                  `[${i + 1}] ${c.filePath}#${c.chunkIndex} (${(c.score * 100).toFixed(0)}%)\n${c.text}`
              )
              .join('\n\n---\n\n')
            const header = '## Retrieved Context\n\n' + contextBlock
            system = system ? `${system}\n\n${header}` : header
          }

          const enabledTools = readEnabledTools()
          return {
            ...(system ? { system } : {}),
            enabledTools,
            conversationId,
            ...(workspaceRoot ? { workspaceRoot } : {})
          }
        }
      }),
    // pendingRef is stable (useRef); chatApiUrl changes only on server restart
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [chatApiUrl, mode, workspaceRoot, conversationId]
  )
  // Filter out messages that have no renderable content — these are corrupted
  // ThreadMessage shells saved in an old format (content:[], no parts).
  // Valid messages have: non-empty parts array (AI SDK UIMessage v6 format),
  // non-empty content string (legacy format), or non-empty content array.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const validMessages = useMemo(() => initialMessages.filter((m: any) => {
    if (Array.isArray(m.parts) && m.parts.some((p: any) => p.type !== 'step-start')) return true
    if (typeof m.content === 'string' && m.content.length > 0) return true
    if (Array.isArray(m.content) && m.content.length > 0) return true
    return false
  }), [initialMessages])
  // Pass validMessages directly to useChatRuntime so useChat initializes with
  // the correct history. Using reset() here is broken: it strips the symbolInnerMessage
  // binding that links ThreadMessage objects back to their UIMessage originals, causing
  // getExternalStoreMessages to return [] and setMessages([]) to be called instead.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const runtime = useChatRuntime({ transport, messages: validMessages as any })

  return (
    <UsageProvider>
      <AssistantRuntimeProvider runtime={runtime}>
        <div className="flex h-full min-h-0 flex-col">
          {!configured && (
            <div className="border-b border-border bg-destructive/10 px-4 py-2 text-sm text-destructive">
              Set ANTHROPIC_API_KEY in .env and restart the app to enable chat.
            </div>
          )}
          <ConversationSyncer
            conversationId={conversationId}
            onSave={onSave}
          />
          <RunningReporter
            conversationId={conversationId}
            onRunningChange={onRunningChange}
          />
          <RagChunksSyncer />
          <UsageTracker chatApiUrl={chatApiUrl} conversationId={conversationId} />
          <div className="min-h-0 flex-1">
            <Thread />
          </div>
        </div>
      </AssistantRuntimeProvider>
    </UsageProvider>
  )
}

function ChatApp({ workspaceId, ...props }: ChatAppProps): React.JSX.Element {
  return (
    <RagProvider workspaceId={workspaceId}>
      <ChatAppInner workspaceId={workspaceId} {...props} />
    </RagProvider>
  )
}

function ModeToggle({ mode, onChange }: { mode: AppMode; onChange: (m: AppMode) => void }): React.JSX.Element {
  return (
    <div
      className="flex items-center gap-0.5 rounded-full bg-muted p-0.5"
      style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
    >
      {(['chat', 'agent'] as AppMode[]).map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={cn(
            'rounded-full px-3 py-0.5 text-xs font-medium capitalize transition-colors',
            mode === m
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          {m}
        </button>
      ))}
    </div>
  )
}

function loadCollapsedWorkspaceIds(): Set<string> {
  try {
    const raw = localStorage.getItem(WORKSPACE_COLLAPSED_STORAGE_KEY)
    if (!raw) return new Set()
    return new Set(JSON.parse(raw) as string[])
  } catch {
    return new Set()
  }
}

function saveCollapsedWorkspaceIds(ids: Set<string>): void {
  try {
    localStorage.setItem(WORKSPACE_COLLAPSED_STORAGE_KEY, JSON.stringify([...ids]))
  } catch {
    // fail silently
  }
}

function getInitialConvState(): { conversations: Conversation[]; activeId: string } {
  const saved = loadConversations()
  if (saved.length > 0) {
    const sorted = [...saved].sort((a, b) => b.createdAt - a.createdAt)
    return { conversations: saved, activeId: sorted[0].id }
  }
  const conv = createConversation(HOME_WORKSPACE_ID)
  saveConversations([conv])
  return { conversations: [conv], activeId: conv.id }
}

function App(): React.JSX.Element {
  const [chatInfo, setChatInfo] = useState<ChatServerInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [appMode, setAppMode] = useState<AppMode>(
    () => (localStorage.getItem(APP_MODE_STORAGE_KEY) as AppMode | null) ?? 'chat'
  )

  const [{ conversations, activeId }, setConvState] = useState(getInitialConvState)
  const [workspaces, setWorkspaces] = useState<Workspace[]>(() => loadWorkspaces())
  const [collapsedWorkspaceIds, setCollapsedWorkspaceIds] = useState<Set<string>>(
    () => loadCollapsedWorkspaceIds()
  )
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set())
  const [notificationIds, setNotificationIds] = useState<Set<string>>(new Set())
  const [storageError, setStorageError] = useState<string | null>(null)
  // Stable ref so handleRunningChange can read the latest activeId without being recreated
  const activeIdRef = useRef(activeId)
  useEffect(() => {
    activeIdRef.current = activeId
  }, [activeId])

  useEffect(() => {
    if (!window.electronAPI?.getChatApiUrl) {
      setError('Preload bridge failed to load. Restart the application.')
      return
    }

    window.electronAPI
      .getChatApiUrl()
      .then(setChatInfo)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to connect to chat server')
      })
  }, [])

  useEffect(() => {
    localStorage.setItem(APP_MODE_STORAGE_KEY, appMode)
  }, [appMode])

  // Persist whenever conversations change
  useEffect(() => {
    const result = saveConversations(conversations)
    if (!result.ok) {
      const message =
        result.reason === 'quota'
          ? 'Conversation history could not be saved: browser storage is full. Delete old conversations or export data.'
          : 'Conversation history could not be saved. Your latest messages may be lost after restart.'
      setStorageError(message)
    } else {
      setStorageError(null)
    }
  }, [conversations])

  // Persist workspaces
  useEffect(() => {
    saveWorkspaces(workspaces)
  }, [workspaces])

  // Persist collapsed state
  useEffect(() => {
    saveCollapsedWorkspaceIds(collapsedWorkspaceIds)
  }, [collapsedWorkspaceIds])

  const handleNew = useCallback((workspaceId: string) => {
    const conv = createConversation(workspaceId)
    setConvState((prev) => ({
      conversations: [conv, ...prev.conversations],
      activeId: conv.id
    }))
  }, [])

  const handleSelect = useCallback((id: string) => {
    setConvState((prev) => ({ ...prev, activeId: id }))
    setNotificationIds((prev) => {
      if (!prev.has(id)) return prev
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  const handleRunningChange = useCallback((id: string, isRunning: boolean) => {
    setRunningIds((prev) => {
      const next = new Set(prev)
      if (isRunning) {
        next.add(id)
      } else {
        next.delete(id)
      }
      return next
    })
    if (!isRunning) {
      setNotificationIds((prev) => {
        if (activeIdRef.current === id) return prev
        const next = new Set(prev)
        next.add(id)
        return next
      })
    }
  }, [])

  const handleDelete = useCallback((id: string) => {
    setConvState((prev) => {
      const remaining = prev.conversations.filter((c) => c.id !== id)
      if (remaining.length === 0) {
        const conv = createConversation(HOME_WORKSPACE_ID)
        return { conversations: [conv], activeId: conv.id }
      }
      const newActiveId =
        prev.activeId === id
          ? [...remaining].sort((a, b) => b.createdAt - a.createdAt)[0].id
          : prev.activeId
      return { conversations: remaining, activeId: newActiveId }
    })
  }, [])

  const handleSave = useCallback(
    (id: string, messages: readonly ThreadMessage[], titleHint?: string) => {
      setConvState((prev) => ({
        ...prev,
        conversations: prev.conversations.map((c) => {
          if (c.id !== id) return c
          const title = titleHint && c.title === 'New conversation' ? titleHint : c.title
          return { ...c, messages: [...messages], title }
        })
      }))
    },
    []
  )

  const handleNewWorkspace = useCallback(async () => {
    const folderPath = await window.electronAPI?.selectKnowledgeFolder()
    if (!folderPath) return
    // Derive name from the last path segment
    const name = folderPath.split('/').filter(Boolean).pop() ?? folderPath
    const ws = createWorkspace(name, folderPath)
    setWorkspaces((prev) => [...prev, ws])
    // Auto-index the workspace folder so RAG uses the correct knowledge base
    try {
      await window.electronAPI.indexKnowledge(ws.id, folderPath)
    } catch (err) {
      console.error('Failed to auto-index workspace:', err)
    }
    // Auto-create an initial conversation in the new workspace
    const conv = createConversation(ws.id)
    setConvState((prev) => ({
      conversations: [conv, ...prev.conversations],
      activeId: conv.id
    }))
  }, [])

  const handleRenameWorkspace = useCallback((id: string, name: string) => {
    setWorkspaces((prev) =>
      prev.map((ws) => (ws.id === id ? { ...ws, name } : ws))
    )
  }, [])

  const handleDeleteWorkspace = useCallback((id: string) => {
    setWorkspaces((prev) => prev.filter((ws) => ws.id !== id))
    setConvState((prev) => {
      const remaining = prev.conversations.filter((c) => c.workspaceId !== id)
      if (remaining.length === 0) {
        const conv = createConversation(HOME_WORKSPACE_ID)
        return { conversations: [conv], activeId: conv.id }
      }
      const newActiveId = prev.conversations.find((c) => c.id === prev.activeId)?.workspaceId === id
        ? [...remaining].sort((a, b) => b.createdAt - a.createdAt)[0].id
        : prev.activeId
      return { conversations: remaining, activeId: newActiveId }
    })
  }, [])

  const handleToggleWorkspace = useCallback((id: string) => {
    setCollapsedWorkspaceIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-muted-foreground">
        {error}
      </div>
    )
  }

  const getWorkspaceRoot = useCallback((conv: Conversation): string | undefined => {
    if (conv.workspaceId === HOME_WORKSPACE_ID) return HOME_WORKSPACE.rootFolder
    return workspaces.find((ws) => ws.id === conv.workspaceId)?.rootFolder
  }, [workspaces])

  // Render the active conversation plus any background conversations that are still running.
  // Using stable key={conv.id} (not keyed on appMode) ensures background ChatApps
  // are not unmounted when the user switches conversations or toggles mode.
  const convsToRender = useMemo(
    () => conversations.filter((c) => c.id === activeId || runningIds.has(c.id)),
    [conversations, activeId, runningIds]
  )

  const activeConversation = conversations.find((c) => c.id === activeId)
  const activeWorkspaceId = activeConversation?.workspaceId ?? HOME_WORKSPACE_ID
  const activeWorkspaceRoot = activeConversation
    ? getWorkspaceRoot(activeConversation)
    : undefined

  return (
    <TooltipProvider>
      <div className="flex h-full flex-col">
        {storageError && (
          <div className="border-b border-border bg-destructive/10 px-4 py-2 text-sm text-destructive">
            {storageError}
          </div>
        )}
        <div
          className="flex h-10 w-full shrink-0 items-center border-b border-border px-4"
          style={{ WebkitAppRegion: 'drag', backgroundColor: 'var(--sidebar-bg)' } as React.CSSProperties}
        >
          <div className="flex-1" />
          <ModeToggle mode={appMode} onChange={setAppMode} />
          <div className="flex flex-1 select-none items-center justify-end gap-2">
            <span className="text-sm font-semibold tracking-wide text-foreground">Chainplate</span>
            <span
              className="size-2 rounded-full"
              style={{
                backgroundColor: 'var(--brand)',
                boxShadow: '0 0 8px var(--glow-brand)',
              }}
            />
          </div>
        </div>
        <div className="flex min-h-0 flex-1">
          <ConversationSidebar
            conversations={conversations}
            workspaces={workspaces}
            collapsedWorkspaceIds={collapsedWorkspaceIds}
            activeId={activeId}
            activeWorkspaceId={activeWorkspaceId}
            activeWorkspaceRoot={activeWorkspaceRoot}
            runningIds={runningIds}
            notificationIds={notificationIds}
            onNew={handleNew}
            onSelect={handleSelect}
            onDelete={handleDelete}
            onNewWorkspace={handleNewWorkspace}
            onRenameWorkspace={handleRenameWorkspace}
            onDeleteWorkspace={handleDeleteWorkspace}
            onToggleWorkspace={handleToggleWorkspace}
          />
          <div className="relative flex min-w-0 flex-1 flex-col">
            {!chatInfo ? (
              <div className="flex h-full items-center justify-center p-6 text-muted-foreground">
                Starting chat server...
              </div>
            ) : (
              convsToRender.map((conv) => (
                <div
                  key={conv.id}
                  className={cn(
                    'flex min-h-0 flex-1 flex-col',
                    conv.id !== activeId && 'hidden'
                  )}
                >
                  <ChatApp
                    chatApiUrl={chatInfo.url}
                    configured={chatInfo.configured}
                    conversationId={conv.id}
                    workspaceId={conv.workspaceId}
                    initialMessages={conv.messages ?? []}
                    onSave={handleSave}
                    onRunningChange={handleRunningChange}
                    mode={appMode}
                    workspaceRoot={getWorkspaceRoot(conv)}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}

export default App
