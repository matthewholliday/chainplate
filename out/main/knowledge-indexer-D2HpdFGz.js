"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const promises = require("fs/promises");
const path = require("path");
const electron = require("electron");
const CHUNK_SIZE = 800;
const CHUNK_OVERLAP = 100;
const TEXT_EXTENSIONS = /* @__PURE__ */ new Set([
  ".txt",
  ".md",
  ".markdown",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".py",
  ".json",
  ".yaml",
  ".yml",
  ".toml",
  ".ini",
  ".cfg",
  ".html",
  ".htm",
  ".css",
  ".scss",
  ".sh",
  ".bash",
  ".zsh",
  ".rs",
  ".go",
  ".java",
  ".rb",
  ".php",
  ".swift",
  ".kt",
  ".c",
  ".cpp",
  ".h",
  ".hpp",
  ".cs",
  ".r",
  ".sql",
  ".xml",
  ".example",
  ".gitignore"
]);
const SKIP_DIRS = /* @__PURE__ */ new Set([
  "node_modules",
  ".git",
  ".cursor",
  "dist",
  "build",
  "out",
  ".next",
  "__pycache__",
  ".venv",
  "venv"
]);
function getIndexPath() {
  return path.join(electron.app.getPath("userData"), "knowledge-index.json");
}
async function walkFiles(dir) {
  const results = [];
  async function walk(current) {
    let entries;
    try {
      entries = await promises.readdir(current, { withFileTypes: true, encoding: "utf-8" });
    } catch {
      return;
    }
    for (const entry of entries) {
      const name = entry.name;
      const fullPath = path.join(current, name);
      if (entry.isDirectory()) {
        if (!SKIP_DIRS.has(name)) {
          await walk(fullPath);
        }
      } else if (entry.isFile()) {
        const ext = path.extname(name).toLowerCase();
        if (TEXT_EXTENSIONS.has(ext)) {
          const fileStat = await promises.stat(fullPath).catch(() => null);
          if (fileStat && fileStat.size <= 2 * 1024 * 1024) {
            results.push(fullPath);
          }
        }
      }
    }
  }
  await walk(dir);
  return results;
}
function chunkText(text, size = CHUNK_SIZE, overlap = CHUNK_OVERLAP) {
  const chunks = [];
  let start = 0;
  while (start < text.length) {
    const end = Math.min(start + size, text.length);
    chunks.push(text.slice(start, end));
    if (end === text.length) break;
    start += size - overlap;
  }
  return chunks;
}
async function indexKnowledge(folderPath) {
  const files = await walkFiles(folderPath);
  const chunks = [];
  for (const filePath of files) {
    let content;
    try {
      content = await promises.readFile(filePath, "utf-8");
    } catch {
      continue;
    }
    const textChunks = chunkText(content.trim());
    const relPath = path.relative(folderPath, filePath);
    for (let i = 0; i < textChunks.length; i++) {
      const text = textChunks[i].trim();
      if (!text) continue;
      chunks.push({
        id: `${relPath}::${i}`,
        text,
        filePath: relPath,
        chunkIndex: i
      });
    }
  }
  const index = {
    folderPath,
    indexedAt: (/* @__PURE__ */ new Date()).toISOString(),
    chunks
  };
  const indexPath = getIndexPath();
  await promises.mkdir(path.dirname(indexPath), { recursive: true });
  await promises.writeFile(indexPath, JSON.stringify(index, null, 2), "utf-8");
  return chunks.length;
}
async function loadKnowledgeIndex() {
  try {
    const raw = await promises.readFile(getIndexPath(), "utf-8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
async function getIndexMeta() {
  const index = await loadKnowledgeIndex();
  if (!index) return null;
  return { chunkCount: index.chunks.length, indexedAt: index.indexedAt };
}
function tokenize(text) {
  return text.toLowerCase().replace(/[^\w]/g, " ").split(/\s+/).filter((t) => t.length > 1);
}
function termFreq(tokens) {
  const freq = /* @__PURE__ */ new Map();
  for (const t of tokens) freq.set(t, (freq.get(t) ?? 0) + 1);
  return freq;
}
function cosineSim(a, b) {
  let dot = 0;
  for (const [term, fa] of a) {
    const fb = b.get(term);
    if (fb !== void 0) dot += fa * fb;
  }
  let normA = 0;
  for (const fa of a.values()) normA += fa * fa;
  let normB = 0;
  for (const fb of b.values()) normB += fb * fb;
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}
async function searchChunks(query) {
  const index = await loadKnowledgeIndex();
  if (!index) return [];
  const q = query.trim();
  if (!q) {
    return index.chunks.map((c) => ({ ...c, score: 1 }));
  }
  const qFreq = termFreq(tokenize(q));
  return index.chunks.map((chunk) => ({ ...chunk, score: cosineSim(qFreq, termFreq(tokenize(chunk.text))) })).sort((a, b) => b.score - a.score);
}
exports.getIndexMeta = getIndexMeta;
exports.indexKnowledge = indexKnowledge;
exports.loadKnowledgeIndex = loadKnowledgeIndex;
exports.searchChunks = searchChunks;
