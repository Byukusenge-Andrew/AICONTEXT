import os
from pathlib import Path
from typing import List, Set

DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    ".aicontext/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "node_modules/",
    "venv/",
    ".venv/",
    "env/",
    "dist/",
    "build/",
    "*.egg-info/",
    ".idea/",
    ".vscode/",
    ".next/",
    "coverage/",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.lock",
    "package-lock.json",
    "poetry.lock",
]

class Config:
    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()
        self.aicontext_dir = self.root_dir / ".aicontext"
        self.cache_file = self.aicontext_dir / "cache.json"
        self.summary_file = self.aicontext_dir / "SUMMARY.md"
        self.graph_file = self.aicontext_dir / "graph.mmd"
        self.graph_json_file = self.aicontext_dir / "graph.json"
        self.changes_file = self.aicontext_dir / "recent_changes.md"
        self.ignore_patterns: Set[str] = set(DEFAULT_IGNORE_PATTERNS)
        self.load_ignore_files()

    def load_ignore_files(self):
        """Loads patterns from .gitignore and .aicontextignore if present."""
        for filename in [".gitignore", ".aicontextignore"]:
            ignore_path = self.root_dir / filename
            if ignore_path.exists():
                try:
                    with open(ignore_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                self.ignore_patterns.add(line)
                except Exception:
                    pass

    def ensure_dir(self):
        """Ensures the .aicontext directory exists."""
        self.aicontext_dir.mkdir(parents=True, exist_ok=True)
