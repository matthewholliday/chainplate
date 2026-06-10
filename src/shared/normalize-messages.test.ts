import { describe, expect, it } from 'vitest'
import type { UIMessage } from 'ai'
import { normalizeMessages } from './normalize-messages'

describe('normalizeMessages', () => {
  it('passes through messages that already have parts', () => {
    const messages: UIMessage[] = [
      {
        id: '1',
        role: 'user',
        parts: [{ type: 'text', text: 'hello' }]
      }
    ]
    expect(normalizeMessages(messages)).toEqual(messages)
  })

  it('converts content array to parts', () => {
    const input = [
      {
        id: '1',
        role: 'user',
        content: [
          { type: 'text', text: 'hello' },
          { type: 'image', url: 'http://example.com/a.png' }
        ]
      }
    ] as unknown as UIMessage[]

    const result = normalizeMessages(input)
    expect(result[0].parts).toEqual([
      { type: 'text', text: 'hello' },
      { type: 'image', url: 'http://example.com/a.png' }
    ])
  })

  it('defaults missing text fields to empty string', () => {
    const input = [
      {
        id: '1',
        role: 'assistant',
        content: [{ type: 'text' }]
      }
    ] as unknown as UIMessage[]

    const result = normalizeMessages(input)
    expect(result[0].parts).toEqual([{ type: 'text', text: '' }])
  })

  it('converts string content to a text part', () => {
    const input = [
      {
        id: '1',
        role: 'user',
        content: 'plain string'
      }
    ] as unknown as UIMessage[]

    const result = normalizeMessages(input)
    expect(result[0].parts).toEqual([{ type: 'text', text: 'plain string' }])
  })

  it('returns unrecognized messages unchanged', () => {
    const input = [{ id: '1', role: 'system' }] as unknown as UIMessage[]
    expect(normalizeMessages(input)).toEqual(input)
  })
})
