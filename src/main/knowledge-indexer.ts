import { readdir, readFile, stat, writeFile, mkdir } from 'fs/promises'
import type { Dirent } from 'fs'
import { join, extname, relative, dirname } from 'path'
import { app } from 'electron'

const CHUNK_SIZE = 800
const CHUNK_OVERLAP = 100

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

export type IndexMeta = { chunkCount: number; indexedAt: string }

export type KnowledgeSearchResult = KnowledgeChunk & { score: number }

function getIndexPath(): string {
  return join(app.getPath('userData'), 'knowledge-index.json')
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

function chunkText(text: string, size = CHUNK_SIZE, overlap = CHUNK_OVERLAP): string[] {
  const chunks: string[] = []
  let start = 0
  while (start < text.length) {
    const end = Math.min(start + size, text.length)
    chunks.push(text.slice(start, end))
    if (end === text.length) break
    start += size - overlap
  }
  return chunks
}

export async function indexKnowledge(folderPath: string): Promise<number> {
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

  const indexPath = getIndexPath()
  await mkdir(dirname(indexPath), { recursive: true })
  await writeFile(indexPath, JSON.stringify(index, null, 2), 'utf-8')

  return chunks.length
}

export async function loadKnowledgeIndex(): Promise<KnowledgeIndex | null> {
  try {
    const raw = await readFile(getIndexPath(), 'utf-8')
    return JSON.parse(raw) as KnowledgeIndex
  } catch {
    return null
  }
}

export async function getIndexMeta(): Promise<IndexMeta | null> {
  const index = await loadKnowledgeIndex()
  if (!index) return null
  return { chunkCount: index.chunks.length, indexedAt: index.indexedAt }
}

function tokenize(text: string): string[] {
  return text.toLowerCase().replace(/[^\w]/g, ' ').split(/\s+/).filter(t => t.length > 1)
}

function termFreq(tokens: string[]): Map<string, number> {
  const freq = new Map<string, number>()
  for (const t of tokens) freq.set(t, (freq.get(t) ?? 0) + 1)
  return freq
}

function cosineSim(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0
  for (const [term, fa] of a) {
    const fb = b.get(term)
    if (fb !== undefined) dot += fa * fb
  }
  let normA = 0
  for (const fa of a.values()) normA += fa * fa
  let normB = 0
  for (const fb of b.values()) normB += fb * fb
  if (normA === 0 || normB === 0) return 0
  return dot / (Math.sqrt(normA) * Math.sqrt(normB))
}

export async function searchChunks(query: string): Promise<KnowledgeSearchResult[]> {
  const index = await loadKnowledgeIndex()
  if (!index) return []

  const q = query.trim()
  if (!q) {
    return index.chunks.map(c => ({ ...c, score: 1 }))
  }

  const qFreq = termFreq(tokenize(q))
  return index.chunks
    .map(chunk => ({ ...chunk, score: cosineSim(qFreq, termFreq(tokenize(chunk.text))) }))
    .sort((a, b) => b.score - a.score)
}
