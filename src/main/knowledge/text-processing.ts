export const CHUNK_SIZE = 800
export const CHUNK_OVERLAP = 100

export function sanitizeWorkspaceId(workspaceId: string): string {
  return workspaceId.replace(/[^a-zA-Z0-9_-]/g, '_')
}

export function chunkText(
  text: string,
  size = CHUNK_SIZE,
  overlap = CHUNK_OVERLAP
): string[] {
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

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w]/g, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 1)
}

export function termFreq(tokens: string[]): Map<string, number> {
  const freq = new Map<string, number>()
  for (const t of tokens) freq.set(t, (freq.get(t) ?? 0) + 1)
  return freq
}

export function cosineSim(a: Map<string, number>, b: Map<string, number>): number {
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

export function rankChunksByQuery<T extends { text: string }>(
  chunks: T[],
  query: string
): Array<T & { score: number }> {
  const q = query.trim()
  if (!q) {
    return chunks.map((c) => ({ ...c, score: 1 }))
  }

  const qFreq = termFreq(tokenize(q))
  return chunks
    .map((chunk) => ({
      ...chunk,
      score: cosineSim(qFreq, termFreq(tokenize(chunk.text)))
    }))
    .sort((a, b) => b.score - a.score)
}
