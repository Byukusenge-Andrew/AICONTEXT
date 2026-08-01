# AIContext - Persistent Codebase Context, Change Tracker & Connection Graph Engine

**AIContext** is a lightweight, universal context engine designed for AI coding assistants in **Antigravity**, **Cursor**, **VS Code**, **Claude Code**, or **Windsurf**.

It eliminates the overhead of LLMs re-reading entire codebases on every turn by maintaining an incremental cached index of symbols, file architecture, git deltas, **dependency connection graphs**, and **exact $N$-hop neighborhood context extraction**.

---

## 🚀 Key Features

* **Zero-Config Global MCP Integration**: Works across any project automatically without hardcoding absolute paths.
* **Exact $N$-Hop Graph Scoping**: Uses deterministic BFS graph radius traversal ($R$-hop adjacency) to deliver strictly relevant dependent files without risking missed context.
* **Tiered Context Delivery**:
  * **Tier 1 (Global)**: High-level module index & architectural summary (`SUMMARY.md`).
  * **Tier 2 (Neighborhood)**: $R$-hop dependency graph radius around target/modified files.
  * **Tier 3 (Focus)**: Line-level AST symbol signatures and docstrings for targeted files.
* **$\mathcal{O}(1)$ HashMap Import Resolution**: Instant module lookup dictionary mapping imports to workspace files.
* **Incremental SHA-256 Caching**: Parses only modified/added files, keeping context sync fast ($\sim 0$ LLM tokens burned).
* **Interactive 3D Browser Dashboard**: Renders project dependency graphs in a 3D WebGL Code Globe network visualizer.

> 📖 Read the detailed technical specification: [SPATIAL_AICONTEXT_SPEC.md](file:///d:/mytools/AICONTEXT/SPATIAL_AICONTEXT_SPEC.md)

---

## ⚡ Zero-Path Setup (Use in ANY Project)

You do **NOT** need to memorize paths or pass path arguments! Once installed globally, `aicontext` automatically detects whichever project folder you are currently in.

### Step 1: Install Globally Once

Run the global installer script (Windows):

```cmd
install_global.bat
```
*(Automatically configures pip installation and updates your User PATH).*

### Step 2: Use in ANY Project

Open **ANY project directory** in your terminal or IDE, and simply type:

```bash
# In your project folder:
aicontext init
```

*(Note: If `aicontext` command is not recognized in an active terminal before restarting, use `py -m aicontext.cli init`)*

That's it! `aicontext` automatically creates `.aicontext/` in that project directory and injects context rules into `AGENTS.md`.

---

## 🔌 Universal Global MCP Setup for Antigravity / Cursor / VS Code

To make AIContext work automatically in **every new project** you open in Antigravity or Cursor without typing anything:

Add this single configuration to your global MCP settings (`mcpServers`):

```json
{
  "mcpServers": {
    "aicontext": {
      "command": "aicontext",
      "args": ["mcp"],
      "disabled": false
    }
  }
}
```

> **Why this works seamlessly everywhere**: When `aicontext mcp` runs without arguments, it automatically detects the current working directory of whatever project is currently open in your IDE!

---

## 🚀 Everyday Commands in Any Project

- **Initialize & Sync Context**:
  ```bash
  aicontext init
  ```

- **Query Scoped $N$-Hop Neighborhood Context**:
  ```bash
  aicontext query --file <relative_path> --radius 2 --tier 2
  ```

- **Measure Token Savings Stats**:
  ```bash
  aicontext stats [--file <relative_path>]
  ```

- **Open Interactive 3D WebGL Browser Visualizer**:
  ```bash
  aicontext visualize
  ```

- **Output Low-Token Chat Bootstrap Prompt**:
  ```bash
  aicontext bootstrap
  ```

- **Watch File Edits in Real-Time**:
  ```bash
  aicontext watch
  ```

---

## 📁 Artifacts Generated in `.aicontext/`

- `.aicontext/SUMMARY.md`: Token-optimized codebase index, symbols, and imports map.
- `.aicontext/recent_changes.md`: Delta summary of added/modified files and impact radius analysis.
- `.aicontext/graph.mmd`: Dependency connection graph in Mermaid format.
- `.aicontext/index.html`: Interactive 3D WebGL Code Globe dashboard.
- `.aicontext/prompt.txt`: Copy-pasteable session bootstrap prompt for new AI chats.
