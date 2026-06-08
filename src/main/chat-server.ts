import { anthropic } from '@ai-sdk/anthropic'
import { resolveAnthropicModelId } from '../shared/models'
import { frontendTools } from '@assistant-ui/react-ai-sdk'
import { convertToModelMessages, streamText, stepCountIs, tool } from 'ai'
import type { UIMessage } from 'ai'
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { serve, type ServerType } from '@hono/node-server'
import { readFile, writeFile, readdir } from 'fs/promises'
import { exec } from 'child_process'
import { promisify } from 'util'
import { resolve as resolvePath } from 'path'
import { z } from 'zod'

const execAsync = promisify(exec)

// Converts old-format messages (content: ContentPart[]) to AI SDK v6 UIMessage format (parts: UIMessagePart[]).
// Messages saved from earlier sessions may be in assistant-ui ThreadMessage format without `parts`.
function normalizeMessages(messages: UIMessage[]): UIMessage[] {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return messages.map((msg: any) => {
    if (Array.isArray(msg.parts)) return msg
    if (Array.isArray(msg.content)) {
      return {
        ...msg,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        parts: msg.content.map((c: any) =>
          c.type === 'text' ? { type: 'text', text: c.text ?? '' } : c
        )
      }
    }
    if (typeof msg.content === 'string') {
      return { ...msg, parts: [{ type: 'text', text: msg.content }] }
    }
    return msg
  })
}

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

let lastUsage: UsageData | null = null

function isAllowedOrigin(origin: string | undefined): boolean {
  if (!origin) return true
  return (
    origin.startsWith('http://localhost:') ||
    origin.startsWith('http://127.0.0.1:') ||
    origin.startsWith('file://')
  )
}

export async function startChatServer(): Promise<ChatServerInfo> {
  if (chatServerInfo) {
    return chatServerInfo
  }

  const configured = Boolean(process.env.ANTHROPIC_API_KEY)

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
    if (!configured) {
      return c.json(
        { error: 'ANTHROPIC_API_KEY is not set. Add it to .env and restart the app.' },
        503
      )
    }

    try {
      const body = await c.req.json<{
        messages: UIMessage[]
        system?: string
        tools?: unknown
        metadata?: { custom?: { model?: unknown } }
      }>()
      const { messages, system, tools, metadata } = body
      const modelId = resolveAnthropicModelId(metadata?.custom?.model)

      const result = streamText({
        model: anthropic(modelId),
        system,
        messages: await convertToModelMessages(normalizeMessages(messages)),
        tools: frontendTools(tools as Parameters<typeof frontendTools>[0]),
        onFinish({ usage }) {
          lastUsage = {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          }
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
    if (!configured) {
      return c.json(
        { error: 'ANTHROPIC_API_KEY is not set. Add it to .env and restart the app.' },
        503
      )
    }

    try {
      const body = await c.req.json<{
        messages: UIMessage[]
        system?: string
        enabledTools?: string[]
        workspaceRoot?: string
        metadata?: { custom?: { model?: unknown } }
      }>()
      const { messages, system, enabledTools, workspaceRoot, metadata } = body
      const modelId = resolveAnthropicModelId(metadata?.custom?.model)

      const allTools = {
        read_file: tool({
          description: 'Read the contents of a file at the given path.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the file to read.')
          }),
          execute: async ({ path }) => {
            try {
              const resolved = workspaceRoot ? resolvePath(workspaceRoot, path) : path
              const content = await readFile(resolved, 'utf-8')
              return { success: true, content }
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) }
            }
          }
        }),
        write_file: tool({
          description: 'Write content to a file at the given path, creating it if it does not exist.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the file to write.'),
            content: z.string().describe('Content to write to the file.')
          }),
          execute: async ({ path, content }) => {
            try {
              const resolved = workspaceRoot ? resolvePath(workspaceRoot, path) : path
              await writeFile(resolved, content, 'utf-8')
              return { success: true }
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) }
            }
          }
        }),
        list_directory: tool({
          description: 'List the files and subdirectories in a directory.',
          inputSchema: z.object({
            path: z.string().describe('Absolute or relative path to the directory to list.')
          }),
          execute: async ({ path }) => {
            try {
              const resolved = workspaceRoot ? resolvePath(workspaceRoot, path) : path
              const entries = await readdir(resolved, { withFileTypes: true })
              const items = entries.map((e) => ({
                name: e.name,
                type: e.isDirectory() ? 'directory' : 'file'
              }))
              return { success: true, items }
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) }
            }
          }
        }),
        execute_command: tool({
          description: 'Run a shell command and return its stdout and stderr output.',
          inputSchema: z.object({
            command: z.string().describe('The shell command to execute.'),
            cwd: z.string().optional().describe('Working directory for the command. Defaults to the workspace root if set, otherwise the process cwd.')
          }),
          execute: async ({ command, cwd }) => {
            try {
              const effectiveCwd = cwd ?? workspaceRoot ?? process.cwd()
              const { stdout, stderr } = await execAsync(command, {
                cwd: effectiveCwd,
                timeout: 30_000
              })
              return { success: true, stdout: stdout.trim(), stderr: stderr.trim() }
            } catch (err: unknown) {
              const e = err as { stdout?: string; stderr?: string; message?: string }
              return {
                success: false,
                stdout: e.stdout?.trim() ?? '',
                stderr: e.stderr?.trim() ?? '',
                error: e.message ?? String(err)
              }
            }
          }
        })
      }

      const tools = enabledTools
        ? Object.fromEntries(
            Object.entries(allTools).filter(([k]) => enabledTools.includes(k))
          )
        : allTools

      const result = streamText({
        model: anthropic(modelId),
        system,
        messages: await convertToModelMessages(normalizeMessages(messages)),
        stopWhen: stepCountIs(20),
        tools,
        onFinish({ usage }) {
          lastUsage = {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          }
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
    return c.json(lastUsage)
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
            `[chat-server] ANTHROPIC_API_KEY is missing. Set it in .env and restart. (${chatServerInfo.url})`
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
}
