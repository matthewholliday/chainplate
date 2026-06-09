import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type FC,
  type MutableRefObject,
  type ReactNode,
} from 'react'
import {
  RAG_ENABLED_STORAGE_KEY,
  RAG_MAX_CHUNKS_STORAGE_KEY,
  DEFAULT_RAG_MAX_CHUNKS,
  RAG_SIMILARITY_CUTOFF_STORAGE_KEY,
  DEFAULT_RAG_SIMILARITY_CUTOFF,
} from '@shared/models'

export type RagChunk = {
  id: string
  text: string
  filePath: string
  chunkIndex: number
  score: number
}

type RagStore = {
  pendingRef: MutableRefObject<RagChunk[]>
  ragChunksMap: Map<string, RagChunk[]>
  prefetch: (query: string) => Promise<void>
  commitPending: (messageId: string) => void
  getChunks: (messageId: string) => RagChunk[]
}

const RagContext = createContext<RagStore | null>(null)

export const RagProvider: FC<{ children: ReactNode; workspaceId: string }> = ({
  children,
  workspaceId
}) => {
  const pendingRef = useRef<RagChunk[]>([])
  const [ragChunksMap, setRagChunksMap] = useState<Map<string, RagChunk[]>>(
    () => new Map()
  )

  const prefetch = useCallback(async (query: string): Promise<void> => {
    const enabled = localStorage.getItem(RAG_ENABLED_STORAGE_KEY) === 'true'
    if (!enabled) {
      pendingRef.current = []
      return
    }

    const storedMax = parseInt(
      localStorage.getItem(RAG_MAX_CHUNKS_STORAGE_KEY) ?? '',
      10
    )
    const maxChunks =
      Number.isFinite(storedMax) && storedMax > 0
        ? storedMax
        : DEFAULT_RAG_MAX_CHUNKS

    const storedCutoff = parseFloat(
      localStorage.getItem(RAG_SIMILARITY_CUTOFF_STORAGE_KEY) ?? ''
    )
    const cutoff =
      Number.isFinite(storedCutoff) && storedCutoff >= 0 && storedCutoff <= 1
        ? storedCutoff
        : DEFAULT_RAG_SIMILARITY_CUTOFF

    try {
      const chunks = await window.electronAPI.searchChunks(workspaceId, query)
      pendingRef.current = chunks
        .filter((c) => c.score > cutoff)
        .slice(0, maxChunks)
    } catch {
      pendingRef.current = []
    }
  }, [workspaceId])

  const commitPending = useCallback((messageId: string): void => {
    const chunks = pendingRef.current
    if (chunks.length === 0) return
    pendingRef.current = []
    setRagChunksMap((prev) => {
      const next = new Map(prev)
      next.set(messageId, chunks)
      return next
    })
  }, [])

  const getChunks = useCallback(
    (messageId: string): RagChunk[] => {
      return ragChunksMap.get(messageId) ?? []
    },
    [ragChunksMap]
  )

  const value = useMemo(
    () => ({ pendingRef, ragChunksMap, prefetch, commitPending, getChunks }),
    [ragChunksMap, prefetch, commitPending, getChunks]
  )

  return <RagContext.Provider value={value}>{children}</RagContext.Provider>
}

export function useRagStore(): RagStore {
  const ctx = useContext(RagContext)
  if (!ctx) throw new Error('useRagStore must be used inside RagProvider')
  return ctx
}
