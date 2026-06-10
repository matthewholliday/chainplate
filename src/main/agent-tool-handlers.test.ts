import { mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'fs/promises'
import { tmpdir } from 'os'
import { join } from 'path'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  handleExecuteCommand,
  handleListDirectory,
  handleReadFile,
  handleWriteFile,
  resolveToolPath
} from './agent-tool-handlers'

describe('resolveToolPath', () => {
  it('resolves relative paths against workspace root', () => {
    expect(resolveToolPath('/workspace', 'src/index.ts')).toBe(
      join('/workspace', 'src/index.ts')
    )
  })

  it('returns path unchanged when workspace root is unset', () => {
    expect(resolveToolPath(undefined, '/absolute/path.txt')).toBe('/absolute/path.txt')
  })
})

describe('agent tool handlers', () => {
  let workspace: string

  beforeEach(async () => {
    workspace = await mkdtemp(join(tmpdir(), 'chainplate-agent-'))
    await writeFile(join(workspace, 'readme.txt'), 'hello world', 'utf-8')
    await mkdir(join(workspace, 'nested'))
    await writeFile(join(workspace, 'nested', 'note.md'), 'nested file', 'utf-8')
  })

  afterEach(async () => {
    await rm(workspace, { recursive: true, force: true })
  })

  describe('handleReadFile', () => {
    it('reads a file relative to workspace root', async () => {
      const result = await handleReadFile('readme.txt', workspace)
      expect(result).toEqual({ success: true, content: 'hello world' })
    })

    it('reads nested files', async () => {
      const result = await handleReadFile('nested/note.md', workspace)
      expect(result).toEqual({ success: true, content: 'nested file' })
    })

    it('returns error for missing files', async () => {
      const result = await handleReadFile('missing.txt', workspace)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error).toContain('ENOENT')
      }
    })
  })

  describe('handleWriteFile', () => {
    it('writes and overwrites files in workspace', async () => {
      const write = await handleWriteFile('output.txt', 'first', workspace)
      expect(write).toEqual({ success: true })

      const overwrite = await handleWriteFile('output.txt', 'second', workspace)
      expect(overwrite).toEqual({ success: true })

      const content = await readFile(join(workspace, 'output.txt'), 'utf-8')
      expect(content).toBe('second')
    })

    it('creates files in nested directories when parent exists', async () => {
      const result = await handleWriteFile('nested/new.txt', 'created', workspace)
      expect(result).toEqual({ success: true })
    })
  })

  describe('handleListDirectory', () => {
    it('lists files and directories', async () => {
      const result = await handleListDirectory('.', workspace)
      expect(result.success).toBe(true)
      if (result.success) {
        const names = result.items.map((i) => i.name).sort()
        expect(names).toContain('readme.txt')
        expect(names).toContain('nested')
        const nested = result.items.find((i) => i.name === 'nested')
        expect(nested?.type).toBe('directory')
      }
    })

    it('returns error for missing directory', async () => {
      const result = await handleListDirectory('does-not-exist', workspace)
      expect(result.success).toBe(false)
    })
  })

  describe('handleExecuteCommand', () => {
    it('runs commands in workspace root', async () => {
      const result = await handleExecuteCommand('echo chainplate-test', { workspaceRoot: workspace })
      expect(result).toEqual({ success: true, stdout: 'chainplate-test', stderr: '' })
    })

    it('uses explicit cwd when provided', async () => {
      const result = await handleExecuteCommand('pwd', { cwd: workspace })
      expect(result.success).toBe(true)
      if (result.success) {
        const resolvedWorkspace = await realpath(workspace)
        expect(result.stdout).toBe(resolvedWorkspace)
      }
    })

    it('captures stderr on failing commands', async () => {
      const result = await handleExecuteCommand('ls definitely-missing-file', {
        workspaceRoot: workspace
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error).toBeTruthy()
      }
    })
  })
})
