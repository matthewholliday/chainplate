import { useState, useCallback, type FC } from 'react'
import { WrenchIcon } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'
import {
  AGENT_TOOLS,
  ALL_TOOL_IDS,
  ENABLED_TOOLS_STORAGE_KEY,
  readEnabledTools,
  type AgentToolId
} from '@shared/models'

function getIsCustomized(): boolean {
  const enabled = readEnabledTools()
  return enabled.length !== ALL_TOOL_IDS.length
}

export const ToolsModal: FC = () => {
  const [open, setOpen] = useState(false)
  const [enabledTools, setEnabledTools] = useState<AgentToolId[]>(ALL_TOOL_IDS)
  const [isCustomized, setIsCustomized] = useState(getIsCustomized)

  const handleOpen = useCallback((isOpen: boolean) => {
    if (isOpen) {
      setEnabledTools(readEnabledTools())
    }
    setOpen(isOpen)
  }, [])

  const handleToggle = useCallback((toolId: AgentToolId, checked: boolean) => {
    setEnabledTools((prev) => {
      const next = checked ? [...prev, toolId] : prev.filter((id) => id !== toolId)
      if (next.length === ALL_TOOL_IDS.length) {
        localStorage.removeItem(ENABLED_TOOLS_STORAGE_KEY)
      } else {
        localStorage.setItem(ENABLED_TOOLS_STORAGE_KEY, JSON.stringify(next))
      }
      setIsCustomized(next.length !== ALL_TOOL_IDS.length)
      return next
    })
  }, [])

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <TooltipIconButton
        tooltip={isCustomized ? 'Tools (customized)' : 'Tools'}
        side="top"
        variant="ghost"
        size="icon"
        className="hover:bg-muted-foreground/15 dark:border-muted-foreground/15 dark:hover:bg-muted-foreground/30 size-8 rounded-full p-1"
        aria-label="Open tools"
        onClick={() => handleOpen(true)}
      >
        <WrenchIcon
          className={
            isCustomized
              ? 'size-4 stroke-[1.5px] text-primary'
              : 'size-4 stroke-[1.5px]'
          }
        />
      </TooltipIconButton>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Agent Tools</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-1 py-2">
          <p className="mb-3 text-xs text-muted-foreground">
            Choose which tools the agent can use. Changes take effect on the next message.
          </p>
          {AGENT_TOOLS.map((tool) => {
            const checked = enabledTools.includes(tool.id)
            return (
              <label
                key={tool.id}
                className="flex cursor-pointer items-start gap-3 rounded-md px-3 py-2.5 transition-colors hover:bg-muted/60"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => handleToggle(tool.id, e.target.checked)}
                  className="mt-0.5 size-4 shrink-0 rounded border-input accent-primary cursor-pointer"
                />
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-medium leading-none">{tool.label}</span>
                  <span className="text-xs text-muted-foreground">{tool.description}</span>
                </div>
              </label>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
