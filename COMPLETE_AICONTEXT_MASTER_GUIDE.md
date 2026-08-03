# AIContext - Complete Master Guide & Technical Documentation

Welcome to the **Master Guide for AIContext**. This document is an exhaustive manual covering every feature, command, architecture component, security protocol, configuration schema, and developer extension pattern in the **AIContext** ecosystem.

---

## 📋 Table of Contents
1. [Executive Overview & Core Value Proposition](#1-executive-overview--core-value-proposition)
2. [Installation & Environment Setup](#2-installation--environment-setup)
3. [Complete CLI Command Reference](#3-complete-cli-command-reference)
4. [MCP Server & IDE Integration](#4-mcp-server--ide-integration)
5. [Security & Anti-Leakage System](#5-security--anti-leakage-system)
6. [Per-Project Custom Configuration (`.aicontext.json`)](#6-per-project-custom-configuration-aicontextjson)
7. [Universal Multi-Language AST & Docstring Engine](#7-universal-multi-language-ast--docstring-engine)
8. [Interactive 3D WebGL & 2D Visualizer Dashboard](#8-interactive-3d-webgl--2d-visualizer-dashboard)
9. [Algorithmic Complexity & Graph Analysis](#9-algorithmic-complexity--graph-analysis)
10. [Developer Extension & Offline Modification Guide](#10-developer-extension--offline-modification-guide)

---

## 1. Executive Overview & Core Value Proposition

When AI coding assistants (Antigravity, Cursor, Claude Code, GitHub Copilot) work on large codebases, they traditionally re-read entire repository source files on every turn. This burns tens of thousands of tokens per prompt, costs money, and causes LLMs to lose context.

### What AIContext Does
- **Zero-Token Local Indexing**: Scans and parses your codebase 100% locally on CPU using AST parsing and SHA-256 hash tracking. **0 LLM API tokens burned for indexing.**
- **$\mathcal{O}(1)$ HashMap Import Resolution**: Maps dot notation (`aicontext.tracker`), POSIX paths, and module stems directly to exact file paths in near-constant time.
- **$N$-Hop BFS Neighborhood Context**: Replaces indiscriminate full-codebase scans with exact topological neighborhood extraction extending $N$ hops upstream (dependents) and downstream (dependencies).
- **Tiered Context Payloads**: Serves Tier 1 (Global Map), Tier 2 (Neighborhood Map), or Tier 3 (Focus File Map) depending on the AI's task.
- **Enterprise Anti-Leakage Security**: Prevents secret leaks across `.gitignore`, `.dockerignore`, `.helmignore`, `.npmignore`, `.gcloudignore`, `.vercelignore`, redacting credentials with regex AST filters.
- **3D WebGL Code Globe**: Visualizes your entire codebase architecture in an interactive 3D particle sphere in your browser.

---

## 2. Installation & Environment Setup

### Method A: Automated Installation Script (Windows)
Run `install_global.bat` from the repository root:
```cmd
install_global.bat
```
This batch script automatically detects python/py launcher, installs the package globally, configures your User PATH (`%APPDATA%\Python\Python314\Scripts`), and builds local binaries.

### Method B: Manual Pip Installation
```bash
# Clone repository
git clone https://github.com/Byukusenge-Andrew/AICONTEXT.git
cd AICONTEXT

# Install in editable mode
pip install -e .
```

### Method C: Offline Virtual Environment Execution
If working in an air-gapped or offline environment:
```powershell
.\.venv\Scripts\python.exe -m aicontext.cli init
```

---

## 3. Complete CLI Command Reference

All commands can be invoked via `aicontext <command>` or `python -m aicontext.cli <command>`.

### `aicontext init`
Initializes `.aicontext/` in the workspace root, installs AI instruction rules in `AGENTS.md` & `.cursorrules`, configures Git security hooks, and performs an initial workspace sync.
```bash
aicontext init [--path .]
```

### `aicontext sync`
Incrementally scans the codebase, computes file SHA-256 deltas, updates AST symbol tables, rebuilds dependency graphs, and refreshes `.aicontext/SUMMARY.md` & `.aicontext/index.html`.
```bash
aicontext sync [--path .] [--obscure]
```
- `--obscure`: Enables salted SHA-256 identifier obfuscation (`obs_a1b2c3d4`) for symbol names and file paths in cached files.

### `aicontext query`
Performs an $N$-hop BFS graph neighborhood query for target file(s) and returns a scoped, tiered context payload for AI consumption.
```bash
aicontext query -f aicontext/cli.py -r 2 -t 2
```
- `-f, --file`: Target relative file path(s).
- `-r, --radius`: BFS hop depth radius (default: `2`).
- `-t, --tier`: Context tier (1 = Global, 2 = Neighborhood, 3 = Focus).

### `aicontext stats`
Scans live workspace files and calculates real-time token savings achieved by AIContext using `tiktoken` BPE (or character ratio fallback).
```bash
aicontext stats [--file aicontext/cli.py]
```

### `aicontext audit`
Runs a security audit inspecting status across `.gitignore`, `.dockerignore`, `.helmignore`, `.npmignore`, `.gcloudignore`, `.vercelignore`, and verifying Git pre-commit security gates.
```bash
aicontext audit
```

### `aicontext purge`
Securely purges `.aicontext/`, uninstalls Git hooks, and strips injected rules from `AGENTS.md` and `.cursorrules` with zero trace left behind.
```bash
aicontext purge
```

### `aicontext visualize` (alias: `aicontext ui`)
Launches a local HTTP server and opens the 3D WebGL Code Globe and 2D Mermaid diagram visualizer dashboard in your default browser.
```bash
aicontext visualize [--port 8080]
```

### `aicontext bootstrap`
Outputs an ultra-compact Persistent Context Bootstrap prompt ready for pasting into new chat sessions.
```bash
aicontext bootstrap
```

### `aicontext watch`
Runs a real-time background file system watcher that automatically re-syncs context caches whenever files are saved or created.
```bash
aicontext watch
```

### `aicontext mcp`
Launches the Model Context Protocol (MCP) server over standard I/O for IDE integrations.
```bash
aicontext mcp
```

---

## 4. MCP Server & IDE Integration

AIContext includes native Model Context Protocol (MCP) server support via FastMCP.

### Registering with Antigravity / Cursor / Claude Desktop
Add the following to your MCP configuration file (`mcp.json` / `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "aicontext": {
      "command": "python",
      "args": ["-m", "aicontext.cli", "mcp"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Exposed MCP Tools
1. `get_neighborhood_context(file_path: str, radius: int = 2, tier: int = 2)`: Returns scoped $N$-hop neighborhood context payload.
2. `get_summary()`: Returns entire codebase architecture summary map.
3. `get_changes()`: Returns recent file changes and impact radius.
4. `audit_security()`: Returns workspace security audit report.

---

## 5. Security & Anti-Leakage System

AIContext incorporates multi-layer security to ensure context files, secrets, and private credentials never leak:

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY GUARD SYSTEM                    │
├──────────────────────────────┬──────────────────────────────┤
│ Multi-Target Ignore Auto-Inj │ Redacts .aicontext/ from     │
│                              │ .gitignore, .dockerignore,   │
│                              │ .helmignore, .npmignore, etc. │
├──────────────────────────────┼──────────────────────────────┤
│ Sensitive File Exclusions    │ Excludes .env*, *.pem, *.key,│
│                              │ credentials.json, secrets.*  │
├──────────────────────────────┼──────────────────────────────┤
│ AST Secret Redaction Engine  │ Masks sk-proj-*, AKIA*,      │
│                              │ ghp_*, postgres:// URIs      │
├──────────────────────────────┼──────────────────────────────┤
│ Identifier Obfuscation       │ Hashes paths & symbols as    │
│                              │ obs_a1b2c3d4                 │
├──────────────────────────────┼──────────────────────────────┤
│ OS Stealth Mode              │ Marks .aicontext/ hidden on  │
│                              │ Windows (attrib +h)          │
├──────────────────────────────┼──────────────────────────────┤
│ Zero-Trace Purge             │ Complete workspace reset     │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 6. Per-Project Custom Configuration (`.aicontext.json`)

To customize security, sensitive file patterns, or extra ignore targets for a specific repository, place a `.aicontext.json` file in your project root:

```json
{
  "sensitive_patterns": [
    "custom_secret.txt",
    "config/keys/*",
    "internal_credentials.json"
  ],
  "ignore_targets": [
    ".customignore",
    ".dockerignore",
    ".helmignore"
  ],
  "custom_ignore_patterns": [
    "build/",
    "temp_logs/",
    "*.bak"
  ]
}
```

---

## 7. Universal Multi-Language AST & Docstring Engine

The `SymbolExtractor` ([parser.py](file:///d:/mytools/AICONTEXT/aicontext/parser.py)) parses symbols, imports, and top-level file explanations across all programming languages:

```python
# Language Parser Support Matrix
Python (.py)         -> AST Tree Parsing + Module Docstrings
JavaScript/TS (.js)  -> Regex Import/Export + JSDoc Block Comments
C/C++/C# (.cpp, .cs) -> C-Style Comment Headers + Symbol Regex
Go / Rust (.go, .rs) -> Line Comments + Func/Struct Regex
HTML / XML (.html)   -> Comment Blocks (<!-- ... -->)
Markdown (.md)       -> Top Overview Headers & Blockquotes (# / >)
```

---

## 8. Interactive 3D WebGL & 2D Visualizer Dashboard

Running `aicontext visualize` opens `.aicontext/index.html`, an offline single-page visualizer powered by Three.js, `3d-force-graph`, and Mermaid:

- **🪐 3D Code Globe**: Renders file nodes as glowing spheres with dynamic particle flow representing import directions. Node tooltips display file explanations (`module_docstring`).
- **🌐 2D Diagram Graph**: Renders a clean Mermaid architecture diagram with lazy tab initialization.
- **🧩 Codebase & Symbols**: Filterable card view displaying indexed files, language types, file descriptions, and extracted class/function symbols.
- **⚡ Changes & Impact**: Displays recent file modifications and calculated downstream impact radius.

---

## 9. Algorithmic Complexity & Graph Analysis

AIContext uses exact dependency graph topological traversal:

### Time Complexity
- **Module Index Build**: $\mathcal{O}(V \cdot I + S)$ where $V$ is number of files, $I$ is imports per file, and $S$ is total AST symbols.
- **HashMap Symbol Resolution**: $\mathcal{O}(1)$ average lookup via `self.module_map`.
- **$N$-Hop Neighborhood Traversal**: $\mathcal{O}(M \cdot \Delta^d)$ BFS radius search where $M$ is target file set, $\Delta$ is average graph degree, and $d$ is depth radius.

### Space Complexity
- **Graph Adjacency Storage**: $\mathcal{O}(V + E + S)$ where $E$ is total import edges.

---

## 10. Developer Extension & Offline Modification Guide

To modify or extend AIContext offline:

1. **Source Code Structure**:
   - Entry & CLI: [`aicontext/cli.py`](file:///d:/mytools/AICONTEXT/aicontext/cli.py)
   - Configuration: [`aicontext/config.py`](file:///d:/mytools/AICONTEXT/aicontext/config.py)
   - AST Parser: [`aicontext/parser.py`](file:///d:/mytools/AICONTEXT/aicontext/parser.py)
   - Graph Engine: [`aicontext/graph.py`](file:///d:/mytools/AICONTEXT/aicontext/graph.py)
   - Security Guard: [`aicontext/security.py`](file:///d:/mytools/AICONTEXT/aicontext/security.py)
   - Change Tracker: [`aicontext/tracker.py`](file:///d:/mytools/AICONTEXT/aicontext/tracker.py)
   - Context Generator: [`aicontext/generator.py`](file:///d:/mytools/AICONTEXT/aicontext/generator.py)
   - Dashboard Visualizer: [`aicontext/visualizer.py`](file:///d:/mytools/AICONTEXT/aicontext/visualizer.py)
   - Test Suite: [`tests/test_aicontext.py`](file:///d:/mytools/AICONTEXT/tests/test_aicontext.py)

2. **Running Tests**:
   ```bash
   python -m pytest
   ```

3. **Self-Updating Context**:
   Whenever source code files are modified, run:
   ```bash
   python -m aicontext.cli sync
   ```
