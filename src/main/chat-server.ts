import { anthropic } from '@ai-sdk/anthropic'
import { createOpenAI } from '@ai-sdk/openai'
import { resolveProviderSelection, type ProviderSelection } from '../shared/models'
import { normalizeMessages } from '../shared/normalize-messages'
import {
  handleExecuteCommand,
  handleListDirectory,
  handleReadFile,
  handleWriteFile
} from './agent-tool-handlers'
import {
  getApiKey,
  getProviderConfig,
  hasAnyConfiguredProvider,
  isProviderConfigured
} from './provider-config'
import { frontendTools } from '@assistant-ui/react-ai-sdk'
import { convertToModelMessages, streamText, stepCountIs, tool } from 'ai'
import type { LanguageModel, UIMessage } from 'ai'
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { serve, type ServerType } from '@hono/node-server'
import { z } from 'zod'

export type ChatServerInfo = {
  url: string
  configured: boolean
}

let chatServer: ServerType | null = null
let chatServerInfo: ChatServerInfo | null = null

type UsageData = {
  promptTokens: number
  completionTokens: number
}

const usageByConversation = new Map<string, UsageData>()

function storeUsage(conversationId: string | undefined, usage: UsageData): void {
  if (!conversationId) return
  usageByConversation.set(conversationId, usage)
}

function isAllowedOrigin(origin: string | undefined): boolean {
  if (!origin) return true
  return (
    origin.startsWith('http://localhost:') ||
    origin.startsWith('http://127.0.0.1:') ||
    origin.startsWith('file://')
  )
}

function resolveSelection(metadata?: {
  custom?: { provider?: unknown; model?: unknown; contextWindow?: unknown }
}): ProviderSelection {
  return resolveProviderSelection({
    providerId: metadata?.custom?.provider,
    modelId: metadata?.custom?.model,
    contextWindow:
      typeof metadata?.custom?.contextWindow === 'number'
        ? metadata.custom.contextWindow
        : undefined
  })
}

function resolveModel(selection: ProviderSelection): LanguageModel {
  const config = getProviderConfig(selection.providerId)
  if (!config) {
    throw new Error(`Unknown provider: ${selection.providerId}`)
  }

  if (!isProviderConfigured(config)) {
    throw new Error(`Provider "${config.label}" is not configured`)
  }

  const apiKey = getApiKey(config.id)

  if (config.type === 'anthropic') {
    return anthropic(selection.modelId)
  }

  if (config.type === 'openai') {
    return createOpenAI({ apiKey })(selection.modelId)
  }

  return createOpenAI({
    baseURL: config.baseUrl,
    apiKey: apiKey ?? 'ollama'
  })(selection.modelId)
}

function providerErrorMessage(selection: ProviderSelection): string {
  const config = getProviderConfig(selection.providerId)
  if (!config) {
    return `Unknown provider "${selection.providerId}". Configure providers in settings.`
  }

  if (config.type === 'openai-compatible') {
    return `Provider "${config.label}" is not configured. Add a base URL in provider settings.`
  }

  return `Provider "${config.label}" is not configured. Add an API key in provider settings.`
}

export async function startChatServer(): Promise<ChatServerInfo> {
  if (chatServerInfo) {
    return chatServerInfo
  }

  const configured = hasAnyConfiguredProvider()

  const app = new Hono()

  app.use(
    '/api/*',
    cors({
      origin: (origin) => (isAllowedOrigin(origin) ? origin : 'http://localhost'),
      allowMethods: ['GET', 'POST', 'OPTIONS'],
      allowHeaders: ['Content-Type']
    })
  )

  app.post('/api/chat', async (c) => {
    try {
      const body = await c.req.json<{
        messages: UIMessage[]
        system?: string
        tools?: unknown
        conversationId?: string
        metadata?: { custom?: { provider?: unknown; model?: unknown; contextWindow?: unknown } }
      }>()
      const { messages, system, tools, conversationId, metadata } = body
      const selection = resolveSelection(metadata)

      const providerConfig = getProviderConfig(selection.providerId)
      if (!providerConfig || !isProviderConfigured(providerConfig)) {
        return c.json({ error: providerErrorMessage(selection) }, 503)
      }

      const result = streamText({
        model: resolveModel(selection),
        system,
        messages: await convertToModelMessages(normalizeMessages(messages)),
        tools: frontendTools(tools as Parameters<typeof frontendTools>[0]),
        onFinish({ usage }) {
          storeUsage(conversationId, {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          })
        }
      })

      return result.toUIMessageStreamResponse()
    } catch (error) {
      console.error('Chat request failed:', error)
      return c.json(
        {
          error: 'Failed to process chat request',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        500
      )
    }
  })

  app.post('/api/agent', async (c) => {
    try {
      const body = await c.req.json<{
        messages: UIMessage[]
        system?: string
        enabledTools?: string[]
        workspaceRoot?: string
        conversationId?: string
        metadata?: { custom?: { provider?: unknown; model?: unknown; contextWindow?: unknown } }
      }>()
      const { messages, system, enabledTools, workspaceRoot, conversationId, metadata } = body
      const selection = resolveSelection(metadata)

      const providerConfig = getProviderConfig(selection.providerId)
      if (!providerConfig || !isProviderConfigured(providerConfig)) {
        return c.json({ error: providerErrorMessage(selection) }, 503)
      }

      const allTools = {
        read_file: tool({
          description: 'Read the contents of a file at the given path.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the file to read.')
          }),
          execute: async ({ path }) => handleReadFile(path, workspaceRoot)
        }),
        write_file: tool({
          description: 'Write content to a file at the given path, creating it if not exist.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the file to write.'),
            content: z.string().describe('Content to write to the file.')
          }),
          execute: async ({ path, content }) => handleWriteFile(path, content, workspaceRoot)
        }),
        list_directory: tool({
          description: 'List the files and subdirectories in a directory.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the directory to list.')
          }),
          execute: async ({ path }) => handleListDirectory(path, workspaceRoot)
        }),
        execute_command: tool({
          description: 'Run a shell command and return its stdout and stderr output.',
          inputSchema: z.object({
            command: z.string().describe('The shell command to execute.'),
            cwd: z
              .string()
              .optional()
              .describe(
                'Working directory for the command. Defaults to the workspace root if set, otherwise the process cwd.'
              )
          }),
          execute: async ({ command, cwd }) =>
            handleExecuteCommand(command, { cwd, workspaceRoot })
        })
      }

      const tools = enabledTools
        ? Object.fromEntries(
            Object.entries(allTools).filter(([k]) => enabledTools.includes(k))
          )
        : allTools

      const result = streamText({
        model: resolveModel(selection),
        system,
        messages: await convertToModelMessages(normalizeMessages(messages)),
        stopWhen: stepCountIs(20),
        tools,
        onFinish({ usage }) {
          storeUsage(conversationId, {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          })
        }
      })

      return result.toUIMessageStreamResponse()
    } catch (error) {
      console.error('Agent request failed:', error)
      return c.json(
        {
          error: 'Failed to process agent request',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        500
      )
    }
  })

  app.get('/api/usage', (c) => {
    const conversationId = c.req.query('conversationId')
    if (!conversationId) {
      return c.json(null)
    }
    return c.json(usageByConversation.get(conversationId) ?? null)
  })

  return new Promise((resolve, reject) => {
    chatServer = serve(
      {
        fetch: app.fetch,
        hostname: '127.0.0.1',
        port: 0
      },
      (info) => {
        chatServerInfo = {
          url: `http://127.0.0.1:${info.port}`,
          configured
        }

        if (!configured) {
          console.error(
            `[chat-server] No LLM providers are configured. Add API keys or custom providers in settings. (${chatServerInfo.url})`
          )
        } else {
          console.log(`[chat-server] Listening on ${chatServerInfo.url}`)
        }

        resolve(chatServerInfo)
      }
    )

    chatServer.on('error', (error) => {
      reject(error)
    })
  })
}

export function getChatServerInfo(): ChatServerInfo | null {
  return chatServerInfo
}

export function stopChatServer(): void {
  if (chatServer) {
    chatServer.close()
    chatServer = null
    chatServerInfo = null
  }
  usageByConversation.clear()
}

export function setConversationUsage(conversationId: string, usage: UsageData): void {
  storeUsage(conversationId, usage)
}
