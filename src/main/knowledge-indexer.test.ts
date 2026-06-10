import { mkdir, mkdtemp, readFile, rm, writeFile } from 'fs/promises'
import { tmpdir } from 'os'
import { join } from 'path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const userDataDir = join(tmpdir(), 'chainplate-knowledge-test')

vi.mock('electron', () => ({
  app: {
    getPath: () => userDataDir
  }
}))

import {
  getIndexMeta,
  indexKnowledge,
  loadKnowledgeIndex,
  searchChunks
} from './knowledge-indexer'

describe('knowledge-indexer', () => {
  let projectDir: string
  const workspaceId = 'test-workspace'

  beforeEach(async () => {
    projectDir = await mkdtemp(join(tmpdir(), 'chainplate-knowledge-project-'))
    await mkdir(userDataDir, { recursive: true })
    await writeFile(join(projectDir, 'alpha.md'), 'JWT authentication guide for APIs', 'utf-8')
    await writeFile(join(projectDir, 'beta.txt'), 'database schema migrations', 'utf-8')
    await mkdir(join(projectDir, 'node_modules'))
    await writeFile(join(projectDir, 'node_modules', 'ignored.js'), 'should skip', 'utf-8')
  })

  afterEach(async () => {
    await rm(projectDir, { recursive: true, force: true })
    await rm(userDataDir, { recursive: true, force: true })
  })

  it('indexes text files and skips ignored directories', async () => {
    const chunkCount = await indexKnowledge(workspaceId, projectDir)
    expect(chunkCount).toBeGreaterThan(0)

    const index = await loadKnowledgeIndex(workspaceId)
    expect(index).not.toBeNull()
    expect(index?.folderPath).toBe(projectDir)
    expect(index?.chunks.some((c) => c.filePath === 'alpha.md')).toBe(true)
    expect(index?.chunks.some((c) => c.filePath.includes('node_modules'))).toBe(false)
  })

  it('persists index to userData and returns metadata', async () => {
    await indexKnowledge(workspaceId, projectDir)
    const meta = await getIndexMeta(workspaceId)
    expect(meta?.chunkCount).toBeGreaterThan(0)
    expect(meta?.folderPath).toBe(projectDir)
    expect(meta?.indexedAt).toBeTruthy()

    const files = await readFile(
      join(userDataDir, 'knowledge-index-test-workspace.json'),
      'utf-8'
    )
    expect(JSON.parse(files).chunks.length).toBe(meta?.chunkCount)
  })

  it('returns null for missing index', async () => {
    expect(await loadKnowledgeIndex('missing-workspace')).toBeNull()
    expect(await getIndexMeta('missing-workspace')).toBeNull()
  })

  it('searches chunks by relevance', async () => {
    await indexKnowledge(workspaceId, projectDir)
    const results = await searchChunks(workspaceId, 'JWT authentication')
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].filePath).toBe('alpha.md')
    expect(results[0].score).toBeGreaterThan(0)
  })

  it('returns all chunks with uniform score for empty query', async () => {
    await indexKnowledge(workspaceId, projectDir)
    const results = await searchChunks(workspaceId, '   ')
    expect(results.every((r) => r.score === 1)).toBe(true)
  })

  it('migrates legacy home index when present', async () => {
    const legacyPath = join(userDataDir, 'knowledge-index.json')
    const legacyIndex = {
      folderPath: projectDir,
      indexedAt: new Date().toISOString(),
      chunks: [{ id: 'legacy::0', text: 'legacy chunk', filePath: 'legacy.txt', chunkIndex: 0 }]
    }
    await writeFile(legacyPath, JSON.stringify(legacyIndex), 'utf-8')

    const loaded = await loadKnowledgeIndex('home')
    expect(loaded?.chunks[0].text).toBe('legacy chunk')
  })
})
