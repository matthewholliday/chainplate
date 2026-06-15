# Chainplate

A desktop AI chat application built with Electron, assistant-ui, Vercel AI SDK, and shadcn/ui.

## Prerequisites

- Node.js 20.19+ or 22.12+
- At least one configured AI provider (see [Supported AI Providers](#supported-ai-providers))

## Supported AI Providers

Chainplate supports built-in cloud providers and custom OpenAI-compatible endpoints. Configure API keys in `.env` for first-run setup, or add and edit providers in the in-app **LLM Providers** settings.

### Anthropic

| Model | Context window |
| --- | --- |
| Claude Sonnet 4.6 | 200K |
| Claude Opus 4.6 | 200K |
| Claude Haiku 4.5 | 200K |

- **API key**: `ANTHROPIC_API_KEY` in `.env`, or enter it in provider settings
- **SDK**: `@ai-sdk/anthropic`

### OpenAI

| Model | Context window |
| --- | --- |
| GPT-4.1 | ~1M |
| GPT-4.1 Mini | ~1M |
| GPT-4o | 128K |
| o3-mini | 200K |

- **API key**: `OPENAI_API_KEY` in `.env`, or enter it in provider settings
- **SDK**: `@ai-sdk/openai`

### OpenAI-compatible (custom)

Add any provider that exposes an OpenAI-compatible chat API, such as [Ollama](https://ollama.com/), LM Studio, or vLLM.

- **Configuration**: base URL, model list, and optional API key (not required for local servers)
- **Example base URL**: `http://localhost:11434/v1` (Ollama)
- **SDK**: `@ai-sdk/openai` with a custom `baseURL`

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure at least one provider:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set one or more of:

   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`

   You can also add or update providers later from the app settings UI.

## Development

Start the app with hot reload:

```bash
npm run dev
```

## Build

Type-check and build for production:

```bash
npm run build
npm run preview
```

Platform-specific packaging:

```bash
npm run build:mac
npm run build:win
npm run build:linux
```

## Architecture

- **Renderer**: React + assistant-ui chat interface (shadcn/ui components)
- **Main process**: Local Hono server on `127.0.0.1` that streams responses via Vercel AI SDK (Anthropic, OpenAI, or OpenAI-compatible providers)
- **Security**: API keys stay in the main process; the renderer only talks to the local chat endpoint

## Stack

- [Electron](https://www.electronjs.org/) + [electron-vite](https://electron-vite.org/)
- [assistant-ui](https://www.assistant-ui.com/)
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Anthropic](https://www.anthropic.com/) via `@ai-sdk/anthropic`
- [OpenAI](https://openai.com/) via `@ai-sdk/openai`
