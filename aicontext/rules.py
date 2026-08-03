"""
AIContext Rule Injector - Configures and appends AI context instruction rules into AGENTS.md and .cursorrules.
"""
from pathlib import Path
from typing import List
from .config import Config

AI_RULES_CONTENT = """# AI Context & Change Tracking Instructions

> [!IMPORTANT]
> **Token Preservation Rule**: Do NOT re-read or scan entire codebase source files indiscriminately.
> Instead, read `.aicontext/SUMMARY.md` for complete codebase architecture, symbol maps, and connection graphs.

## Instructions for AI Assistant

1. **Context & Architecture Discovery**:
   - Read `.aicontext/SUMMARY.md` to understand all available modules, classes, functions, and import relationships in ~2,000 tokens.
   - Inspect `.aicontext/recent_changes.md` to see recent modifications and impact radius.

2. **Self-Updating Context (0 LLM Tokens Burned)**:
   - Whenever you create, modify, or delete files in this project, execute `aicontext sync` (or invoke the `sync_context` MCP tool).
   - *Note: `aicontext sync` executes 100% locally on CPU via fast AST/hash parsing. It uses 0 LLM API tokens.*

3. **Impact Radius Verification**:
   - Before suggesting edits to shared modules, check `.aicontext/recent_changes.md` or use `get_impact_radius` to verify which downstream dependent files are affected.
"""

class RuleInjector:
    def __init__(self, config: Config):
        self.config = config

    def inject_rules(self) -> List[str]:
        """
        Injects AI instruction rules into target workspace:
        - AGENTS.md
        - .cursorrules
        - .aicontext/rules.md
        """
        updated_files = []
        root = self.config.root_dir

        # 1. .aicontext/rules.md
        rule_md = self.config.aicontext_dir / "rules.md"
        rule_md.write_text(AI_RULES_CONTENT, encoding="utf-8")
        updated_files.append(str(rule_md.relative_to(root)))

        # 2. AGENTS.md (Antigravity & Universal Agents)
        agents_md = root / "AGENTS.md"
        self._append_rule_if_missing(agents_md, AI_RULES_CONTENT)
        updated_files.append("AGENTS.md")

        # 3. .cursorrules (Cursor & Windsurf IDEs)
        cursor_rules = root / ".cursorrules"
        self._append_rule_if_missing(cursor_rules, AI_RULES_CONTENT)
        updated_files.append(".cursorrules")

        return updated_files

    def _append_rule_if_missing(self, target_file: Path, content: str):
        marker = "AI Context & Change Tracking Instructions"
        if target_file.exists():
            existing = target_file.read_text(encoding="utf-8", errors="ignore")
            if marker in existing:
                return  # already present
            new_text = existing.rstrip() + "\n\n" + content
        else:
            new_text = content

        target_file.write_text(new_text, encoding="utf-8")
