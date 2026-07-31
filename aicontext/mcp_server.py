import asyncio
import json
from pathlib import Path
from typing import List, Optional

try:
    from mcp.server.fastmcp import FastMCP
    mcp_available = True
except ImportError:
    mcp_available = False

from .config import Config
from .tracker import ChangeTracker
from .parser import SymbolExtractor
from .graph import ConnectionGraph
from .generator import ContextGenerator

def create_mcp_server(root_dir: str = "."):
    if not mcp_available:
        raise RuntimeError("The 'mcp' package is required to run the MCP server. Install with `pip install mcp`.")

    config = Config(root_dir)
    mcp = FastMCP("AIContext - Codebase Context & Change Tracker")

    def _sync():
        tracker = ChangeTracker(config)
        extractor = SymbolExtractor()
        current_cache, added, modified, deleted = tracker.scan_files()
        
        parse_results = {}
        for rel_path in current_cache:
            full_path = config.root_dir / rel_path
            parse_results[rel_path] = extractor.parse_file(full_path, rel_path)

        graph = ConnectionGraph(config.root_dir)
        graph.build_graph(parse_results)

        git_status = tracker.get_git_status()
        generator = ContextGenerator(config)
        generator.generate_all(current_cache, parse_results, added, modified, deleted, git_status, graph)
        tracker.save_cache(current_cache)

        return config, current_cache, parse_results, graph

    @mcp.tool()
    def get_codebase_summary() -> str:
        """Returns the high-level codebase architecture summary, symbols, and token-optimized map."""
        if not config.summary_file.exists():
            _sync()
        return config.summary_file.read_text(encoding="utf-8")

    @mcp.tool()
    def get_recent_changes() -> str:
        """Returns recent uncommitted changes, modified files, and impact radius analysis."""
        _sync()
        if config.changes_file.exists():
            return config.changes_file.read_text(encoding="utf-8")
        return "No change tracking data available."

    @mcp.tool()
    def get_connection_graph(format: str = "mermaid") -> str:
        """Returns the codebase dependency connection graph (format: 'mermaid' or 'json')."""
        _sync()
        if format == "json" and config.graph_json_file.exists():
            return config.graph_json_file.read_text(encoding="utf-8")
        if config.graph_file.exists():
            return config.graph_file.read_text(encoding="utf-8")
        return "No graph available."

    @mcp.tool()
    def get_impact_radius(files: List[str]) -> str:
        """Calculates which dependent files in the codebase will be impacted if the given files are modified."""
        cfg, current_cache, parse_results, graph = _sync()
        impact = graph.get_impact_radius(files, max_depth=3)
        return json.dumps(impact, indent=2)

    @mcp.tool()
    def search_symbols(query: str) -> str:
        """Searches for matching symbols (classes, functions, methods) across the workspace codebase."""
        cfg, current_cache, parse_results, graph = _sync()
        matches = []
        query_lower = query.lower()

        for rel_path, parse_res in parse_results.items():
            for sym in parse_res.symbols:
                if query_lower in sym.name.lower() or query_lower in sym.kind.lower():
                    matches.append({
                        "file": rel_path,
                        "symbol": sym.name,
                        "kind": sym.kind,
                        "line": sym.line_no,
                        "details": sym.details,
                    })

        return json.dumps(matches[:30], indent=2)

    @mcp.tool()
    def get_neighborhood_context(target_files: List[str], radius: int = 2, tier: int = 2) -> str:
        """Returns N-hop neighborhood context payload (Radius R, Tier 1..3) for target files."""
        cfg, current_cache, parse_results, graph = _sync()
        generator = ContextGenerator(config)
        return generator.generate_tiered_context(target_files, graph, parse_results, radius=radius, tier=tier)

    @mcp.tool()
    def sync_context() -> str:
        """Forces an immediate incremental re-indexing of the workspace context and dependency graph."""
        _sync()
        return "✅ AIContext index, dependency graph, and recent changes successfully synced."

    return mcp

def run_mcp_server(root_dir: str = "."):
    mcp_app = create_mcp_server(root_dir)
    mcp_app.run()
