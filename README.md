# Chainplate

A desktop AI chat application built with Electron, assistant-ui, Vercel AI SDK, and shadcn/ui.

## Prerequisites

- Node.js 20.19+ or 22.12+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure your API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `ANTHROPIC_API_KEY`.

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
- **Main process**: Local Hono server on `127.0.0.1` that streams responses via Vercel AI SDK + Anthropic
- **Security**: API keys stay in the main process; the renderer only talks to the local chat endpoint

## Stack

- [Electron](https://www.electronjs.org/) + [electron-vite](https://electron-vite.org/)
- [assistant-ui](https://www.assistant-ui.com/)
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Anthropic](https://www.anthropic.com/) via `@ai-sdk/anthropic`
