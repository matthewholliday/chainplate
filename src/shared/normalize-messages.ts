import type { UIMessage } from 'ai'

// Converts old-format messages (content: ContentPart[]) to AI SDK v6 UIMessage format (parts: UIMessagePart[]).
// Messages saved from earlier sessions may be in assistant-ui ThreadMessage format without `parts`.
export function normalizeMessages(messages: UIMessage[]): UIMessage[] {
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
