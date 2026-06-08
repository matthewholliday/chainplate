import { useState, type FC } from 'react'
import { ChevronDownIcon, ChevronRightIcon, LayersIcon } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible'
import type { RagChunk } from '@/lib/rag-context'

const PAGE_SIZE = 10

function ChunkItem({ chunk }: { chunk: RagChunk }) {
  const [open, setOpen] = useState(false)
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
        <span className="shrink-0 tabular-nums text-muted-foreground/60">
          {(chunk.score * 100).toFixed(0)}%
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="mx-3 mb-2.5 mt-0.5 max-h-48 overflow-auto rounded-md border border-border bg-muted/40 px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap break-all font-mono">
          {chunk.text}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  )
}

type RagChunksModalProps = {
  chunks: RagChunk[]
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const RagChunksModal: FC<RagChunksModalProps> = ({
  chunks,
  open,
  onOpenChange,
}) => {
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = Math.max(1, Math.ceil(chunks.length / PAGE_SIZE))
  const pagedChunks = chunks.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  )

  const handleOpenChange = (next: boolean) => {
    if (!next) setCurrentPage(1)
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl flex flex-col max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LayersIcon className="size-4" />
            Retrieved Context
          </DialogTitle>
          <DialogDescription>
            {chunks.length} chunk{chunks.length !== 1 ? 's' : ''} retrieved,
            sorted by cosine similarity
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3 overflow-y-auto min-h-0 h-96">
          {chunks.length === 0 ? (
            <p className="px-3 py-4 text-center text-xs text-muted-foreground">
              No chunks retrieved for this response.
            </p>
          ) : (
            <>
              <div className="rounded-md border border-border divide-y divide-border overflow-hidden">
                {pagedChunks.map((chunk) => (
                  <ChunkItem key={chunk.id} chunk={chunk} />
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between shrink-0">
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
      </DialogContent>
    </Dialog>
  )
}
