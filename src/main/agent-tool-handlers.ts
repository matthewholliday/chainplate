import { readFile, writeFile, readdir } from 'fs/promises'
import { exec } from 'child_process'
import { promisify } from 'util'
import { resolve as resolvePath } from 'path'

const execAsync = promisify(exec)

export function resolveToolPath(workspaceRoot: string | undefined, path: string): string {
  return workspaceRoot ? resolvePath(workspaceRoot, path) : path
}

export async function handleReadFile(
  path: string,
  workspaceRoot?: string
): Promise<{ success: true; content: string } | { success: false; error: string }> {
  try {
    const resolved = resolveToolPath(workspaceRoot, path)
    const content = await readFile(resolved, 'utf-8')
    return { success: true, content }
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export async function handleWriteFile(
  path: string,
  content: string,
  workspaceRoot?: string
): Promise<{ success: true } | { success: false; error: string }> {
  try {
    const resolved = resolveToolPath(workspaceRoot, path)
    await writeFile(resolved, content, 'utf-8')
    return { success: true }
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export async function handleListDirectory(
  path: string,
  workspaceRoot?: string
): Promise<
  | { success: true; items: Array<{ name: string; type: 'directory' | 'file' }> }
  | { success: false; error: string }
> {
  try {
    const resolved = resolveToolPath(workspaceRoot, path)
    const entries = await readdir(resolved, { withFileTypes: true })
    const items = entries.map((e) => ({
      name: e.name,
      type: e.isDirectory() ? ('directory' as const) : ('file' as const)
    }))
    return { success: true, items }
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export async function handleExecuteCommand(
  command: string,
  options: { cwd?: string; workspaceRoot?: string } = {}
): Promise<
  | { success: true; stdout: string; stderr: string }
  | { success: false; stdout: string; stderr: string; error: string }
> {
  const { cwd, workspaceRoot } = options
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
