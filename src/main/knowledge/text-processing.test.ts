import { describe, expect, it } from 'vitest'
import {
  CHUNK_OVERLAP,
  CHUNK_SIZE,
  chunkText,
  cosineSim,
  rankChunksByQuery,
  sanitizeWorkspaceId,
  termFreq,
  tokenize
} from './text-processing'

describe('sanitizeWorkspaceId', () => {
  it('replaces unsafe characters', () => {
    expect(sanitizeWorkspaceId('my workspace!')).toBe('my_workspace_')
    expect(sanitizeWorkspaceId('proj-1_v2')).toBe('proj-1_v2')
  })
})

describe('chunkText', () => {
  it('returns a single chunk for short text', () => {
    expect(chunkText('hello')).toEqual(['hello'])
  })

  it('splits long text with overlap', () => {
    const text = 'a'.repeat(CHUNK_SIZE + 200)
    const chunks = chunkText(text)
    expect(chunks).toHaveLength(2)
    expect(chunks[0]).toHaveLength(CHUNK_SIZE)
    expect(chunks[1]).toHaveLength(200 + CHUNK_OVERLAP)
  })

  it('handles exact chunk boundary', () => {
    const text = 'b'.repeat(CHUNK_SIZE)
    expect(chunkText(text)).toEqual([text])
  })
})

describe('tokenize', () => {
  it('lowercases and filters short tokens', () => {
    expect(tokenize('Hello, World! A test.')).toEqual(['hello', 'world', 'test'])
  })
})

describe('cosineSim', () => {
  it('returns 1 for identical term frequencies', () => {
    const freq = termFreq(['alpha', 'beta', 'alpha'])
    expect(cosineSim(freq, freq)).toBeCloseTo(1)
  })

  it('returns 0 for orthogonal vectors', () => {
    expect(cosineSim(termFreq(['alpha']), termFreq(['beta']))).toBe(0)
  })

  it('returns 0 when either vector is empty', () => {
    expect(cosineSim(new Map(), termFreq(['alpha']))).toBe(0)
  })
})

describe('rankChunksByQuery', () => {
  const chunks = [
    { id: '1', text: 'authentication with JWT tokens' },
    { id: '2', text: 'database migration scripts' },
    { id: '3', text: 'JWT token validation middleware' }
  ]

  it('ranks relevant chunks higher', () => {
    const ranked = rankChunksByQuery(chunks, 'JWT authentication')
    expect(ranked[0].id).toBe('1')
    expect(ranked[0].score).toBeGreaterThan(ranked[1].score)
  })

  it('assigns uniform score for empty query', () => {
    const ranked = rankChunksByQuery(chunks, '   ')
    expect(ranked.every((c) => c.score === 1)).toBe(true)
  })
})
