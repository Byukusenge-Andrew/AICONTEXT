# AIContext - Recent Architectural & Security Changes

This document provides a comprehensive summary of all major enhancements, security features, configuration options, and multi-language documentation capabilities recently added to **AIContext**.

---

## 🔒 1. Advanced Security & Obfuscation System

### Multi-Target Ignore Auto-Protection
AIContext automatically detects present container, package, and deployment ignore files in your workspace root and ensures `.aicontext/` is protected against accidental commits or pushes:
- `.gitignore` (Git)
- `.dockerignore` (Docker)
- `.helmignore` (Kubernetes Helm)
- `.npmignore` (npm packages)
- `.gcloudignore` (Google Cloud)
- `.vercelignore` (Vercel)

### Secret Redaction Engine (`aicontext/security.py`)
Automatically sanitizes hardcoded secrets, API keys, and connection strings from docstrings, symbol details, and public payloads before writing to `.aicontext/`:
- **OpenAI / Anthropic Keys**: `sk-proj-...` / `sk-...` $\rightarrow$ `[REDACTED_OPENAI_KEY]` / `[REDACTED_API_KEY]`
- **AWS Credentials**: `AKIA...` $\rightarrow$ `[REDACTED_AWS_KEY]`
- **GitHub Tokens**: `ghp_...` / `gho_...` $\rightarrow$ `[REDACTED_GITHUB_TOKEN]`
- **Database Connection URIs**: `postgres://...`, `mongodb://...`, `mysql://...` $\rightarrow$ `[REDACTED_CONNECTION_STRING]`

### Sensitive File Exclusions
Files matching patterns like `.env*`, `*.pem`, `*.key`, `*.pfx`, `credentials.json`, `secrets.json`, `secrets.yaml` are completely excluded from AST parsing and index tracking.

### Identifier Obfuscation (`aicontext sync --obscure`)
Masks file paths and symbol names using keyed SHA-256 digests (`obs_a1b2c3d4`), concealing internal codebase structure in cached files.

### OS Stealth Mode
Conceals the `.aicontext/` directory on Windows using system hidden attributes (`attrib +h`), keeping it invisible to third-party directory scanners.

### Zero-Trace Workspace Purge (`aicontext purge`)
Wipes `.aicontext/`, uninstalls git hooks, and strips injected AI rules from `AGENTS.md` and `.cursorrules` cleanly with zero trace.

---

## ⚙️ 2. Per-Project Custom Configuration (`.aicontext.json`)

Repositories can now define a `.aicontext.json` file in the project root to customize security rules, sensitive files, and extra ignore targets:

```json
{
  "sensitive_patterns": [
    "custom_secret.txt",
    "config/keys/*"
  ],
  "ignore_targets": [
    ".customignore",
    ".dockerignore"
  ],
  "custom_ignore_patterns": [
    "build/",
    "temp_logs/"
  ]
}
```

---

## 💡 3. Universal Multi-Language Docstrings & Explanations

### Universal Docstring Extraction Engine (`aicontext/parser.py`)
Extracts top-level module explanations and symbol documentation across **any programming language**:
- **Python (`.py`)**: Top-level module docstrings (`""" ... """` / `''' ... '''`).
- **C-Style Languages (`.js`, `.ts`, `.go`, `.java`, `.c`, `.cpp`, `.cs`, `.rs`, `.kt`, `.swift`, `.php`)**: JSDoc block comments (`/** ... */`) and double-slash comments (`// ...`).
- **Hash/Script Languages (`.sh`, `.bash`, `.rb`, `.py`, `.yaml`, `.toml`)**: Header line comments (`# ...`).
- **Markup & Styling (`.html`, `.xml`)**: Top-level block comments (`<!-- ... -->`).
- **Markdown (`.md`)**: Top headers and overview blockquotes (`# ...` / `> ...`).

### Context & Visualization Integration
- **Context Summaries (`SUMMARY.md`)**: Displays `> *Description: ...*` for each file.
- **3D Code Globe Tooltips**: Hovering over file nodes in the 3D globe displays rich HTML tooltips with file summaries.
- **Codebase & Symbols Tab**: Displays cyan explanation cards (`💡 ...`) under file headers in the dashboard.

---

## 📊 4. 2D Diagram Rendering Optimization

Fixed a browser DOM layout issue where 2D Mermaid SVG diagrams failed to render when initialized inside hidden container tabs (`display: none`). Mermaid rendering is now lazy-triggered when switching to the 2D Diagram Graph tab (`switchTab('graph')`).

---

## 🧪 5. Automated Verification

All 10 unit tests in `tests/test_aicontext.py` pass cleanly, validating:
- Config initialization & stealth mode
- Incremental hash caching & delta tracking
- Multi-language symbol & docstring extraction
- Dependency connection graph & BFS impact radius
- Multi-target ignore auto-injection & secret redaction
- Salted identifier obfuscation & zero-trace purge
- `.aicontext.json` per-project configuration
