import {
  ANTHROPIC_MODELS,
  MODEL_STORAGE_KEY,
  readStoredModelId,
  type AnthropicModelId
} from '@shared/models'
import { useAui, useAuiState } from '@assistant-ui/react'
import { cn } from '@/lib/utils'
import { useEffect, useState, type FC } from 'react'

export const ModelSelector: FC = () => {
  const aui = useAui()
  const isRunning = useAuiState((s) => s.thread.isRunning)
  const [model, setModel] = useState<AnthropicModelId>(readStoredModelId)

  useEffect(() => {
    aui.composer().setRunConfig({ custom: { model } })
  }, [aui, model])

  return (
    <select
      value={model}
      disabled={isRunning}
      aria-label="Model"
      className={cn(
        'bg-transparent text-muted-foreground hover:text-foreground max-w-[9.5rem] truncate rounded-md border border-transparent px-2 py-1 text-xs outline-none',
        'focus-visible:border-ring focus-visible:ring-ring/20 focus-visible:ring-2',
        'disabled:cursor-not-allowed disabled:opacity-50'
      )}
      onChange={(event) => {
        const nextModel = event.target.value as AnthropicModelId
        setModel(nextModel)
        localStorage.setItem(MODEL_STORAGE_KEY, nextModel)
        aui.composer().setRunConfig({ custom: { model: nextModel } })
      }}
    >
      {ANTHROPIC_MODELS.map(({ id, label }) => (
        <option key={id} value={id}>
          {label}
        </option>
      ))}
    </select>
  )
}
