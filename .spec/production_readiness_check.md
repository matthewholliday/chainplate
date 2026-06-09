# Production Readiness Check: Chainplate as an Open-Source Coding Agent

**Date:** 2026-06-08  
**Scope:** Functional and non-functional gaps required to distribute Chainplate reliably as an open-source coding agent. Prioritizes reliability of existing core features over new capabilities; essential missing features are included where they block trustworthy agent use.

---

## Executive Summary

Chainplate is a functional Electron desktop app with a credible agent loop (chat + agent modes, four filesystem/shell tools, RAG, workspaces, conversation persistence). Typecheck and production build pass today.

It is **not yet ready** for reliable open-source distribution as a coding agent. The largest risks are:

1. **No automated test or CI coverage** for the actual TypeScript/Electron codebase (CI still targets a removed Python project).
2. **Agent tool execution lacks workspace sandboxing and user approval**, making destructive or out-of-scope operations possible without guardrails.
3. **Open-source hygiene is incomplete** (no license, missing `.env.example`, stale docs and packaging config, README undersells agent behavior and safety expectations).
4. **Several core reliability bugs** (global usage tracking with concurrent conversations, disconnected workspace vs. RAG knowledge, silent persistence failures).

**Verdict:** Suitable for private/local experimentation. Requires a focused hardening pass before public OSS release where users will run agent mode against real repositories.

---

## Current State (What Works)

| Area | Status | Notes |
|------|--------|-------|
| Chat streaming | Working | Anthropic via Vercel AI SDK; local Hono server on `127.0.0.1` |
| Agent mode | Working | `read_file`, `write_file`, `list_directory`, `execute_command`; 20-step budget |
| Tool UI | Working | Enable/disable tools, collapsible tool call display |
| RAG | Working (basic) | Cosine similarity over chunked text index; manual (re-)index |
| Workspaces | Working | Folder-scoped `workspaceRoot` passed to agent endpoint |
| Conversations | Working | localStorage persistence, background runs, sidebar |
| Model selection | Working | Three Anthropic models; stored in localStorage |
| System prompt | Working | Configurable via Data modal |
| Context indicator | Partial | Shows last response input token % of 200k window |
| Build | Passing | `npm run typecheck` and `npm run build` succeed |
| Security (API key) | Partial | Key stays in main process; renderer talks only to local server |

---

## Gap Analysis

### P0: Blockers for Reliable OSS Distribution

These must be addressed before recommending the project to external users.

#### 1. Quality gates and CI are absent / wrong

- **No project-owned tests.** Zero `*.test.*` / `*.spec.*` files under `src/`.
- **`.github/workflows/main.yml` is stale.** It runs Python `unittest` against `requirements.txt` and `tests/`, none of which exist in this codebase. Every push/PR either fails or provides false confidence.
- **`npm run lint` reports 85 errors** (plus ~1160 Prettier warnings). Lint is not enforced in CI.
- **No release build verification** in CI (electron-builder packaging untested in automation).

**Risk:** Regressions in agent tools, message persistence, or streaming will ship undetected.

**Acceptance criteria:**
- CI runs on `ubuntu-latest` (minimum): `npm ci`, `typecheck`, `lint`, `test`, `build`.
- At least smoke/integration tests for `chat-server` agent tools and `knowledge-indexer`.
- Stale Python workflow and instructions removed or replaced.

#### 2. Agent tool sandboxing is missing

`chat-server.ts` resolves paths with `resolvePath(workspaceRoot, path)` but **never verifies the result stays inside `workspaceRoot`**. A model (or prompt injection) can supply `../../../etc/passwd` or write outside the project.

When no `workspaceRoot` is set (HOME workspace), tools accept **absolute paths anywhere on disk** or fall back to `process.cwd()` for shell commands.

`execute_command` runs arbitrary shell with only a 30s timeout. No allowlist, blocklist, or workspace confinement.

**Risk:** Data loss, credential exfiltration, system compromise. Unacceptable for a public coding agent.

**Acceptance criteria:**
- All file tools reject paths that escape `workspaceRoot` after normalization (including symlinks where feasible).
- `execute_command` requires an explicit `workspaceRoot`; cwd constrained to that root.
- HOME workspace prompts user to select a project folder before agent mode is enabled, or agent mode is disabled until a workspace with `rootFolder` is active.
- Documented threat model in README/SECURITY.md.

#### 3. No confirmation for destructive agent actions

`write_file` and `execute_command` run immediately with no user approval step. Industry-standard coding agents (Cursor, Claude Code, etc.) gate destructive operations.

**Risk:** Model hallucination or mis-parsed intent causes irreversible changes.

**Acceptance criteria:**
- Configurable approval policy (e.g. always approve writes and shell commands, or approve only shell).
- UI shows pending tool call with diff preview for writes where practical.
- User can reject individual tool calls without aborting the whole thread.

#### 4. Open-source legal and onboarding gaps

| Missing | Impact |
|---------|--------|
| `LICENSE` | Cannot legally redistribute or accept contributions |
| `.env.example` | README references `cp .env.example .env` but file does not exist |
| `CONTRIBUTING.md` | No contribution workflow |
| `SECURITY.md` | No vulnerability reporting path |
| `CODE_OF_CONDUCT.md` | Expected for public OSS communities |

`package.json` still lists `author: "example.com"` and `homepage: "https://electron-vite.org"`. `electron-builder.yml` uses template `appId: com.electron.app`, `productName: app`, placeholder auto-update URL, `notarize: false`.

**Acceptance criteria:**
- SPDX license committed (project owner chooses; MIT or Apache-2.0 typical for agent tooling).
- `.env.example` with `ANTHROPIC_API_KEY=` documented.
- Packaging metadata reflects Chainplate branding.
- Mac build path documented (signing/notarization requirements stated even if not automated).

#### 5. Documentation does not match the product

`README.md` describes a generic "desktop AI chat application." It omits:

- Agent mode and tool capabilities
- Workspace model and HOME vs. project workspaces
- RAG setup and limitations (lexical cosine, not embeddings)
- Safety expectations for shell/file tools
- Architecture of the agent loop (`AGENT_LOOP.md` exists but is not linked)

`.github/instructions/chainplate.instructions.md` still documents a **Python XML workflow engine** (`src/chainplate/`, `tests/`, `requirements.txt`). This will mislead contributors and AI tooling.

**Acceptance criteria:**
- README covers setup, agent mode, workspaces, RAG, security warnings, and development commands.
- Stale Python/Copilot instructions removed or rewritten for Electron/TypeScript layout.
- `AGENT_LOOP.md` linked as architecture reference or merged into docs.

---

### P1: Core Reliability (Existing Features)

Fix these to make current features dependable for daily use.

#### 6. Workspace and RAG knowledge are disconnected

- Workspaces store `rootFolder` for agent tools.
- RAG uses a separate global `KNOWLEDGE_LOCATION_STORAGE_KEY` in the Data modal.
- Creating a workspace does **not** auto-index its folder for RAG.
- Knowledge index is a **single global file** (`userData/knowledge-index.json`), not per-workspace.

**Risk:** Users enable RAG expecting project context but query the wrong index, or stale index from another repo pollutes answers.

**Recommendation:** Bind RAG index to `workspaceId`; auto-(re)index when workspace folder changes; surface index status in sidebar.

#### 7. Concurrent conversation usage tracking is wrong

`lastUsage` in `chat-server.ts` is a **process-global singleton**. Background conversations finishing out of order overwrite each other's usage. The context indicator can show wrong token counts.

**Recommendation:** Key usage by `conversationId` or request id; pass id from renderer in transport body.

#### 8. Message persistence is fragile

`App.tsx` contains substantial compatibility logic between UIMessage (`parts`) and ThreadMessage (`content`) formats. Comments document known broken `reset()` paths. `saveConversations` fails silently on quota errors.

**Risk:** Upgrades or edge cases corrupt conversation history (empty message shells already filtered on load).

**Recommendation:**
- Add migration/version field on stored conversations.
- Tests for round-trip save/load of tool-call messages.
- User-visible warning when localStorage write fails.
- Consider electron `safeStorage` or file-based persistence under `userData` for large histories.

#### 9. API key configuration is dev-only ergonomics

Key is read from `.env` at startup only. Packaged app users must create `.env` beside the binary or set env vars manually. No in-app settings UI.

**Recommendation:** Settings panel for API key (stored via `safeStorage`), validation ping, clear error when missing.

#### 10. Agent loop budget is fixed and opaque

`stopWhen: stepCountIs(20)` is hardcoded. `AGENT_LOOP.md` describes `MaxStepsAllowed` and timeout failure, but the app does not surface step budget exhaustion clearly or allow configuration.

**Recommendation:** Configurable max steps; terminal message when budget exhausted; optional per-request timeout.

#### 11. Error handling and recovery are thin

- Chat/agent 500 responses return JSON but streaming failures may not always surface in UI (`ErrorPrimitive` exists; coverage unclear for network drops).
- `UsageTracker` swallows fetch errors (`catch(() => {})`).
- No retry with backoff for transient Anthropic rate limits or 529 errors.
- No structured logging; only `console.error` in main process.

**Recommendation:** Retry policy for idempotent failures; user-visible retry button; log file under `userData` with rotation.

#### 12. Attachments are UI-only for the model

Composer supports image/file attachments in the UI, but `/api/chat` and `/api/agent` do not accept or forward attachment content to the model.

**Risk:** Users attach files expecting context; model never sees them.

**Recommendation:** Either wire attachments through to Anthropic multimodal API or disable/hide attachment UI until supported.

---

### P2: Essential Missing Features for a Credible Coding Agent

Not required for a minimal release, but expected by users comparing to other OSS agents.

| Feature | Why it matters |
|---------|----------------|
| `search` / `grep` tool | Navigating codebases without expensive `list_directory` + `read_file` chains |
| `apply_patch` or `edit_file` | Surgical edits; full `write_file` is error-prone on large files |
| Git tools (`git status`, `git diff`, `git commit` with safeguards) | Core coding-agent workflow |
| Semantic RAG (embeddings) | Lexical cosine misses paraphrased queries; critical for large repos |
| Headless / CLI mode | CI, scripting, and OSS adoption without Electron GUI |
| Multi-provider support | Anthropic-only limits contributor audience; abstract provider interface |
| MCP tool integration | Stubs exist (`src/renderer/src/stubs/ai-sdk-mcp/`) but are not wired |
| Export/import conversations | Backup and portability beyond localStorage |
| Auto-update channel | `electron-builder` publish config is placeholder |

---

### Non-Functional Requirements

| Requirement | Current | Target for OSS |
|-------------|---------|----------------|
| **Testability** | None | Unit + integration tests for tools, indexer, persistence |
| **CI/CD** | Broken Python pipeline | Node CI matrix; optional macOS build job |
| **Security** | API key isolated; tools unsandboxed | Sandboxed tools, approval flow, SECURITY.md |
| **Observability** | Console logs | File logs, optional debug mode |
| **Portability** | macOS-focused dev (hiddenInset title bar) | Verified Win/Linux builds; platform notes |
| **Performance** | RAG loads full index into memory | Pagination or sqlite index for large repos |
| **Accessibility** | Partial aria labels | Audit composer, dialogs, sidebar |
| **Privacy** | No telemetry (good) | Document explicitly; no accidental data egress |
| **Dependency hygiene** | `node_modules` standard | Lockfile committed; Dependabot/Renovate |
| **Bundle size** | Renderer chunk ~2.25 MB | Acceptable for Electron; monitor |

---

## Legacy Artifact Cleanup

The repo retains files from a prior Python/XML workflow project. These actively harm OSS onboarding:

| Artifact | Problem |
|----------|---------|
| `.github/workflows/main.yml` | Python tests for nonexistent code |
| `.github/instructions/chainplate.instructions.md` | Documents Python package layout |
| `.dockerignore` | Python venv, `chainplate.db`, `tests/` |
| `.gitignore` | `__pycache__`, `secrets`; missing `node_modules`, `out/`, `.env` |
| `package.json` description | "An Electron application with React and TypeScript" |

Clean up in the same pass as CI introduction.

---

## Recommended Roadmap

### Phase 1: Trust and gates (1 to 2 weeks)

1. Add `LICENSE`, `.env.example`, `SECURITY.md`, `CONTRIBUTING.md`
2. Replace CI with Node pipeline; add tests for path sandboxing and tool execution
3. Implement workspace path containment and disable agent mode without workspace root
4. Update README and remove stale Python instructions
5. Fix `electron-builder.yml` and package metadata

### Phase 2: Core reliability (2 to 3 weeks)

1. Per-conversation usage tracking
2. Workspace-scoped RAG with auto-index on workspace create/change
3. Tool approval UI for `write_file` and `execute_command`
4. In-app API key settings with `safeStorage`
5. Conversation persistence tests and storage failure warnings
6. Retry/backoff for API errors; basic file logging

### Phase 3: Coding-agent completeness (ongoing)

1. `grep` and `apply_patch` tools
2. Git read tools (status/diff/log); guarded commit only with explicit opt-in
3. Embedding-based RAG option
4. CLI/headless entry point exposing the same agent loop
5. MCP server support

---

## Release Checklist (Definition of Done)

Before tagging `v1.0.0` as an open-source coding agent:

- [ ] CI green on PRs: typecheck, lint, test, build
- [ ] LICENSE and SECURITY.md present
- [ ] README accurately documents agent mode, tools, RAG, and risks
- [ ] `.env.example` exists; packaged app can configure API key without manual env files
- [ ] Agent file/shell tools cannot escape workspace root
- [ ] Destructive tool calls require user approval (configurable)
- [ ] At least one integration test runs agent tool chain end-to-end
- [ ] Fresh clone → `npm install` → `npm run dev` works on documented Node version
- [ ] macOS/Windows/Linux build instructions verified by a second machine or CI
- [ ] No stale Python project references in repo docs or automation
- [ ] Known limitations documented (Anthropic-only, lexical RAG, localStorage persistence, 20-step cap)

---

## Appendix: Architecture Reference

```
Renderer (React + assistant-ui)
  → AssistantChatTransport → http://127.0.0.1:<port>/api/{chat|agent}
Main process (Hono chat-server)
  → streamText (Vercel AI SDK + Anthropic)
  → agent tools: read/write/list/exec (main process fs/child_process)
  → knowledge-indexer (IPC): index + search for RAG
Persistence: localStorage (conversations, workspaces, settings)
```

Agent loop intent is documented in `AGENT_LOOP.md` (generate → route → execute → update memory → budget). Implementation maps to AI SDK multi-step `streamText` with `stepCountIs(20)` rather than an explicit custom loop, which is acceptable if step limits and error paths are made visible and tested.
