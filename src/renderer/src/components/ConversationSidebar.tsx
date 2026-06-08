import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  type Conversation,
  type Workspace,
  HOME_WORKSPACE_ID,
  HOME_WORKSPACE,
  formatRelativeTime
} from '@/lib/conversations'
import {
  PlusIcon,
  Trash2Icon,
  ChevronDownIcon,
  ChevronRightIcon,
  FolderOpenIcon,
  FolderPlusIcon
} from 'lucide-react'
import { type FC, useState, useRef, useEffect, useCallback } from 'react'
import { DataModal } from '@/components/assistant-ui/data-modal'
import { ToolsModal } from '@/components/assistant-ui/tools-modal'

type Props = {
  conversations: Conversation[]
  workspaces: Workspace[]
  collapsedWorkspaceIds: Set<string>
  activeId: string
  runningIds: Set<string>
  notificationIds: Set<string>
  onNew: (workspaceId: string) => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onNewWorkspace: () => void
  onRenameWorkspace: (id: string, name: string) => void
  onDeleteWorkspace: (id: string) => void
  onToggleWorkspace: (id: string) => void
}

type ConversationItemProps = {
  conv: Conversation
  isActive: boolean
  isRunning: boolean
  hasNotification: boolean
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

function ConversationItem({ conv, isActive, isRunning, hasNotification, onSelect, onDelete }: ConversationItemProps) {
  return (
    <div
      className={cn(
        'group flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm transition-all duration-150',
        'border-l-2',
        isActive
          ? 'border-l-[--brand] bg-[--user-bubble]'
          : 'border-l-transparent hover:border-l-[--brand-dim] hover:bg-accent hover:translate-x-0.5'
      )}
      onClick={() => onSelect(conv.id)}
    >
      <span
        className={cn(
          'min-w-0 flex-1 truncate font-medium leading-snug',
          isActive ? 'text-foreground' : 'text-foreground/80'
        )}
      >
        {conv.title}
      </span>

      <span className="shrink-0 text-xs text-muted-foreground group-hover:hidden">
        {formatRelativeTime(conv.createdAt)}
      </span>

      {/* Running animation — pulsing beacon, hidden on hover so delete button shows */}
      {isRunning && !isActive && (
        <span className="relative flex shrink-0 size-2 group-hover:hidden">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex size-2 rounded-full bg-amber-500" />
        </span>
      )}

      {/* Notification dot — shown when run finished while user was elsewhere */}
      {hasNotification && !isRunning && (
        <span
          className="shrink-0 size-2 rounded-full group-hover:hidden"
          style={{ backgroundColor: 'var(--brand)' }}
        />
      )}

      <button
        className="hidden shrink-0 rounded p-0.5 text-muted-foreground transition-colors hover:text-foreground group-hover:block"
        onClick={(e) => {
          e.stopPropagation()
          onDelete(conv.id)
        }}
        aria-label="Delete conversation"
      >
        <Trash2Icon className="size-3.5" />
      </button>
    </div>
  )
}

type WorkspaceSectionProps = {
  workspace: Workspace
  conversations: Conversation[]
  isCollapsed: boolean
  isHome: boolean
  activeId: string
  runningIds: Set<string>
  notificationIds: Set<string>
  onNew: (workspaceId: string) => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onToggle: (id: string) => void
  onRename?: (id: string, name: string) => void
  onDeleteWorkspace?: (id: string) => void
}

function WorkspaceSection({
  workspace,
  conversations,
  isCollapsed,
  isHome,
  activeId,
  runningIds,
  notificationIds,
  onNew,
  onSelect,
  onDelete,
  onToggle,
  onRename,
  onDeleteWorkspace
}: WorkspaceSectionProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(workspace.name)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [isEditing])

  const commitRename = useCallback(() => {
    const trimmed = editValue.trim()
    if (trimmed && trimmed !== workspace.name && onRename) {
      onRename(workspace.id, trimmed)
    } else {
      setEditValue(workspace.name)
    }
    setIsEditing(false)
  }, [editValue, workspace.name, workspace.id, onRename])

  const sorted = [...conversations].sort((a, b) => b.createdAt - a.createdAt)

  return (
    <div className="mb-1">
      {/* Workspace header row */}
      <div
        className="group flex items-center gap-1 rounded-md px-1.5 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
        onClick={() => onToggle(workspace.id)}
      >
        {/* Chevron */}
        <span className="shrink-0">
          {isCollapsed
            ? <ChevronRightIcon className="size-3" />
            : <ChevronDownIcon className="size-3" />
          }
        </span>

        {/* Folder icon (user workspaces only) */}
        {!isHome && (
          <FolderOpenIcon className="size-3 shrink-0 text-[--brand]" />
        )}

        {/* Name or inline rename input */}
        {isEditing ? (
          <input
            ref={inputRef}
            className="min-w-0 flex-1 rounded bg-background px-1 py-0 text-xs font-semibold uppercase tracking-wider text-foreground outline-none ring-1 ring-[--brand]"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitRename()
              if (e.key === 'Escape') {
                setEditValue(workspace.name)
                setIsEditing(false)
              }
              e.stopPropagation()
            }}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span
            className="min-w-0 flex-1 truncate"
            onDoubleClick={(e) => {
              if (!isHome) {
                e.stopPropagation()
                setIsEditing(true)
              }
            }}
            title={!isHome ? 'Double-click to rename' : undefined}
          >
            {workspace.name}
          </span>
        )}

        {/* Delete workspace button (user workspaces only) */}
        {!isHome && onDeleteWorkspace && (
          <button
            className="ml-auto shrink-0 rounded p-0.5 opacity-0 transition-all hover:text-destructive group-hover:opacity-100"
            onClick={(e) => {
              e.stopPropagation()
              onDeleteWorkspace(workspace.id)
            }}
            aria-label={`Delete workspace ${workspace.name}`}
          >
            <Trash2Icon className="size-3" />
          </button>
        )}
      </div>

      {/* Conversations + new button */}
      {!isCollapsed && (
        <div className="ml-2 border-l border-border/50 pl-1">
          {sorted.map((conv) => (
            <ConversationItem
              key={conv.id}
              conv={conv}
              isActive={conv.id === activeId}
              isRunning={runningIds.has(conv.id)}
              hasNotification={notificationIds.has(conv.id)}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          ))}
          <button
            className="mt-0.5 flex w-full items-center gap-1.5 rounded-md px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            onClick={(e) => {
              e.stopPropagation()
              onNew(workspace.id)
            }}
          >
            <PlusIcon className="size-3 shrink-0" />
            New conversation
          </button>
        </div>
      )}
    </div>
  )
}

export const ConversationSidebar: FC<Props> = ({
  conversations,
  workspaces,
  collapsedWorkspaceIds,
  activeId,
  runningIds,
  notificationIds,
  onNew,
  onSelect,
  onDelete,
  onNewWorkspace,
  onRenameWorkspace,
  onDeleteWorkspace,
  onToggleWorkspace
}) => {
  const homeConversations = conversations.filter((c) => c.workspaceId === HOME_WORKSPACE_ID)
  const isHomeCollapsed = collapsedWorkspaceIds.has(HOME_WORKSPACE_ID)

  return (
    <div
      className="flex w-72 shrink-0 flex-col border-r border-border"
      style={{ backgroundColor: 'var(--sidebar-bg)' }}
    >
      <div className="px-2 pt-2">
        <Button
          variant="ghost"
          size="sm"
          className="mb-1 w-full justify-start gap-2 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          onClick={onNewWorkspace}
        >
          <FolderPlusIcon className="size-3.5 shrink-0" />
          Add workspace
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {/* HOME workspace — always first */}
        <WorkspaceSection
          workspace={HOME_WORKSPACE}
          conversations={homeConversations}
          isCollapsed={isHomeCollapsed}
          isHome={true}
          activeId={activeId}
          runningIds={runningIds}
          notificationIds={notificationIds}
          onNew={onNew}
          onSelect={onSelect}
          onDelete={onDelete}
          onToggle={onToggleWorkspace}
        />

        {/* User-created workspaces */}
        {workspaces
          .slice()
          .sort((a, b) => a.createdAt - b.createdAt)
          .map((ws) => (
            <WorkspaceSection
              key={ws.id}
              workspace={ws}
              conversations={conversations.filter((c) => c.workspaceId === ws.id)}
              isCollapsed={collapsedWorkspaceIds.has(ws.id)}
              isHome={false}
              activeId={activeId}
              runningIds={runningIds}
              notificationIds={notificationIds}
              onNew={onNew}
              onSelect={onSelect}
              onDelete={onDelete}
              onToggle={onToggleWorkspace}
              onRename={onRenameWorkspace}
              onDeleteWorkspace={onDeleteWorkspace}
            />
          ))}
      </div>

      {/* Footer */}
      <div className="border-t border-border px-2 py-2">
        <div className="flex items-center gap-1">
          <DataModal />
          <ToolsModal />
        </div>
      </div>
    </div>
  )
}
