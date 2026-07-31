import json
from pathlib import Path
from typing import Dict, List
from .config import Config
from .tracker import FileState
from .parser import FileParseResult
from .graph import ConnectionGraph
from .visualizer import Visualizer

class ContextGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.prompt_file = self.config.aicontext_dir / "prompt.txt"

    def generate_all(
        self,
        current_cache: Dict[str, FileState],
        parse_results: Dict[str, FileParseResult],
        added: List[str],
        modified: List[str],
        deleted: List[str],
        git_status: dict,
        graph: ConnectionGraph,
    ):
        """Generates all context files in .aicontext/."""
        self.config.ensure_dir()

        # 1. Generate SUMMARY.md
        summary_md = self._build_summary_md(current_cache, parse_results, graph)
        with open(self.config.summary_file, "w", encoding="utf-8") as f:
            f.write(summary_md)

        # 2. Generate recent_changes.md
        changes_md = self._build_changes_md(added, modified, deleted, git_status, graph)
        with open(self.config.changes_file, "w", encoding="utf-8") as f:
            f.write(changes_md)

        # 3. Generate graph.mmd & graph.json
        mermaid_graph = graph.export_mermaid()
        with open(self.config.graph_file, "w", encoding="utf-8") as f:
            f.write(mermaid_graph)

        graph_data = {
            "nodes": {path: node.to_dict() for path, node in sorted(graph.nodes.items())}
        }
        with open(self.config.graph_json_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)

        # 4. Generate Interactive HTML Visualization Dashboard (.aicontext/index.html)
        visualizer = Visualizer(self.config)
        visualizer.write_dashboard(current_cache, parse_results, mermaid_graph, changes_md)

        # 5. Generate Ultra-Low-Token Session Bootstrap Prompt (.aicontext/prompt.txt)
        bootstrap_prompt = self._build_bootstrap_prompt(summary_md, changes_md)
        with open(self.prompt_file, "w", encoding="utf-8") as f:
            f.write(bootstrap_prompt)

    def generate_tiered_context(
        self,
        target_files: List[str],
        graph: ConnectionGraph,
        parse_results: Dict[str, FileParseResult],
        radius: int = 2,
        tier: int = 2,
    ) -> str:
        """Generates scoped, tiered context payload for AI assistants."""
        if tier == 1:
            if self.config.summary_file.exists():
                return self.config.summary_file.read_text(encoding="utf-8")
            return self._build_summary_md({}, parse_results, graph)
        
        neighborhood = graph.get_neighborhood(target_files, max_depth=radius)
        scoped_files = set(target_files)
        for target, deps in neighborhood.items():
            scoped_files.update(deps)

        lines = [
            f"# AIContext Tiered Payload (Tier {tier}, Radius={radius})",
            f"> Target files: {', '.join([f'`{f}`' for f in target_files])}",
            "",
            "## Scoped Neighborhood Files",
        ]

        for rel_path in sorted(scoped_files):
            res = parse_results.get(rel_path)
            lang = res.language if res else "file"
            is_target = rel_path in target_files
            tag = " [TARGET]" if is_target else " [NEIGHBOR]"
            
            lines.append(f"### `{rel_path}` ({lang}){tag}")
            if res and res.symbols:
                lines.append("**Symbols:**")
                sym_limit = None if (tier == 3 and is_target) else 10
                sym_list = res.symbols if sym_limit is None else res.symbols[:sym_limit]
                for sym in sym_list:
                    det = f" {sym.details}" if sym.details else ""
                    doc = f" - *{sym.docstring}*" if sym.docstring else ""
                    lines.append(f"- `{sym.kind}` **{sym.name}** (L{sym.line_no}){det}{doc}")
            
            if res and res.imports:
                lines.append(f"**Imports:** {', '.join([f'`{imp}`' for imp in res.imports])}")
            lines.append("")

        return "\n".join(lines)

    def _build_bootstrap_prompt(self, summary_md: str, changes_md: str) -> str:
        return f"""<AICONTEXT_PERSISTENT_CONTEXT>
The following is an ultra-compact, token-optimized context index and recent change log for this project.
Do not re-read unchanged codebase files unless requested.

--- CODEBASE SUMMARY ---
{summary_md}

--- RECENT CHANGES & IMPACT RADIUS ---
{changes_md}
</AICONTEXT_PERSISTENT_CONTEXT>"""

    def _build_summary_md(
        self,
        current_cache: Dict[str, FileState],
        parse_results: Dict[str, FileParseResult],
        graph: ConnectionGraph,
    ) -> str:
        lines = [
            "# Codebase Architecture & Context Summary",
            "> Generated automatically by AIContext. Token-optimized context map.",
            "",
            "## Workspace File Index & Symbols",
            "",
        ]

        for rel_path, state in sorted(current_cache.items()):
            res = parse_results.get(rel_path)
            lang = res.language if res else "file"
            
            lines.append(f"### `{rel_path}` ({lang}, {state.size} bytes)")
            
            if res and res.symbols:
                lines.append("**Key Symbols:**")
                for sym in res.symbols[:10]:
                    det = f" {sym.details}" if sym.details else ""
                    doc = f" - *{sym.docstring}*" if sym.docstring else ""
                    lines.append(f"- `{sym.kind}` **{sym.name}** (L{sym.line_no}){det}{doc}")
                if len(res.symbols) > 10:
                    lines.append(f"- *... and {len(res.symbols) - 10} more symbols*")

            if res and res.imports:
                lines.append(f"**Imports:** {', '.join([f'`{imp}`' for imp in res.imports[:6]])}")

            lines.append("")

        lines.append("## Dependency Connection Graph (Mermaid)")
        lines.append("```mermaid")
        lines.append(graph.export_mermaid())
        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def _build_changes_md(
        self,
        added: List[str],
        modified: List[str],
        deleted: List[str],
        git_status: dict,
        graph: ConnectionGraph,
    ) -> str:
        lines = [
            "# Recent Code Changes & Impact Radius",
            "> Tracks recent modifications so AI does not need to re-read unchanged code.",
            "",
        ]

        if not added and not modified and not deleted and not git_status.get("unstaged"):
            lines.append("✅ **No uncommitted file changes detected.**")
            lines.append("")
        else:
            if added:
                lines.append("### ➕ Added Files")
                for f in added:
                    lines.append(f"- `{f}`")
                lines.append("")

            if modified:
                lines.append("### ✏️ Modified Files")
                for f in modified:
                    lines.append(f"- `{f}`")
                lines.append("")

            if deleted:
                lines.append("### ❌ Deleted Files")
                for f in deleted:
                    lines.append(f"- `{f}`")
                lines.append("")

        # Impact Radius Analysis
        all_changed = list(set(added + modified + git_status.get("unstaged", []) + git_status.get("staged", [])))
        if all_changed:
            impact_map = graph.get_impact_radius(all_changed, max_depth=2)
            lines.append("### 🎯 Impact Radius (Affected Dependent Files)")
            has_impact = False
            for mod_file, dependents in impact_map.items():
                if dependents:
                    has_impact = True
                    lines.append(f"- Modifying `{mod_file}` impacts:")
                    for dep in dependents:
                        lines.append(f"  - `{dep}`")
            if not has_impact:
                lines.append("No downstream dependent files impacted.")
            lines.append("")

        if git_status.get("recent_commits"):
            lines.append("### 📜 Recent Git Commits")
            for c in git_status["recent_commits"]:
                lines.append(f"- {c}")
            lines.append("")

        return "\n".join(lines)
