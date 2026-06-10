import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getChatServerInfo,
  setConversationUsage,
  startChatServer,
  stopChatServer
} from './chat-server'

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
  const originalApiKey = process.env.ANTHROPIC_API_KEY

  beforeEach(() => {
    stopChatServer()
  })

  afterEach(() => {
    stopChatServer()
    if (originalApiKey === undefined) {
      delete process.env.ANTHROPIC_API_KEY
    } else {
      process.env.ANTHROPIC_API_KEY = originalApiKey
    }
  })

  it('starts once and reuses the same server info', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key'
    const first = await startChatServer()
    const second = await startChatServer()
    expect(second).toEqual(first)
    expect(getChatServerInfo()?.url).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/)
  })

  it('reports configured=false when API key is missing', async () => {
    delete process.env.ANTHROPIC_API_KEY
    const info = await startChatServer()
    expect(info.configured).toBe(false)
  })

  it('returns null usage when conversationId is missing', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key'
    const { url } = await startChatServer()
    const response = await fetch(`${url}/api/usage`)
    expect(response.status).toBe(200)
    expect(await response.json()).toBeNull()
  })

  it('returns stored usage for a conversation', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key'
    const { url } = await startChatServer()
    setConversationUsage('conv-1', { promptTokens: 100, completionTokens: 50 })

    const response = await fetch(`${url}/api/usage?conversationId=conv-1`)
    expect(await response.json()).toEqual({
      promptTokens: 100,
      completionTokens: 50
    })
  })

  it('returns 503 for chat when API key is missing', async () => {
    delete process.env.ANTHROPIC_API_KEY
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [] })
    })

    expect(response.status).toBe(503)
    const body = await response.json()
    expect(body.error).toContain('ANTHROPIC_API_KEY')
  })

  it('returns 503 for agent when API key is missing', async () => {
    delete process.env.ANTHROPIC_API_KEY
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [] })
    })

    expect(response.status).toBe(503)
  })

  it('accepts chat requests when configured', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key'
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Origin: 'http://localhost:5173'
      },
      body: JSON.stringify({
        messages: [{ id: '1', role: 'user', parts: [{ type: 'text', text: 'hi' }] }],
        tools: {}
      })
    })

    expect(response.status).toBe(200)
    expect(response.headers.get('content-type')).toContain('text/event-stream')
  })

  it('accepts agent requests when configured', async () => {
    process.env.ANTHROPIC_API_KEY = 'test-key'
    const { url } = await startChatServer()

    const response = await fetch(`${url}/api/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ id: '1', role: 'user', parts: [{ type: 'text', text: 'list files' }] }],
        enabledTools: ['list_directory'],
        workspaceRoot: process.cwd()
      })
    })

    expect(response.status).toBe(200)
  })
})
