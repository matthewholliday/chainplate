/** @vitest-environment jsdom */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  CONVERSATIONS_STORAGE_VERSION,
  HOME_WORKSPACE_ID,
  createConversation,
  createWorkspace,
  formatRelativeTime,
  loadConversations,
  loadWorkspaces,
  saveConversations,
  saveWorkspaces
} from './conversations'

describe('conversation persistence', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-08T12:00:00Z'))
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('creates a conversation with defaults', () => {
    const conv = createConversation()
    expect(conv.title).toBe('New conversation')
    expect(conv.workspaceId).toBe(HOME_WORKSPACE_ID)
    expect(conv.messages).toEqual([])
    expect(conv.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    )
  })

  it('round-trips versioned conversation storage', () => {
    const conv = createConversation('workspace-1')
    const result = saveConversations([conv])
    expect(result).toEqual({ ok: true })

    const loaded = loadConversations()
    expect(loaded).toHaveLength(1)
    expect(loaded[0].id).toBe(conv.id)
    expect(loaded[0].workspaceId).toBe('workspace-1')

    const raw = JSON.parse(localStorage.getItem('chainplate:conversations') ?? '{}')
    expect(raw.version).toBe(CONVERSATIONS_STORAGE_VERSION)
  })

  it('loads legacy bare array format and normalizes workspaceId', () => {
    localStorage.setItem(
      'chainplate:conversations',
      JSON.stringify([
        {
          id: 'legacy-1',
          title: 'Old chat',
          createdAt: 1,
          messages: []
        }
      ])
    )

    const loaded = loadConversations()
    expect(loaded[0].workspaceId).toBe(HOME_WORKSPACE_ID)
  })

  it('returns empty array for corrupt storage', () => {
    localStorage.setItem('chainplate:conversations', '{bad json')
    expect(loadConversations()).toEqual([])
    localStorage.setItem('chainplate:conversations', JSON.stringify({ foo: 'bar' }))
    expect(loadConversations()).toEqual([])
  })

  it('reports quota errors on save', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      const error = new DOMException('quota', 'QuotaExceededError')
      throw error
    })

    expect(saveConversations([])).toEqual({ ok: false, reason: 'quota' })
  })

  it('reports serialization errors on save', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new TypeError('circular')
    })

    expect(saveConversations([])).toEqual({ ok: false, reason: 'serialization' })
  })
})

describe('workspace persistence', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('creates and saves workspaces', () => {
    const workspace = createWorkspace('Project', '/tmp/project')
    saveWorkspaces([workspace])

    const loaded = loadWorkspaces()
    expect(loaded).toHaveLength(1)
    expect(loaded[0].name).toBe('Project')
    expect(loaded[0].rootFolder).toBe('/tmp/project')
  })

  it('returns empty array when storage is missing or invalid', () => {
    expect(loadWorkspaces()).toEqual([])
    localStorage.setItem('chainplate:workspaces', 'not-json')
    expect(loadWorkspaces()).toEqual([])
  })
})

describe('formatRelativeTime', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-08T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('formats recent timestamps', () => {
    const now = Date.now()
    expect(formatRelativeTime(now - 30_000)).toBe('just now')
    expect(formatRelativeTime(now - 5 * 60_000)).toBe('5m ago')
    expect(formatRelativeTime(now - 3 * 3_600_000)).toBe('3h ago')
    expect(formatRelativeTime(now - 2 * 86_400_000)).toBe('2d ago')
  })

  it('falls back to locale date for older timestamps', () => {
    const old = Date.now() - 10 * 86_400_000
    expect(formatRelativeTime(old)).toBe(new Date(old).toLocaleDateString())
  })
})
