import { useCallback, useState, type FC } from 'react'
import { PlugIcon, PlusIcon, Trash2Icon } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'
import type { ModelEntry, ProviderConfig, ProviderConfigStatus } from '@shared/models'

type ProviderSettingsModalProps = {
  providers: ProviderConfigStatus[]
  onProvidersChange: (providers: ProviderConfigStatus[]) => void
}

type CustomProviderDraft = {
  label: string
  baseUrl: string
  apiKey: string
  models: ModelEntry[]
}

const EMPTY_DRAFT: CustomProviderDraft = {
  label: '',
  baseUrl: '',
  apiKey: '',
  models: [{ id: '', label: '' }]
}

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function hasCustomProviders(providers: ProviderConfigStatus[]): boolean {
  return providers.some((provider) => !provider.isBuiltIn)
}

export const ProviderSettingsModal: FC<ProviderSettingsModalProps> = ({
  providers,
  onProvidersChange
}) => {
  const [open, setOpen] = useState(false)
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [savingId, setSavingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newProvider, setNewProvider] = useState<CustomProviderDraft>(EMPTY_DRAFT)
  const [error, setError] = useState<string | null>(null)

  const refreshProviders = useCallback(async () => {
    const next = await window.electronAPI.getProviderConfigs()
    onProvidersChange(next)
    return next
  }, [onProvidersChange])

  const handleOpen = useCallback(
    async (isOpen: boolean) => {
      if (isOpen) {
        setError(null)
        await refreshProviders()
      }
      setOpen(isOpen)
    },
    [refreshProviders]
  )

  const handleSaveProvider = useCallback(
    async (provider: ProviderConfigStatus) => {
      setSavingId(provider.id)
      setError(null)
      try {
        const apiKey = drafts[provider.id]
        const updated = await window.electronAPI.saveProviderConfig(provider, apiKey)
        const next = await refreshProviders()
        const merged = next.map((entry) => (entry.id === updated.id ? updated : entry))
        onProvidersChange(merged)
        setDrafts((prev) => {
          const copy = { ...prev }
          delete copy[provider.id]
          return copy
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to save provider')
      } finally {
        setSavingId(null)
      }
    },
    [drafts, onProvidersChange, refreshProviders]
  )

  const handleDeleteProvider = useCallback(
    async (providerId: string) => {
      setSavingId(providerId)
      setError(null)
      try {
        await window.electronAPI.deleteProviderConfig(providerId)
        await refreshProviders()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete provider')
      } finally {
        setSavingId(null)
      }
    },
    [refreshProviders]
  )

  const handleAddProvider = useCallback(async () => {
    const label = newProvider.label.trim()
    const baseUrl = newProvider.baseUrl.trim()
    const models = newProvider.models
      .map((model) => ({
        id: model.id.trim(),
        label: model.label.trim() || model.id.trim()
      }))
      .filter((model) => model.id.length > 0)

    if (!label) {
      setError('Provider name is required')
      return
    }
    if (!baseUrl) {
      setError('Base URL is required for custom providers')
      return
    }
    if (models.length === 0) {
      setError('Add at least one model ID')
      return
    }

    const id = slugify(label)
    if (!id) {
      setError('Provider name must include letters or numbers')
      return
    }

    setSavingId('new')
    setError(null)
    try {
      const config: ProviderConfig = {
        id,
        type: 'openai-compatible',
        label,
        baseUrl,
        models,
        isBuiltIn: false
      }
      await window.electronAPI.saveProviderConfig(config, newProvider.apiKey.trim() || undefined)
      await refreshProviders()
      setNewProvider(EMPTY_DRAFT)
      setShowAddForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add provider')
    } finally {
      setSavingId(null)
    }
  }, [newProvider, refreshProviders])

  const updateNewModel = useCallback((index: number, field: 'id' | 'label', value: string) => {
    setNewProvider((prev) => ({
      ...prev,
      models: prev.models.map((model, modelIndex) =>
        modelIndex === index ? { ...model, [field]: value } : model
      )
    }))
  }, [])

  const addNewModelRow = useCallback(() => {
    setNewProvider((prev) => ({
      ...prev,
      models: [...prev.models, { id: '', label: '' }]
    }))
  }, [])

  const removeNewModelRow = useCallback((index: number) => {
    setNewProvider((prev) => ({
      ...prev,
      models: prev.models.filter((_, modelIndex) => modelIndex !== index)
    }))
  }, [])

  const customized = providers.some((provider) => !provider.configured) || hasCustomProviders(providers)

  return (
    <Dialog open={open} onOpenChange={(isOpen) => void handleOpen(isOpen)}>
      <TooltipIconButton
        tooltip={customized ? 'Providers (needs setup)' : 'Providers'}
        side="top"
        variant="ghost"
        size="icon"
        className="hover:bg-muted-foreground/15 dark:border-muted-foreground/15 dark:hover:bg-muted-foreground/30 size-8 rounded-full p-1"
        aria-label="Open provider settings"
        onClick={() => void handleOpen(true)}
      >
        <PlugIcon
          className={
            customized
              ? 'size-4 stroke-[1.5px] text-primary'
              : 'size-4 stroke-[1.5px]'
          }
        />
      </TooltipIconButton>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>LLM Providers</DialogTitle>
        </DialogHeader>
        <div className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto py-2">
          <p className="text-xs text-muted-foreground">
            Connect cloud or local OpenAI-compatible APIs. API keys stay in the main process and are never sent to the renderer.
          </p>

          {error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {error}
            </div>
          )}

          {providers.map((provider) => (
            <div
              key={provider.id}
              className="rounded-lg border border-border p-3"
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium">{provider.label}</h3>
                    <span
                      className={
                        provider.configured
                          ? 'rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-500'
                          : 'rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-500'
                      }
                    >
                      {provider.configured ? 'Connected' : 'Not configured'}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {provider.type === 'openai-compatible'
                      ? provider.baseUrl || 'No base URL set'
                      : `${provider.type} provider`}
                  </p>
                </div>
                {!provider.isBuiltIn && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8 shrink-0 text-destructive hover:text-destructive"
                    disabled={savingId === provider.id}
                    onClick={() => void handleDeleteProvider(provider.id)}
                  >
                    <Trash2Icon className="size-4" />
                  </Button>
                )}
              </div>

              {provider.type === 'openai-compatible' && !provider.isBuiltIn && (
                <label className="mb-2 block text-xs">
                  <span className="mb-1 block text-muted-foreground">Base URL</span>
                  <input
                    type="url"
                    value={provider.baseUrl ?? ''}
                    onChange={(event) => {
                      const baseUrl = event.target.value
                      onProvidersChange(
                        providers.map((entry) =>
                          entry.id === provider.id ? { ...entry, baseUrl } : entry
                        )
                      )
                    }}
                    placeholder="http://localhost:11434/v1"
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                  />
                </label>
              )}

              <label className="mb-3 block text-xs">
                <span className="mb-1 block text-muted-foreground">
                  API key {provider.type === 'openai-compatible' ? '(optional for local servers)' : ''}
                </span>
                <input
                  type="password"
                  value={drafts[provider.id] ?? ''}
                  placeholder={provider.hasApiKey ? 'Saved (enter to replace)' : 'Enter API key'}
                  onChange={(event) =>
                    setDrafts((prev) => ({ ...prev, [provider.id]: event.target.value }))
                  }
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                />
              </label>

              <div className="flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  disabled={savingId === provider.id}
                  onClick={() => void handleSaveProvider(provider)}
                >
                  {savingId === provider.id ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          ))}

          {showAddForm ? (
            <div className="rounded-lg border border-dashed border-border p-3">
              <h3 className="mb-3 text-sm font-medium">Add custom provider</h3>
              <div className="flex flex-col gap-3">
                <label className="block text-xs">
                  <span className="mb-1 block text-muted-foreground">Name</span>
                  <input
                    type="text"
                    value={newProvider.label}
                    onChange={(event) =>
                      setNewProvider((prev) => ({ ...prev, label: event.target.value }))
                    }
                    placeholder="Ollama"
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                  />
                </label>
                <label className="block text-xs">
                  <span className="mb-1 block text-muted-foreground">Base URL</span>
                  <input
                    type="url"
                    value={newProvider.baseUrl}
                    onChange={(event) =>
                      setNewProvider((prev) => ({ ...prev, baseUrl: event.target.value }))
                    }
                    placeholder="http://localhost:11434/v1"
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                  />
                </label>
                <label className="block text-xs">
                  <span className="mb-1 block text-muted-foreground">API key (optional)</span>
                  <input
                    type="password"
                    value={newProvider.apiKey}
                    onChange={(event) =>
                      setNewProvider((prev) => ({ ...prev, apiKey: event.target.value }))
                    }
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                  />
                </label>
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Models</span>
                    <Button type="button" variant="ghost" size="sm" onClick={addNewModelRow}>
                      <PlusIcon className="mr-1 size-3" />
                      Add model
                    </Button>
                  </div>
                  <div className="flex flex-col gap-2">
                    {newProvider.models.map((model, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={model.id}
                          onChange={(event) => updateNewModel(index, 'id', event.target.value)}
                          placeholder="model-id"
                          className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                        />
                        <input
                          type="text"
                          value={model.label}
                          onChange={(event) => updateNewModel(index, 'label', event.target.value)}
                          placeholder="Display label"
                          className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/20"
                        />
                        {newProvider.models.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="size-8 shrink-0"
                            onClick={() => removeNewModelRow(index)}
                          >
                            <Trash2Icon className="size-4" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowAddForm(false)
                      setNewProvider(EMPTY_DRAFT)
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    disabled={savingId === 'new'}
                    onClick={() => void handleAddProvider()}
                  >
                    {savingId === 'new' ? 'Adding...' : 'Add provider'}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <Button type="button" variant="outline" size="sm" onClick={() => setShowAddForm(true)}>
              <PlusIcon className="mr-1 size-4" />
              Add custom provider
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
