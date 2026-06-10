import { readdir, readFile, stat, writeFile, mkdir } from 'fs/promises'
import type { Dirent } from 'fs'
import { join, extname, relative, dirname } from 'path'
import { app } from 'electron'
import { chunkText, rankChunksByQuery, sanitizeWorkspaceId } from './knowledge/text-processing'

const TEXT_EXTENSIONS = new Set([
  '.txt', '.md', '.markdown', '.ts', '.tsx', '.js', '.jsx',
  '.py', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
  '.html', '.htm', '.css', '.scss', '.sh', '.bash', '.zsh',
  '.rs', '.go', '.java', '.rb', '.php', '.swift', '.kt',
  '.c', '.cpp', '.h', '.hpp', '.cs', '.r', '.sql', '.xml',
  '.example', '.gitignore',
])

const SKIP_DIRS = new Set([
  'node_modules', '.git', '.cursor', 'dist', 'build',
  'out', '.next', '__pycache__', '.venv', 'venv',
])

export type KnowledgeChunk = {
  id: string
  text: string
  filePath: string
  chunkIndex: number
}

export type KnowledgeIndex = {
  folderPath: string
  indexedAt: string
  chunks: KnowledgeChunk[]
}

export type IndexMeta = { chunkCount: number; indexedAt: string; folderPath?: string }

export type KnowledgeSearchResult = KnowledgeChunk & { score: number }

const LEGACY_INDEX_FILENAME = 'knowledge-index.json'

function getIndexPath(workspaceId: string): string {
  return join(app.getPath('userData'), `knowledge-index-${sanitizeWorkspaceId(workspaceId)}.json`)
}

async function migrateLegacyIndexIfNeeded(workspaceId: string): Promise<void> {
  if (workspaceId !== 'home') return

  const legacyPath = join(app.getPath('userData'), LEGACY_INDEX_FILENAME)
  const newPath = getIndexPath(workspaceId)

  try {
    await readFile(newPath, 'utf-8')
    return
  } catch {
    // New per-workspace index does not exist yet
  }

  try {
    const legacy = await readFile(legacyPath, 'utf-8')
    await mkdir(dirname(newPath), { recursive: true })
    await writeFile(newPath, legacy, 'utf-8')
  } catch {
    // No legacy index to migrate
  }
}

async function walkFiles(dir: string): Promise<string[]> {
  const results: string[] = []

  async function walk(current: string): Promise<void> {
    let entries: Dirent<string>[]
    try {
      entries = await readdir(current, { withFileTypes: true, encoding: 'utf-8' })
    } catch {
      return
    }

    for (const entry of entries) {
      const name = entry.name as string
      const fullPath = join(current, name)
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(name)) {
          await walk(fullPath)
        }
      } else if (entry.isFile()) {
        const ext = extname(name).toLowerCase()
        if (TEXT_EXTENSIONS.has(ext)) {
          const fileStat = await stat(fullPath).catch(() => null)
          // Skip files larger than 2MB
          if (fileStat && fileStat.size <= 2 * 1024 * 1024) {
            results.push(fullPath)
          }
        }
      }
    }
  }

  await walk(dir)
  return results
}

export async function indexKnowledge(workspaceId: string, folderPath: string): Promise<number> {
  const files = await walkFiles(folderPath)
  const chunks: KnowledgeChunk[] = []

  for (const filePath of files) {
    let content: string
    try {
      content = await readFile(filePath, 'utf-8')
    } catch {
      continue
    }

    const textChunks = chunkText(content.trim())
    const relPath = relative(folderPath, filePath)

    for (let i = 0; i < textChunks.length; i++) {
      const text = textChunks[i].trim()
      if (!text) continue
      chunks.push({
        id: `${relPath}::${i}`,
        text,
        filePath: relPath,
        chunkIndex: i,
      })
    }
  }

  const index: KnowledgeIndex = {
    folderPath,
    indexedAt: new Date().toISOString(),
    chunks,
  }

  const indexPath = getIndexPath(workspaceId)
  await mkdir(dirname(indexPath), { recursive: true })
  await writeFile(indexPath, JSON.stringify(index, null, 2), 'utf-8')

  return chunks.length
}

export async function loadKnowledgeIndex(workspaceId: string): Promise<KnowledgeIndex | null> {
  await migrateLegacyIndexIfNeeded(workspaceId)
  try {
    const raw = await readFile(getIndexPath(workspaceId), 'utf-8')
    return JSON.parse(raw) as KnowledgeIndex
  } catch {
    return null
  }
}

export async function getIndexMeta(workspaceId: string): Promise<IndexMeta | null> {
  const index = await loadKnowledgeIndex(workspaceId)
  if (!index) return null
  return { chunkCount: index.chunks.length, indexedAt: index.indexedAt, folderPath: index.folderPath }
}

export async function searchChunks(workspaceId: string, query: string): Promise<KnowledgeSearchResult[]> {
  const index = await loadKnowledgeIndex(workspaceId)
  if (!index) return []

  return rankChunksByQuery(index.chunks, query)
}
