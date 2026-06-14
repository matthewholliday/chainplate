import {
  readStoredProviderSelection,
  resolveContextWindow,
  resolveProviderSelection,
  writeStoredProviderSelection,
  type ProviderConfig,
  type ProviderSelection
} from '@shared/models'
import { useAui, useAuiState } from '@assistant-ui/react'
import { cn } from '@/lib/utils'
import { useCallback, useEffect, useMemo, useState, type FC } from 'react'

function toRunConfig(selection: ProviderSelection) {
  return {
    custom: {
      provider: selection.providerId,
      model: selection.modelId,
      contextWindow: selection.contextWindow
    }
  }
}

function selectionValue(providerId: string, modelId: string): string {
  return `${providerId}::${modelId}`
}

function parseSelectionValue(value: string): { providerId: string; modelId: string } | null {
  const separatorIndex = value.indexOf('::')
  if (separatorIndex <= 0) return null
  const providerId = value.slice(0, separatorIndex)
  const modelId = value.slice(separatorIndex + 2)
  if (!providerId || !modelId) return null
  return { providerId, modelId }
}

type ModelSelectorProps = {
  providers: ProviderConfig[]
  onSelectionChange?: (selection: ProviderSelection) => void
}

export const ModelSelector: FC<ModelSelectorProps> = ({ providers, onSelectionChange }) => {
  const aui = useAui()
  const isRunning = useAuiState((s) => s.thread.isRunning)
  const [selection, setSelection] = useState<ProviderSelection>(() =>
    readStoredProviderSelection(providers)
  )

  const groupedProviders = useMemo(
    () => providers.filter((provider) => provider.models.length > 0),
    [providers]
  )

  const applySelection = useCallback(
    (nextSelection: ProviderSelection) => {
      const resolved = resolveProviderSelection(nextSelection, providers)
      setSelection(resolved)
      writeStoredProviderSelection(resolved)
      aui.composer().setRunConfig(toRunConfig(resolved))
      onSelectionChange?.(resolved)
    },
    [aui, onSelectionChange, providers]
  )

  useEffect(() => {
    const resolved = resolveProviderSelection(selection, providers)
    if (
      resolved.providerId !== selection.providerId ||
      resolved.modelId !== selection.modelId ||
      resolved.contextWindow !== selection.contextWindow
    ) {
      applySelection(resolved)
      return
    }
    aui.composer().setRunConfig(toRunConfig(resolved))
  }, [applySelection, aui, providers, selection])

  const currentValue = selectionValue(selection.providerId, selection.modelId)

  return (
    <select
      value={currentValue}
      disabled={isRunning || groupedProviders.length === 0}
      aria-label="Model"
      className={cn(
        'bg-transparent text-muted-foreground hover:text-foreground max-w-[11rem] truncate rounded-md border border-transparent px-2 py-1 text-xs outline-none',
        'focus-visible:border-ring focus-visible:ring-ring/20 focus-visible:ring-2',
        'disabled:cursor-not-allowed disabled:opacity-50'
      )}
      onChange={(event) => {
        const parsed = parseSelectionValue(event.target.value)
        if (!parsed) return
        applySelection({
          providerId: parsed.providerId,
          modelId: parsed.modelId,
          contextWindow: resolveContextWindow(
            { providerId: parsed.providerId, modelId: parsed.modelId },
            providers
          )
        })
      }}
    >
      {groupedProviders.map((provider) => (
        <optgroup key={provider.id} label={provider.label}>
          {provider.models.map((model) => (
            <option key={`${provider.id}-${model.id}`} value={selectionValue(provider.id, model.id)}>
              {model.label}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}
