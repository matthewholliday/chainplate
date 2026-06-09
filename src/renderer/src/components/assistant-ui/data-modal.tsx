import { useState, type FC } from "react";
import { DatabaseIcon, ChevronDownIcon, ChevronRightIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import {
  SYSTEM_PROMPT_STORAGE_KEY,
  RAG_ENABLED_STORAGE_KEY,
  RAG_MAX_CHUNKS_STORAGE_KEY,
  DEFAULT_RAG_MAX_CHUNKS,
  RAG_SIMILARITY_CUTOFF_STORAGE_KEY,
  DEFAULT_RAG_SIMILARITY_CUTOFF,
} from "@shared/models";

const MAX_CHARS = 10_000;
const PAGE_SIZE = 10;

type IndexResult = { chunks: number } | { error: string };
type SearchResult = {
  id: string;
  text: string;
  filePath: string;
  chunkIndex: number;
  score: number;
};

function ChunkItem({ chunk }: { chunk: SearchResult }) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted/60 transition-colors">
        {open ? (
          <ChevronDownIcon className="size-3 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRightIcon className="size-3 shrink-0 text-muted-foreground" />
        )}
        <span className="flex-1 truncate font-mono text-muted-foreground">
          {chunk.filePath}
          <span className="ml-1 opacity-50">#{chunk.chunkIndex}</span>
        </span>
        {chunk.score < 1 && (
          <span className="shrink-0 tabular-nums text-muted-foreground/60">
            {(chunk.score * 100).toFixed(0)}%
          </span>
        )}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="mx-3 mb-2.5 mt-0.5 max-h-48 overflow-auto rounded-md border border-border bg-muted/40 px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap break-all font-mono">
          {chunk.text}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}

type DataModalProps = {
  workspaceId: string
  workspaceRoot?: string
}

export const DataModal: FC<DataModalProps> = ({ workspaceId, workspaceRoot }) => {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [ragEnabled, setRagEnabled] = useState(false);
  const [maxChunks, setMaxChunks] = useState(DEFAULT_RAG_MAX_CHUNKS);
  const [similarityCutoff, setSimilarityCutoff] = useState(DEFAULT_RAG_SIMILARITY_CUTOFF);
  const [knowledgePath, setKnowledgePath] = useState("");
  const [indexing, setIndexing] = useState(false);
  const [indexResult, setIndexResult] = useState<IndexResult | null>(null);
  const [editingPrompt, setEditingPrompt] = useState(false);

  // Chunk explorer
  const [hasIndex, setHasIndex] = useState(false);
  const [chunkCount, setChunkCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [explorerLoading, setExplorerLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const loadExistingIndex = async () => {
    setExplorerLoading(true);
    try {
      const meta = await window.electronAPI.getIndexMeta(workspaceId);
      if (meta) {
        setHasIndex(true);
        setChunkCount(meta.chunkCount);
        const results = await window.electronAPI.searchChunks(workspaceId, "");
        setSearchResults(results);
      } else {
        setHasIndex(false);
        setChunkCount(0);
        setSearchResults(null);
      }
    } finally {
      setExplorerLoading(false);
    }
  };

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setDraft(localStorage.getItem(SYSTEM_PROMPT_STORAGE_KEY) ?? "");
      setKnowledgePath(workspaceRoot ?? "");
      setRagEnabled(localStorage.getItem(RAG_ENABLED_STORAGE_KEY) === "true");
      const storedMax = parseInt(localStorage.getItem(RAG_MAX_CHUNKS_STORAGE_KEY) ?? "", 10);
      setMaxChunks(Number.isFinite(storedMax) && storedMax > 0 ? storedMax : DEFAULT_RAG_MAX_CHUNKS);
      const storedCutoff = parseFloat(localStorage.getItem(RAG_SIMILARITY_CUTOFF_STORAGE_KEY) ?? "");
      setSimilarityCutoff(Number.isFinite(storedCutoff) && storedCutoff >= 0 && storedCutoff <= 1 ? storedCutoff : DEFAULT_RAG_SIMILARITY_CUTOFF);
      setEditingPrompt(false);
      setSearchQuery("");
      setSearchResults(null);
      setCurrentPage(1);
      void loadExistingIndex();
    }
    setOpen(isOpen);
  };

  const handleSave = () => {
    const trimmed = draft.trim();
    if (trimmed) {
      localStorage.setItem(SYSTEM_PROMPT_STORAGE_KEY, trimmed);
    } else {
      localStorage.removeItem(SYSTEM_PROMPT_STORAGE_KEY);
    }
    if (ragEnabled) {
      localStorage.setItem(RAG_ENABLED_STORAGE_KEY, "true");
      localStorage.setItem(RAG_MAX_CHUNKS_STORAGE_KEY, String(maxChunks));
      localStorage.setItem(RAG_SIMILARITY_CUTOFF_STORAGE_KEY, String(similarityCutoff));
    } else {
      localStorage.removeItem(RAG_ENABLED_STORAGE_KEY);
      localStorage.removeItem(RAG_MAX_CHUNKS_STORAGE_KEY);
      localStorage.removeItem(RAG_SIMILARITY_CUTOFF_STORAGE_KEY);
    }
    setOpen(false);
  };

  const handleClear = () => {
    setDraft("");
  };

  const handleReindex = async () => {
    if (!knowledgePath) return;
    setIndexing(true);
    setIndexResult(null);
    try {
      const chunks = await window.electronAPI.indexKnowledge(workspaceId, knowledgePath);
      setIndexResult({ chunks });
      setHasIndex(true);
      setChunkCount(chunks);
      setSearchQuery("");
      setCurrentPage(1);
      const results = await window.electronAPI.searchChunks(workspaceId, "");
      setSearchResults(results);
    } catch (err) {
      setIndexResult({
        error: err instanceof Error ? err.message : "Indexing failed",
      });
    } finally {
      setIndexing(false);
    }
  };

  const handleSearch = async (query = searchQuery) => {
    setSearching(true);
    setCurrentPage(1);
    try {
      const results = await window.electronAPI.searchChunks(workspaceId, query);
      setSearchResults(results);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    void handleSearch("");
  };

  const filteredResults = searchResults
    ? searchQuery.trim()
      ? searchResults.filter((c) => c.score > similarityCutoff)
      : searchResults
    : null;
  const totalPages = filteredResults
    ? Math.max(1, Math.ceil(filteredResults.length / PAGE_SIZE))
    : 0;
  const pagedResults = filteredResults
    ? filteredResults.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
    : [];

  const saved =
    typeof window !== "undefined"
      ? localStorage.getItem(SYSTEM_PROMPT_STORAGE_KEY)
      : null;
  const isActive = Boolean(saved);

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <TooltipIconButton
        tooltip={isActive ? "System prompt (active)" : "Data"}
        side="top"
        variant="ghost"
        size="icon"
        className="hover:bg-muted-foreground/15 dark:border-muted-foreground/15 dark:hover:bg-muted-foreground/30 size-8 rounded-full p-1"
        aria-label="Open data"
        onClick={() => handleOpen(true)}
      >
        <DatabaseIcon
          className={
            isActive
              ? "size-4 stroke-[1.5px] text-primary"
              : "size-4 stroke-[1.5px]"
          }
        />
      </TooltipIconButton>
      <DialogContent className="sm:max-w-2xl flex flex-col max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Data</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-6 py-2 overflow-y-auto">
          {/* System prompt */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <label
                htmlFor="system-prompt"
                className="text-sm font-medium leading-none"
              >
                System prompt
              </label>
              {!editingPrompt && (
                <button
                  type="button"
                  onClick={() => setEditingPrompt(true)}
                  className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted"
                >
                  Edit
                </button>
              )}
            </div>
            {editingPrompt ? (
              <>
                <p className="text-xs text-muted-foreground">
                  Instructions sent at the start of every conversation. Use this to
                  set the assistant's persona, tone, or constraints.
                </p>
                <textarea
                  id="system-prompt"
                  autoFocus
                  value={draft}
                  onChange={(e) => setDraft(e.target.value.slice(0, MAX_CHARS))}
                  placeholder="You are a helpful assistant..."
                  rows={10}
                  className="w-full resize-none rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    {draft.length.toLocaleString()} / {MAX_CHARS.toLocaleString()}
                  </span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleClear}
                      disabled={draft.length === 0}
                      className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground disabled:pointer-events-none disabled:opacity-40"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {draft || <span className="italic">Not set</span>}
              </p>
            )}
          </div>

          {/* RAG */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <input
                id="rag-enabled"
                type="checkbox"
                checked={ragEnabled}
                onChange={(e) => setRagEnabled(e.target.checked)}
                className="size-4 rounded border-input accent-primary cursor-pointer"
              />
              <label
                htmlFor="rag-enabled"
                className="text-sm font-medium leading-none cursor-pointer select-none"
              >
                Enable RAG
              </label>
            </div>
            <p className="text-xs text-muted-foreground">
              When enabled, the assistant retrieves relevant passages from the
              knowledge base and includes them as context with each message.
            </p>

            {ragEnabled && (
              <div className="flex flex-col gap-6 border-l-2 border-border pl-4">
                {/* Max Chunks */}
                <div className="flex items-center gap-3">
                  <label
                    htmlFor="max-chunks"
                    className="text-sm font-medium leading-none whitespace-nowrap"
                  >
                    Max Chunks
                  </label>
                  <input
                    id="max-chunks"
                    type="number"
                    min={1}
                    max={100}
                    value={maxChunks}
                    onChange={(e) => {
                      const v = parseInt(e.target.value, 10);
                      if (Number.isFinite(v) && v > 0) setMaxChunks(v);
                    }}
                    className="w-20 rounded-md border border-input bg-transparent px-3 py-1.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <span className="text-xs text-muted-foreground">
                    passages injected per message
                  </span>
                </div>

                {/* Similarity Cutoff */}
                <div className="flex items-center gap-3">
                  <label
                    htmlFor="similarity-cutoff"
                    className="text-sm font-medium leading-none whitespace-nowrap"
                  >
                    Similarity Cutoff
                  </label>
                  <input
                    id="similarity-cutoff"
                    type="number"
                    min={0}
                    max={1}
                    step={0.01}
                    value={similarityCutoff}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      if (Number.isFinite(v) && v >= 0 && v <= 1) setSimilarityCutoff(v);
                    }}
                    className="w-20 rounded-md border border-input bg-transparent px-3 py-1.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <span className="text-xs text-muted-foreground">
                    minimum similarity score (0–1)
                  </span>
                </div>

                {/* Knowledge location (bound to active workspace) */}
                <div className="flex flex-col gap-2">
                  <label
                    htmlFor="knowledge-location"
                    className="text-sm font-medium leading-none"
                  >
                    Workspace folder
                  </label>
                  <p className="text-xs text-muted-foreground">
                    RAG indexes the active workspace folder. Add a workspace with a project folder to enable indexing.
                  </p>
                  <input
                    id="knowledge-location"
                    type="text"
                    readOnly
                    value={knowledgePath}
                    placeholder="No workspace folder (HOME has no project root)"
                    className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  />
                  <div className="flex items-center gap-3 pt-1">
                    <button
                      type="button"
                      onClick={handleReindex}
                      disabled={indexing || !knowledgePath}
                      className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
                    >
                      {indexing ? "Indexing..." : "(re-)index knowledge"}
                    </button>
                    {indexResult && "chunks" in indexResult && (
                      <span className="text-xs text-muted-foreground">
                        {indexResult.chunks.toLocaleString()} chunk
                        {indexResult.chunks !== 1 ? "s" : ""} created
                      </span>
                    )}
                    {indexResult && "error" in indexResult && (
                      <span className="text-xs text-destructive">
                        {indexResult.error}
                      </span>
                    )}
                  </div>
                </div>

                {/* Chunk Explorer */}
                {(hasIndex || explorerLoading) && (
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium leading-none">
                        Chunk Explorer
                      </label>
                      {!explorerLoading && (
                        <span className="text-xs text-muted-foreground">
                          {chunkCount.toLocaleString()} chunk{chunkCount !== 1 ? "s" : ""} indexed
                        </span>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") void handleSearch();
                        }}
                        placeholder="Enter a query to search by cosine similarity..."
                        className="flex-1 rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      />
                      <button
                        type="button"
                        onClick={() => void handleSearch()}
                        disabled={searching || explorerLoading}
                        className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
                      >
                        {searching ? "Searching..." : "Search"}
                      </button>
                    </div>

                    {explorerLoading && (
                      <p className="text-xs text-muted-foreground">Loading chunks...</p>
                    )}

                    {!explorerLoading && filteredResults !== null && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">
                            {filteredResults.length.toLocaleString()} result
                            {filteredResults.length !== 1 ? "s" : ""}
                            {searchQuery.trim() && filteredResults.length !== searchResults!.length && (
                              <span className="ml-1 opacity-60">
                                ({searchResults!.length.toLocaleString()} before cutoff)
                              </span>
                            )}
                          </span>
                          {searchQuery.trim() && (
                            <button
                              type="button"
                              onClick={handleClearSearch}
                              className="text-xs text-muted-foreground hover:text-foreground"
                            >
                              Clear search
                            </button>
                          )}
                        </div>

                        <div className="rounded-md border border-border divide-y divide-border overflow-hidden">
                          {pagedResults.length > 0 ? (
                            pagedResults.map((chunk) => (
                              <ChunkItem key={chunk.id} chunk={chunk} />
                            ))
                          ) : (
                            <p className="px-3 py-4 text-center text-xs text-muted-foreground">
                              No results
                            </p>
                          )}
                        </div>

                        {totalPages > 1 && (
                          <div className="flex items-center justify-between">
                            <button
                              type="button"
                              disabled={currentPage === 1}
                              onClick={() => setCurrentPage((p) => p - 1)}
                              className="rounded-md border border-input px-3 py-1.5 text-xs hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
                            >
                              Previous
                            </button>
                            <span className="text-xs text-muted-foreground">
                              {currentPage} / {totalPages}
                            </span>
                            <button
                              type="button"
                              disabled={currentPage === totalPages}
                              onClick={() => setCurrentPage((p) => p + 1)}
                              className="rounded-md border border-input px-3 py-1.5 text-xs hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
                            >
                              Next
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Save */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleSave}
              className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Save
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
