"use strict";
require("dotenv/config");
const electron = require("electron");
const path = require("path");
const utils = require("@electron-toolkit/utils");
const anthropic = require("@ai-sdk/anthropic");
const reactAiSdk = require("@assistant-ui/react-ai-sdk");
const ai = require("ai");
const hono = require("hono");
const cors = require("hono/cors");
const nodeServer = require("@hono/node-server");
const promises = require("fs/promises");
const child_process = require("child_process");
const util = require("util");
const zod = require("zod");
const AGENT_TOOLS = [
  {
    id: "read_file",
    label: "Read File",
    description: "Read the contents of a file at a given path."
  },
  {
    id: "write_file",
    label: "Write File",
    description: "Write content to a file, creating it if it does not exist."
  },
  {
    id: "list_directory",
    label: "List Directory",
    description: "List files and subdirectories in a directory."
  },
  {
    id: "execute_command",
    label: "Execute Command",
    description: "Run a shell command and return its stdout/stderr output."
  }
];
AGENT_TOOLS.map((t) => t.id);
const ANTHROPIC_MODELS = [
  { id: "claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
  { id: "claude-opus-4-6", label: "Claude Opus 4.6" },
  { id: "claude-haiku-4-5", label: "Claude Haiku 4.5" }
];
const DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6";
function isAnthropicModelId(value) {
  return typeof value === "string" && ANTHROPIC_MODELS.some((model) => model.id === value);
}
function resolveAnthropicModelId(value) {
  return isAnthropicModelId(value) ? value : DEFAULT_ANTHROPIC_MODEL;
}
const execAsync = util.promisify(child_process.exec);
function normalizeMessages(messages) {
  return messages.map((msg) => {
    if (Array.isArray(msg.parts)) return msg;
    if (Array.isArray(msg.content)) {
      return {
        ...msg,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        parts: msg.content.map(
          (c) => c.type === "text" ? { type: "text", text: c.text ?? "" } : c
        )
      };
    }
    if (typeof msg.content === "string") {
      return { ...msg, parts: [{ type: "text", text: msg.content }] };
    }
    return msg;
  });
}
let chatServer = null;
let chatServerInfo = null;
const usageByConversation = /* @__PURE__ */ new Map();
function storeUsage(conversationId, usage) {
  if (!conversationId) return;
  usageByConversation.set(conversationId, usage);
}
function isAllowedOrigin(origin) {
  if (!origin) return true;
  return origin.startsWith("http://localhost:") || origin.startsWith("http://127.0.0.1:") || origin.startsWith("file://");
}
async function startChatServer() {
  if (chatServerInfo) {
    return chatServerInfo;
  }
  const configured = Boolean(process.env.ANTHROPIC_API_KEY);
  const app = new hono.Hono();
  app.use(
    "/api/*",
    cors.cors({
      origin: (origin) => isAllowedOrigin(origin) ? origin : "http://localhost",
      allowMethods: ["GET", "POST", "OPTIONS"],
      allowHeaders: ["Content-Type"]
    })
  );
  app.post("/api/chat", async (c) => {
    if (!configured) {
      return c.json(
        { error: "ANTHROPIC_API_KEY is not set. Add it to .env and restart the app." },
        503
      );
    }
    try {
      const body = await c.req.json();
      const { messages, system, tools, conversationId, metadata } = body;
      const modelId = resolveAnthropicModelId(metadata?.custom?.model);
      const result = ai.streamText({
        model: anthropic.anthropic(modelId),
        system,
        messages: await ai.convertToModelMessages(normalizeMessages(messages)),
        tools: reactAiSdk.frontendTools(tools),
        onFinish({ usage }) {
          storeUsage(conversationId, {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          });
        }
      });
      return result.toUIMessageStreamResponse();
    } catch (error) {
      console.error("Chat request failed:", error);
      return c.json(
        {
          error: "Failed to process chat request",
          details: error instanceof Error ? error.message : "Unknown error"
        },
        500
      );
    }
  });
  app.post("/api/agent", async (c) => {
    if (!configured) {
      return c.json(
        { error: "ANTHROPIC_API_KEY is not set. Add it to .env and restart the app." },
        503
      );
    }
    try {
      const body = await c.req.json();
      const { messages, system, enabledTools, workspaceRoot, conversationId, metadata } = body;
      const modelId = resolveAnthropicModelId(metadata?.custom?.model);
      const allTools = {
        read_file: ai.tool({
          description: "Read the contents of a file at the given path.",
          inputSchema: zod.z.object({
            path: zod.z.string().describe("Absolute or relative path to the file to read.")
          }),
          execute: async ({ path: path$1 }) => {
            try {
              const resolved = workspaceRoot ? path.resolve(workspaceRoot, path$1) : path$1;
              const content = await promises.readFile(resolved, "utf-8");
              return { success: true, content };
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) };
            }
          }
        }),
        write_file: ai.tool({
          description: "Write content to a file at the given path, creating it if it does not exist.",
          inputSchema: zod.z.object({
            path: zod.z.string().describe("Absolute or relative path to the file to write."),
            content: zod.z.string().describe("Content to write to the file.")
          }),
          execute: async ({ path: path$1, content }) => {
            try {
              const resolved = workspaceRoot ? path.resolve(workspaceRoot, path$1) : path$1;
              await promises.writeFile(resolved, content, "utf-8");
              return { success: true };
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) };
            }
          }
        }),
        list_directory: ai.tool({
          description: "List the files and subdirectories in a directory.",
          inputSchema: zod.z.object({
            path: zod.z.string().describe("Absolute or relative path to the directory to list.")
          }),
          execute: async ({ path: path$1 }) => {
            try {
              const resolved = workspaceRoot ? path.resolve(workspaceRoot, path$1) : path$1;
              const entries = await promises.readdir(resolved, { withFileTypes: true });
              const items = entries.map((e) => ({
                name: e.name,
                type: e.isDirectory() ? "directory" : "file"
              }));
              return { success: true, items };
            } catch (err) {
              return { success: false, error: err instanceof Error ? err.message : String(err) };
            }
          }
        }),
        execute_command: ai.tool({
          description: "Run a shell command and return its stdout and stderr output.",
          inputSchema: zod.z.object({
            command: zod.z.string().describe("The shell command to execute."),
            cwd: zod.z.string().optional().describe("Working directory for the command. Defaults to the workspace root if set, otherwise the process cwd.")
          }),
          execute: async ({ command, cwd }) => {
            try {
              const effectiveCwd = cwd ?? workspaceRoot ?? process.cwd();
              const { stdout, stderr } = await execAsync(command, {
                cwd: effectiveCwd,
                timeout: 3e4
              });
              return { success: true, stdout: stdout.trim(), stderr: stderr.trim() };
            } catch (err) {
              const e = err;
              return {
                success: false,
                stdout: e.stdout?.trim() ?? "",
                stderr: e.stderr?.trim() ?? "",
                error: e.message ?? String(err)
              };
            }
          }
        })
      };
      const tools = enabledTools ? Object.fromEntries(
        Object.entries(allTools).filter(([k]) => enabledTools.includes(k))
      ) : allTools;
      const result = ai.streamText({
        model: anthropic.anthropic(modelId),
        system,
        messages: await ai.convertToModelMessages(normalizeMessages(messages)),
        stopWhen: ai.stepCountIs(20),
        tools,
        onFinish({ usage }) {
          storeUsage(conversationId, {
            promptTokens: usage.inputTokens ?? 0,
            completionTokens: usage.outputTokens ?? 0
          });
        }
      });
      return result.toUIMessageStreamResponse();
    } catch (error) {
      console.error("Agent request failed:", error);
      return c.json(
        {
          error: "Failed to process agent request",
          details: error instanceof Error ? error.message : "Unknown error"
        },
        500
      );
    }
  });
  app.get("/api/usage", (c) => {
    const conversationId = c.req.query("conversationId");
    if (!conversationId) {
      return c.json(null);
    }
    return c.json(usageByConversation.get(conversationId) ?? null);
  });
  return new Promise((resolve, reject) => {
    chatServer = nodeServer.serve(
      {
        fetch: app.fetch,
        hostname: "127.0.0.1",
        port: 0
      },
      (info) => {
        chatServerInfo = {
          url: `http://127.0.0.1:${info.port}`,
          configured
        };
        if (!configured) {
          console.error(
            `[chat-server] ANTHROPIC_API_KEY is missing. Set it in .env and restart. (${chatServerInfo.url})`
          );
        } else {
          console.log(`[chat-server] Listening on ${chatServerInfo.url}`);
        }
        resolve(chatServerInfo);
      }
    );
    chatServer.on("error", (error) => {
      reject(error);
    });
  });
}
function getChatServerInfo() {
  return chatServerInfo;
}
function stopChatServer() {
  if (chatServer) {
    chatServer.close();
    chatServer = null;
    chatServerInfo = null;
  }
}
function createWindow() {
  const mainWindow = new electron.BrowserWindow({
    width: 1100,
    height: 780,
    minWidth: 640,
    minHeight: 480,
    show: false,
    backgroundColor: "#252525",
    title: "Chainplate",
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });
  mainWindow.webContents.setWindowOpenHandler((details) => {
    electron.shell.openExternal(details.url);
    return { action: "deny" };
  });
  if (utils.is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
    mainWindow.webContents.on("console-message", (_event, _level, message) => {
      console.log(`[renderer] ${message}`);
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}
electron.app.whenReady().then(async () => {
  electron.nativeTheme.themeSource = "dark";
  electron.Menu.setApplicationMenu(null);
  utils.electronApp.setAppUserModelId("com.chainplate.chat");
  electron.app.on("browser-window-created", (_, window) => {
    utils.optimizer.watchWindowShortcuts(window);
  });
  electron.ipcMain.handle("dialog:selectFolder", async () => {
    const { canceled, filePaths } = await electron.dialog.showOpenDialog({
      properties: ["openDirectory", "createDirectory"]
    });
    return canceled ? null : filePaths[0];
  });
  electron.ipcMain.handle("knowledge:index", async (_event, workspaceId, folderPath) => {
    const { indexKnowledge } = await Promise.resolve().then(() => require("./knowledge-indexer-h-7Faqda.js"));
    return indexKnowledge(workspaceId, folderPath);
  });
  electron.ipcMain.handle("knowledge:getIndexMeta", async (_event, workspaceId) => {
    const { getIndexMeta } = await Promise.resolve().then(() => require("./knowledge-indexer-h-7Faqda.js"));
    return getIndexMeta(workspaceId);
  });
  electron.ipcMain.handle("knowledge:searchChunks", async (_event, workspaceId, query) => {
    const { searchChunks } = await Promise.resolve().then(() => require("./knowledge-indexer-h-7Faqda.js"));
    return searchChunks(workspaceId, query);
  });
  electron.ipcMain.handle("chat:getApiUrl", () => {
    const info = getChatServerInfo();
    if (!info) {
      throw new Error("Chat server is not running");
    }
    return info;
  });
  await startChatServer();
  createWindow();
  electron.app.on("activate", function() {
    if (electron.BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
electron.app.on("will-quit", () => {
  stopChatServer();
});
