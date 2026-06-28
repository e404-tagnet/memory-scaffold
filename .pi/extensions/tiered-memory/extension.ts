/**
 * Tiered Memory Extension for LLM Agents
 *
 * Auto-manages RAM + ROM memory architecture:
 * - tier: ram (session-cache.md) - volatile, loaded first
 * - tier: hot (core.md, memories.md) - always loaded
 * - tier: warm (*-notes.md) - loaded on demand
 * - tier: cold (archived/) - search only
 *
 * Scans recursively from workspace root to find .md files.
 *
 * Commands:
 *   /cache          - Load session cache (RAM layer)
 *   /remember       - Add to memories.md (HOT)
 *   /load <name>    - Load warm tier file
 *   /search <query> - Search all workspace files
 *   /cache-update   - Update session cache with current state
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import * as fs from "node:fs";
import * as path from "node:path";

interface Frontmatter {
  tier?: "ram" | "hot" | "warm" | "cold";
  project?: string;
  created?: string;
  expires?: string;
  tags?: string[];
}

interface MemoryFile {
  filePath: string;
  name: string;
  frontmatter: Frontmatter;
  body: string;
}

class TieredMemorySystem {
  private workspacePath: string;
  private files: Map<string, MemoryFile> = new Map();

  constructor(workspacePath: string) {
    this.workspacePath = workspacePath;
  }

  async scan(): Promise<void> {
    this.files.clear();
    await this._scanDir(this.workspacePath);
  }

  private async _scanDir(dir: string): Promise<void> {
    const entries = await fs.promises.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        // Skip common noise dirs
        if (entry.name.startsWith(".") || entry.name === "node_modules" || entry.name === "__pycache__" || entry.name === "venv" || entry.name === ".git") {
          continue;
        }
        await this._scanDir(fullPath);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        try {
          const content = await fs.promises.readFile(fullPath, "utf-8");
          const { frontmatter, body } = parseFrontmatter(content);
          const relName = path.relative(this.workspacePath, fullPath);
          this.files.set(relName, {
            filePath: fullPath,
            name: entry.name.replace(/\.md$/, ""),
            frontmatter,
            body,
          });
        } catch {
          // ignore unreadable files
        }
      }
    }
  }

  getRamLayer(): MemoryFile | undefined {
    return Array.from(this.files.values()).find((f) => f.frontmatter.tier === "ram");
  }

  getHotTiers(): MemoryFile[] {
    return Array.from(this.files.values()).filter((f) => f.frontmatter.tier === "hot");
  }

  getWarmTiers(): MemoryFile[] {
    return Array.from(this.files.values()).filter((f) => f.frontmatter.tier === "warm");
  }

  getByName(name: string): MemoryFile | undefined {
    // Try exact match first, then fuzzy
    const exact = Array.from(this.files.values()).find((f) => f.name === name);
    if (exact) return exact;
    return Array.from(this.files.values()).find((f) =>
      f.name.toLowerCase().includes(name.toLowerCase())
    );
  }

  async loadFile(file: MemoryFile): Promise<string> {
    return fs.promises.readFile(file.filePath, "utf-8");
  }

  async appendToMemories(entry: string, tags?: string[]): Promise<void> {
    // Find existing memories.md anywhere in workspace
    const memories = this.getByName("memories");
    let memoriesPath: string;
    if (memories) {
      memoriesPath = memories.filePath;
    } else {
      memoriesPath = path.join(this.workspacePath, "memories.md");
    }
    const timestamp = new Date().toISOString().split("T")[0];
    const tagStr = tags ? ` tags=[${tags.join(",")}]` : "";
    const entryText = `\n## ${timestamp}${tagStr}\n- ${entry}\n`;
    await fs.promises.appendFile(memoriesPath, entryText);
  }

  async updateCache(content: string): Promise<void> {
    const cache = this.getRamLayer();
    let cachePath: string;
    if (cache) {
      cachePath = cache.filePath;
    } else {
      cachePath = path.join(this.workspacePath, "session-cache.md");
    }
    await fs.promises.writeFile(cachePath, content);
  }

  search(query: string): MemoryFile[] {
    const q = query.toLowerCase();
    return Array.from(this.files.values()).filter(
      (f) => f.name.toLowerCase().includes(q) || f.body.toLowerCase().includes(q)
    );
  }
}

function parseFrontmatter(content: string): { frontmatter: Frontmatter; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---\n?/);
  if (match) {
    try {
      const frontmatter = parseYamlLike(match[1]) as Frontmatter;
      const body = content.slice(match[0].length);
      return { frontmatter, body };
    } catch {
      return { frontmatter: {}, body: content };
    }
  }
  return { frontmatter: {}, body: content };
}

function parseYamlLike(text: string): Record<string, any> {
  const result: Record<string, any> = {};
  for (const line of text.split("\n")) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    if (!key) continue;

    if (value.startsWith("[") && value.endsWith("]")) {
      result[key] = value
        .slice(1, -1)
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
    } else if (value === "true") {
      result[key] = true;
    } else if (value === "false") {
      result[key] = false;
    } else if (/^\d+$/.test(value)) {
      result[key] = parseInt(value, 10);
    } else {
      result[key] = value;
    }
  }
  return result;
}

export default function tieredMemoryExtension(agent: ExtensionAPI) {
  let memorySystem: TieredMemorySystem | null = null;

  agent.on("session_start", async (event, ctx) => {
    // Prevent bloat: only inject full memory files on cold starts.
    if (event.reason === "reload" || event.reason === "resume" || event.reason === "fork") {
      ctx.ui.notify("[TieredMemory] Skipped auto-inject on " + event.reason, "info");
      return;
    }

    const workspacePath = ctx.workspace.path;
    memorySystem = new TieredMemorySystem(workspacePath);
    await memorySystem.scan();

    console.log("[TieredMemory] Scanning workspace:", workspacePath);

    // Layer 0: RAM - Session Cache
    const ram = memorySystem.getRamLayer();
    if (ram) {
      const content = await memorySystem.loadFile(ram);
      ctx.ui.notify(`RAM Layer Loaded: ${ram.name}`, "info");
      agent.sendMessage(
        {
          customType: "tiered-memory-ram",
          content: `## 🔴 RAM Layer Loaded: ${ram.name}\n${content}`,
          display: false,
        },
        { deliverAs: "nextTurn" }
      );
    }

    // Layer 1: ROM Hot Tier
    const hot = memorySystem.getHotTiers();
    for (const file of hot) {
      const content = await memorySystem.loadFile(file);
      agent.sendMessage(
        {
          customType: "tiered-memory-hot",
          content: `## 🟢 ROM Hot: ${file.name}\n${content}`,
          display: false,
        },
        { deliverAs: "nextTurn" }
      );
    }

    // Show available warm tiers
    const warm = memorySystem.getWarmTiers();
    if (warm.length > 0) {
      const warmList = warm.map((f) => `/load ${f.name}`).join(", ");
      agent.sendMessage(
        {
          customType: "tiered-memory-warm",
          content: `## 🟡 Warm tiers available: ${warmList}`,
          display: false,
        },
        { deliverAs: "nextTurn" }
      );
    }

    console.log("[TieredMemory] Boot complete. 🐻 Orinoco approves!");
  });

  agent.registerCommand("cache", {
    description: "Load session cache (RAM layer)",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      const ram = memorySystem.getRamLayer();
      if (!ram) {
        ctx.ui.notify("No RAM layer (session-cache.md) found", "warning");
        return;
      }
      const content = await memorySystem.loadFile(ram);
      agent.sendMessage(
        { customType: "tiered-memory-cache", content: `## 🔴 Session Cache\n\n${content}`, display: true },
        { deliverAs: "nextTurn" }
      );
    },
  });

  agent.registerCommand("remember", {
    description: "Add entry to memories.md",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      const entry = args;
      if (!entry) {
        ctx.ui.notify("Usage: /remember <text>", "info");
        return;
      }
      await memorySystem.appendToMemories(entry);
      ctx.ui.notify("Added to memories.md", "info");
    },
  });

  agent.registerCommand("load", {
    description: "Load warm tier file",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      const name = args.split(" ")[0];
      if (!name) {
        ctx.ui.notify("Usage: /load <name>", "info");
        return;
      }
      const file = memorySystem.getByName(name);
      if (!file) {
        ctx.ui.notify(`File not found: ${name}`, "warning");
        return;
      }
      const content = await memorySystem.loadFile(file);
      agent.sendMessage(
        { customType: "tiered-memory-load", content: `## 🟡 ${file.name}\n\n${content}`, display: true },
        { deliverAs: "nextTurn" }
      );
    },
  });

  agent.registerCommand("search", {
    description: "Search all workspace files",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      if (!args) {
        ctx.ui.notify("Usage: /search <query>", "info");
        return;
      }
      const results = memorySystem.search(args);
      if (results.length === 0) {
        ctx.ui.notify("No matches found.", "info");
        return;
      }
      const list = results.map((f) => `- **${f.name}** (${f.frontmatter.tier || "untiered"})`).join("\n");
      agent.sendMessage(
        { customType: "tiered-memory-search", content: `## 🔍 Search Results\n\n${list}`, display: true },
        { deliverAs: "nextTurn" }
      );
    },
  });

  agent.registerCommand("test", {
    description: "Verify tiered memory extension is loaded",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      const ram = memorySystem.getRamLayer();
      const hot = memorySystem.getHotTiers();
      const warm = memorySystem.getWarmTiers();
      const status = `Tiered Memory loaded — RAM: ${ram ? ram.name : "none"} | HOT: ${hot.map((f) => f.name).join(", ") || "none"} | WARM: ${warm.map((f) => f.name).join(", ") || "none"}`;
      ctx.ui.notify(status, "info");
    },
  });

  agent.registerCommand("cache-update", {
    description: "Update session cache with current state",
    handler: async (args, ctx) => {
      if (!memorySystem) {
        ctx.ui.notify("Memory system not initialized", "error");
        return;
      }
      const content = args || "Updated session cache";
      const timestamp = new Date().toISOString();
      const cacheContent = `---\ntier: ram\ncreated: ${timestamp}\n---\n\n${content}`;
      await memorySystem.updateCache(cacheContent);
      ctx.ui.notify(`Session cache updated at ${timestamp}`, "info");
    },
  });
}
