# AIContext - Persistent Codebase Context, Change Tracker & Connection Graph Engine

**AIContext** is a lightweight, universal context engine designed for AI coding assistants in **Antigravity**, **Cursor**, **VS Code**, **Claude Code**, or **Windsurf**.

It eliminates the overhead of LLMs re-reading entire codebases on every turn by maintaining an incremental cached index of symbols, file architecture, git deltas, and **dependency connection graphs**.

---

## ⚡ Zero-Path Setup (Use in ANY Project)

You do **NOT** need to memorize paths or pass path arguments! Once installed globally, `aicontext` automatically detects whichever project folder you are currently in.

### Step 1: Install Globally Once

Run this command once in your terminal:

```bash
pip install --user -e d:\mytools\AICONTEXT
```
*(Or double-click `d:\mytools\AICONTEXT\install_global.bat`)*

### Step 2: Use in ANY Project

Open **ANY project directory** in your terminal or IDE, and simply type:

```bash
# In your new project folder:
aicontext init
```

That's it! `aicontext` automatically creates `.aicontext/` in that project directory.

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

- **Open Interactive Browser Visualizer**:
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
- `.aicontext/index.html`: Interactive browser dashboard.
- `.aicontext/prompt.txt`: Copy-pasteable session bootstrap prompt for new AI chats.
