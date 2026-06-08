import { cn } from '@/lib/utils'
import { useUsage } from '@/lib/usage-context'
import { CONTEXT_WINDOW_SIZE } from '@shared/models'
import type { FC } from 'react'

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10_000 ? 0 : 1)}k`
  return String(n)
}

function barColor(pct: number): string {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 75) return 'bg-orange-400'
  if (pct >= 50) return 'bg-amber-400'
  return 'bg-[--brand-dim]'
}

function textColor(pct: number): string {
  if (pct >= 90) return 'text-red-500'
  if (pct >= 75) return 'text-orange-400'
  if (pct >= 50) return 'text-amber-400'
  return 'text-muted-foreground'
}

export const ContextIndicator: FC = () => {
  const { usage } = useUsage()

  if (!usage) return null

  const { pct, promptTokens } = usage
  const pctRounded = Math.round(pct * 10) / 10

  return (
    <div
      className={cn('flex items-center gap-1.5', textColor(pct))}
      title={`${formatTokens(promptTokens)} / ${formatTokens(CONTEXT_WINDOW_SIZE)} input tokens`}
    >
      <div className="relative h-1.5 w-12 overflow-hidden rounded-full bg-muted-foreground/15">
        <div
          className={cn('absolute inset-y-0 left-0 rounded-full transition-all duration-500', barColor(pct))}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="tabular-nums text-xs">{pctRounded < 1 ? '<1' : Math.round(pct)}%</span>
    </div>
  )
}
