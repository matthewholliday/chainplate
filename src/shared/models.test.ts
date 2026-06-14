/** @vitest-environment jsdom */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ALL_TOOL_IDS,
  DEFAULT_ANTHROPIC_MODEL,
  DEFAULT_PROVIDER_SELECTION,
  ENABLED_TOOLS_STORAGE_KEY,
  MODEL_STORAGE_KEY,
  PROVIDER_SELECTION_STORAGE_KEY,
  isAnthropicModelId,
  readEnabledTools,
  readStoredModelId,
  readStoredProviderSelection,
  resolveAnthropicModelId,
  resolveProviderSelection,
  writeStoredProviderSelection
} from './models'

describe('resolveAnthropicModelId', () => {
  it('returns the model when valid', () => {
    expect(resolveAnthropicModelId('claude-opus-4-6')).toBe('claude-opus-4-6')
  })

  it('falls back to default for invalid values', () => {
    expect(resolveAnthropicModelId('gpt-4')).toBe(DEFAULT_ANTHROPIC_MODEL)
    expect(resolveAnthropicModelId(null)).toBe(DEFAULT_ANTHROPIC_MODEL)
    expect(resolveAnthropicModelId(undefined)).toBe(DEFAULT_ANTHROPIC_MODEL)
    expect(resolveAnthropicModelId(42)).toBe(DEFAULT_ANTHROPIC_MODEL)
  })
})

describe('isAnthropicModelId', () => {
  it('accepts known model ids', () => {
    expect(isAnthropicModelId('claude-sonnet-4-6')).toBe(true)
    expect(isAnthropicModelId('claude-haiku-4-5')).toBe(true)
  })

  it('rejects unknown values', () => {
    expect(isAnthropicModelId('unknown')).toBe(false)
    expect(isAnthropicModelId('')).toBe(false)
  })
})

describe('readEnabledTools', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('returns all tools when storage is empty', () => {
    expect(readEnabledTools()).toEqual(ALL_TOOL_IDS)
  })

  it('filters unknown tool ids', () => {
    localStorage.setItem(
      ENABLED_TOOLS_STORAGE_KEY,
      JSON.stringify(['read_file', 'invalid_tool', 'write_file'])
    )
    expect(readEnabledTools()).toEqual(['read_file', 'write_file'])
  })

  it('returns all tools for malformed storage', () => {
    localStorage.setItem(ENABLED_TOOLS_STORAGE_KEY, 'not-json')
    expect(readEnabledTools()).toEqual(ALL_TOOL_IDS)

    localStorage.setItem(ENABLED_TOOLS_STORAGE_KEY, JSON.stringify({ tools: [] }))
    expect(readEnabledTools()).toEqual(ALL_TOOL_IDS)
  })
})

describe('readStoredModelId', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('reads stored model id', () => {
    localStorage.setItem(MODEL_STORAGE_KEY, 'claude-opus-4-6')
    expect(readStoredModelId()).toBe('claude-opus-4-6')
  })

  it('falls back when storage is missing or invalid', () => {
    expect(readStoredModelId()).toBe(DEFAULT_ANTHROPIC_MODEL)
    localStorage.setItem(MODEL_STORAGE_KEY, 'bad-model')
    expect(readStoredModelId()).toBe(DEFAULT_ANTHROPIC_MODEL)
  })

  it('returns default when localStorage is undefined', () => {
    vi.stubGlobal('localStorage', undefined)
    expect(readStoredModelId()).toBe(DEFAULT_ANTHROPIC_MODEL)
    vi.unstubAllGlobals()
  })
})

describe('provider selection', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('reads stored provider selection', () => {
    writeStoredProviderSelection({
      providerId: 'openai',
      modelId: 'gpt-4o',
      contextWindow: 128_000
    })
    expect(readStoredProviderSelection()).toEqual({
      providerId: 'openai',
      modelId: 'gpt-4o',
      contextWindow: 128_000
    })
  })

  it('migrates legacy anthropic model storage', () => {
    localStorage.setItem(MODEL_STORAGE_KEY, 'claude-opus-4-6')
    expect(readStoredProviderSelection()).toEqual({
      providerId: 'anthropic',
      modelId: 'claude-opus-4-6',
      contextWindow: 200_000
    })
    expect(localStorage.getItem(PROVIDER_SELECTION_STORAGE_KEY)).toContain('claude-opus-4-6')
  })

  it('falls back to default for invalid selection', () => {
    localStorage.setItem(PROVIDER_SELECTION_STORAGE_KEY, JSON.stringify({ providerId: 'bad', modelId: 'bad' }))
    expect(readStoredProviderSelection()).toEqual(DEFAULT_PROVIDER_SELECTION)
  })

  it('resolves unknown model to first model in provider', () => {
    const resolved = resolveProviderSelection({
      providerId: 'anthropic',
      modelId: 'unknown-model'
    })
    expect(resolved.providerId).toBe('anthropic')
    expect(resolved.modelId).toBe(DEFAULT_ANTHROPIC_MODEL)
  })
})
