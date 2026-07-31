import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from .parser import FileParseResult

class GraphNode:
    def __init__(self, rel_path: str, language: str):
        self.rel_path = rel_path
        self.language = language
        self.imports_files: Set[str] = set()    # files this file imports (outgoing edges)
        self.imported_by: Set[str] = set()     # files that import this file (incoming edges)
        self.symbols: List[str] = []

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "language": self.language,
            "imports": sorted(list(self.imports_files)),
            "imported_by": sorted(list(self.imported_by)),
            "symbols": self.symbols,
        }

class ConnectionGraph:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.nodes: Dict[str, GraphNode] = {}

    def build_graph(self, parse_results: Dict[str, FileParseResult]):
        """Builds directed dependency graph from parse results."""
        self.nodes.clear()

        # Step 1: Initialize nodes
        for rel_path, res in parse_results.items():
            node = GraphNode(rel_path, res.language)
            node.symbols = [s.name for s in res.symbols]
            self.nodes[rel_path] = node

        # Step 2: Resolve edges
        all_rel_paths = list(self.nodes.keys())
        
        for rel_path, res in parse_results.items():
            source_node = self.nodes[rel_path]
            source_dir = Path(rel_path).parent

            for imp in res.imports:
                target_path = self._resolve_import(imp, source_dir, all_rel_paths)
                if target_path and target_path in self.nodes and target_path != rel_path:
                    source_node.imports_files.add(target_path)
                    self.nodes[target_path].imported_by.add(rel_path)

    def _resolve_import(self, import_str: str, source_dir: Path, all_paths: List[str]) -> Optional[str]:
        """Resolves an import string (e.g., '.config', 'aicontext.tracker', './utils') to workspace rel_path."""
        import_clean = import_str.lstrip(".").replace(".", "/")
        
        # Check direct matches or relative matches
        candidates = [
            f"{import_clean}.py",
            f"{import_clean}.js",
            f"{import_clean}.ts",
            f"{import_clean}/index.js",
            f"{import_clean}/index.ts",
            f"{import_clean}/__init__.py",
        ]

        if source_dir != Path("."):
            rel_candidate = (source_dir / import_clean).as_posix()
            candidates.extend([
                f"{rel_candidate}.py",
                f"{rel_candidate}.js",
                f"{rel_candidate}.ts",
            ])

        for path in all_paths:
            # Check if candidate ends with path or matches path
            for cand in candidates:
                if path.endswith(cand) or cand.endswith(path):
                    return path
            
            # Module name match (e.g. import "tracker" matches "aicontext/tracker.py")
            base_name = Path(path).stem
            if import_str == base_name or import_str.endswith(f".{base_name}"):
                return path

        return None

    def get_impact_radius(self, modified_files: List[str], max_depth: int = 2) -> Dict[str, List[str]]:
        """
        Computes impact radius for a set of modified files.
        Returns:
            dict mapping modified_file -> list of dependent files up to max_depth
        """
        impact_map = {}
        for mod_file in modified_files:
            if mod_file not in self.nodes:
                continue
            
            dependents = set()
            queue = [(mod_file, 0)]
            visited = {mod_file}

            while queue:
                current_file, depth = queue.pop(0)
                if depth > 0:
                    dependents.add(current_file)

                if depth < max_depth:
                    node = self.nodes.get(current_file)
                    if node:
                        for parent in node.imported_by:
                            if parent not in visited:
                                visited.add(parent)
                                queue.append((parent, depth + 1))

            impact_map[mod_file] = sorted(list(dependents))
        return impact_map

    def export_mermaid(self) -> str:
        """Generates a Mermaid graph representation."""
        lines = ["graph TD"]
        edges_added = set()

        for source_path, node in sorted(self.nodes.items()):
            source_id = self._clean_id(source_path)
            lines.append(f'    {source_id}["{source_path}"]')
            
            for target_path in sorted(node.imports_files):
                target_id = self._clean_id(target_path)
                edge_key = (source_id, target_id)
                if edge_key not in edges_added:
                    edges_added.add(edge_key)
                    lines.append(f'    {source_id} --> {target_id}')

        return "\n".join(lines)

    def export_json() -> dict:
        return {
            "nodes": {path: node.to_dict() for path, node in sorted(self.nodes.items())}
        }

    @staticmethod
    def _clean_id(path_str: str) -> str:
        clean = path_str.replace("/", "_").replace(".", "_").replace("-", "_")
        return f"node_{clean}"
