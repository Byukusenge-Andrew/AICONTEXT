# AIContext - Offline Developer & Code Modification Guide

This guide is designed to help you **understand, navigate, modify, and extend the AIContext codebase 100% offline** without needing an active internet connection or external API calls.

---

## 🏛️ 1. High-Level System Architecture

AIContext operates completely locally on your CPU via zero-token AST parsing, SHA-256 hash delta tracking, and local graph algorithms.

```
                  ┌──────────────────────────────┐
                  │    CLI Entry / MCP Server    │
                  │ (cli.py / mcp_server.py)     │
                  └──────────────┬───────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
        ┌──────────────────┐        ┌──────────────────┐
        │ Incremental Delta│        │ Multi-Language   │
        │ Change Tracker   │        │ AST & Docstring  │
        │   (tracker.py)   │        │ Parser(parser.py)│
        └──────────┬───────┘        └──────────┬───────┘
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Security & Anti-Leakage  │
                    │ Guard (security.py)      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Connection Graph Engine  │
                    │       (graph.py)         │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Context Generator & UI   │
                    │ (generator.py /          │
                    │  visualizer.py)          │
                    └──────────────────────────┘
```

---

## 📁 2. Complete Module Map & Responsibilities

| File | Purpose / Responsibility | Primary Class or Functions |
| :--- | :--- | :--- |
| [`aicontext/cli.py`](file:///d:/mytools/AICONTEXT/aicontext/cli.py) | Command line interface router built with Click and Rich. | `init`, `sync`, `query`, `stats`, `audit`, `purge`, `visualize`, `mcp` |
| [`aicontext/config.py`](file:///d:/mytools/AICONTEXT/aicontext/config.py) | Configuration manager for paths, ignore patterns, and `.aicontext.json`. | `Config`, `load_project_config()`, `ensure_dir()` |
| [`aicontext/parser.py`](file:///d:/mytools/AICONTEXT/aicontext/parser.py) | Universal multi-language AST parser for symbols, imports, and top-level docstrings. | `SymbolExtractor`, `SymbolInfo`, `FileParseResult` |
| [`aicontext/tracker.py`](file:///d:/mytools/AICONTEXT/aicontext/tracker.py) | Incremental SHA-256 file hash tracking and git delta detector. | `ChangeTracker`, `FileState` |
| [`aicontext/graph.py`](file:///d:/mytools/AICONTEXT/aicontext/graph.py) | Graph engine supporting $\mathcal{O}(1)$ HashMap module lookup and $N$-hop BFS radius. | `ConnectionGraph`, `GraphNode` |
| [`aicontext/security.py`](file:///d:/mytools/AICONTEXT/aicontext/security.py) | Ignore auto-injection, AST secret redaction, identifier obfuscation, OS stealth mode, and purge. | `SecurityGuard` |
| [`aicontext/generator.py`](file:///d:/mytools/AICONTEXT/aicontext/generator.py) | Formats `.aicontext/SUMMARY.md`, `recent_changes.md`, bootstrap prompt, and tiered payloads. | `ContextGenerator` |
| [`aicontext/visualizer.py`](file:///d:/mytools/AICONTEXT/aicontext/visualizer.py) | Generates `.aicontext/index.html` interactive 3D WebGL Code Globe and 2D Mermaid UI. | `Visualizer` |
| [`aicontext/rules.py`](file:///d:/mytools/AICONTEXT/aicontext/rules.py) | Injector for AI instructions in `AGENTS.md` and `.cursorrules`. | `RuleInjector` |
| [`aicontext/hooks.py`](file:///d:/mytools/AICONTEXT/aicontext/hooks.py) | Git pre-commit, post-commit, and post-checkout hook installers. | `GitHookInstaller` |
| [`aicontext/mcp_server.py`](file:///d:/mytools/AICONTEXT/aicontext/mcp_server.py) | FastMCP server implementation for IDE context retrieval. | `run_mcp_server()` |

---

## 🛠️ 3. How to Run & Test Completely Offline

### 1. Setup Local Environment
If working offline without internet access, use the pre-configured local virtual environment:

```powershell
# Activate local virtual environment on Windows
.\.venv\Scripts\Activate.ps1

# Or run python directly
.\.venv\Scripts\python.exe -m aicontext.cli --help
```

### 2. Run Local Unit Test Suite
To verify all features work cleanly offline:

```bash
python -m pytest
```

### 3. Test CLI Commands Locally
```bash
# Sync context cache
python -m aicontext.cli sync

# Run $N$-hop neighborhood query
python -m aicontext.cli query -f aicontext/cli.py -r 2 -t 2

# Measure live token savings stats
python -m aicontext.cli stats

# Launch local browser visualization dashboard
python -m aicontext.cli visualize

# Run security audit
python -m aicontext.cli audit
```

---

## 💻 4. How to Modify & Extend the Codebase

### Recipe A: Adding a New Programming Language Parser
To support a new language (e.g. Go or Rust) in [`aicontext/parser.py`](file:///d:/mytools/AICONTEXT/aicontext/parser.py):

1. Add file extension mapping in `SymbolExtractor.detect_language`:
   ```python
   mapping = {
       ".go": "go",
       ".rs": "rust",
       # ...
   }
   ```
2. Add regex symbol parsing logic in `SymbolExtractor._parse_generic`:
   ```python
   # Detect Go functions: func FunctionName(args...)
   if lang == "go":
       fn_match = re.search(r'^func\s+([A-Za-z0-9_]+)', line_str)
       if fn_match:
           result.symbols.append(SymbolInfo(fn_match.group(1), "function", idx))
   ```

---

### Recipe B: Adding a New CLI Command
To add a new command (e.g. `aicontext export`) in [`aicontext/cli.py`](file:///d:/mytools/AICONTEXT/aicontext/cli.py):

```python
@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--output", "-o", default="context.json", help="Output file path.")
def export(path: str, output: str):
    """Exports indexed codebase context as a custom JSON file."""
    config = Config(path)
    tracker = ChangeTracker(config)
    cache, _, _, _ = tracker.scan_files()
    
    out_path = Path(output)
    out_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    console.print(f"[bold green]Exported context to {out_path.name}[/]")
```

---

### Recipe C: Adding Custom Secret Redaction Patterns
To catch custom API keys or company tokens in [`aicontext/security.py`](file:///d:/mytools/AICONTEXT/aicontext/security.py):

Add your regex tuple to `SECRET_REGEX_PATTERNS`:
```python
SECRET_REGEX_PATTERNS = [
    (r"mycompany_token_[a-zA-Z0-9]{32}", "[REDACTED_COMPANY_TOKEN]"),
    # ...
]
```

---

### Recipe D: Customizing the 3D WebGL Browser Dashboard
To tweak visual styles, colors, or node behavior in [`aicontext/visualizer.py`](file:///d:/mytools/AICONTEXT/aicontext/visualizer.py):

1. Edit CSS variables inside `HTML_TEMPLATE` (e.g. `--accent-cyan`, `--bg-dark`).
2. Edit Three.js 3D Force Graph properties inside `init3DGraph()`:
   ```javascript
   graph3dInstance = ForceGraph3D()(elem)
       .nodeRelSize(10) // Change node size
       .linkOpacity(0.6)  // Change line opacity
       .linkDirectionalParticles(5); // Adjust particle particle count
   ```

---

## 🔧 5. Troubleshooting & FAQs (Offline Mode)

- **PowerShell `aicontext : Command Not Found` Error**:
  Run via Python module directly: `python -m aicontext.cli sync` or add `%APPDATA%\Python\Python314\Scripts` to your User PATH.

- **PowerShell Encoding Error on Windows**:
  Run commands with UTF-8 encoding enabled:
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  python -m aicontext.cli sync
  ```

- **Resetting / Cleaning AIContext Artifacts**:
  Run `python -m aicontext.cli purge` to securely reset all local `.aicontext/` caches and rules cleanly.
