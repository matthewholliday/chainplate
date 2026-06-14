import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getChatServerInfo,
  setConversationUsage,
  startChatServer,
  stopChatServer
} from './chat-server'

const providerState = vi.hoisted(() => ({
  configured: false
}))

vi.mock('./provider-config', () => ({
  getProviderConfig: vi.fn((providerId: string) => ({
    id: providerId,
    type: 'anthropic',
    label: 'Anthropic',
    models: [{ id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' }],
    isBuiltIn: true
  })),
  getApiKey: vi.fn(() => (providerState.configured ? 'test-key' : undefined)),
  hasAnyConfiguredProvider: vi.fn(() => providerState.configured),
  isProviderConfigured: vi.fn(() => providerState.configured)
}))

vi.mock('ai', async (importOriginal) => {
  const actual = await importOriginal<typeof import('ai')>()
  return {
    ...actual,
    streamText: vi.fn(() => ({
      toUIMessageStreamResponse: () =>
        new Response('event: message\ndata: {}\n\n', {
          headers: { 'Content-Type': 'text/event-stream' }
        })
    })),
    convertToModelMessages: vi.fn(async (messages: unknown) => messages)
  }
})

describe('chat-server', () => {
  beforeEach(() => {
    stopChatServer()
    providerState.configured = false
  })

  afterEach(() => {
    stopChatServer()
    providerState.configured = false
  })

  it('starts once and reuses the same server info', async () => {
    providerState.configured = true
    const first = await startChatServer()
    const second = await startChatServer()
    expect(second).toEqual(first)
    expect(getChatServerInfo()?.url).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/)
  })

  it('reports configured=false when no provider is configured', async () => {
    const info = await startChatServer()
    expect(info.configured).toBe(false)
  })

  it('returns null usage when conversationId is missing', async () => {
    providerState.configured = true
    const { url } = await startChatServer()
    const response = await fetch(`${url}/api/usage`)
    expect(response.status).toBe(200)
    expect(await response.json()).toBeNull()
  })

  it('returns stored usage for a conversation', async () => {
    providerState.configured = true
    const { url } = await startChatServer()
    setConversationUsage('conv-1', { promptTokens: 100, completionTokens: 50 })

    const response = await fetch(`${url}/api/usage?conversationId=conv-1`)
    expect(await response.json()).toEqual({
      promptTokens: 100,
      completionTokens: 50
    })
  })

  it('returns 503 for chat when provider is not configured', async () => {
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [] })
    })

    expect(response.status).toBe(503)
    const body = await response.json()
    expect(body.error).toContain('not configured')
  })

  it('returns 503 for agent when provider is not configured', async () => {
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [] })
    })

    expect(response.status).toBe(503)
  })

  it('accepts chat requests when configured', async () => {
    providerState.configured = true
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Origin: 'http://localhost:5173'
      },
      body: JSON.stringify({
        messages: [{ id: '1', role: 'user', parts: [{ type: 'text', text: 'hi' }] }],
        tools: {},
        metadata: {
          custom: {
            provider: 'anthropic',
            model: 'claude-sonnet-4-6'
          }
        }
      })
    })

    expect(response.status).toBe(200)
    expect(response.headers.get('content-type')).toContain('text/event-stream')
  })

  it('accepts agent requests when configured', async () => {
    providerState.configured = true
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ id: '1', role: 'user', parts: [{ type: 'text', text: 'list files' }] }],
        enabledTools: ['list_directory'],
        workspaceRoot: process.cwd(),
        metadata: {
          custom: {
            provider: 'anthropic',
            model: 'claude-sonnet-4-6'
          }
        }
      })
    })

    expect(response.status).toBe(200)
  })
})
