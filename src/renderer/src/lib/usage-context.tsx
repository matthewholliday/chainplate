import { createContext, useContext, useState, type FC, type ReactNode } from 'react'
import { CONTEXT_WINDOW_SIZE } from '@shared/models'

export type UsageData = {
  promptTokens: number
  completionTokens: number
  pct: number
}

type UsageContextValue = {
  usage: UsageData | null
  setUsage: (data: { promptTokens: number; completionTokens: number } | null) => void
}

const UsageContext = createContext<UsageContextValue | null>(null)

export const UsageProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [raw, setRaw] = useState<{ promptTokens: number; completionTokens: number } | null>(null)

  const usage: UsageData | null = raw
    ? {
        ...raw,
        pct: Math.min(100, (raw.promptTokens / CONTEXT_WINDOW_SIZE) * 100)
      }
    : null

  return (
    <UsageContext.Provider value={{ usage, setUsage: setRaw }}>
      {children}
    </UsageContext.Provider>
  )
}

export function useUsage(): UsageContextValue {
  const ctx = useContext(UsageContext)
  if (!ctx) throw new Error('useUsage must be used inside UsageProvider')
  return ctx
}
