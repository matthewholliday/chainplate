export const createMCPClient = (): never => {
  throw new Error('MCP is not available in the renderer process')
}
