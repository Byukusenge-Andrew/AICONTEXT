import json
import os
from pathlib import Path
from typing import List, Set

from .security import SecurityGuard

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
    ".env*",
    "*.pem",
    "*.key",
    "*.pfx",
    "*.p12",
    "*id_rsa*",
    "*id_ed25519*",
    "credentials.json",
    "secrets.json",
    "secrets.yml",
    "secrets.yaml",
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
        
        self.custom_sensitive_patterns: List[str] = []
        self.custom_ignore_targets: List[str] = []
        self.ignore_patterns: Set[str] = set(DEFAULT_IGNORE_PATTERNS)
        
        self.load_project_config()
        self.load_ignore_files()

    def load_project_config(self):
        """Loads custom per-project configuration from .aicontext.json if present."""
        for cfg_name in [".aicontext.json", ".aicontextrc"]:
            cfg_path = self.root_dir / cfg_name
            if cfg_path.exists():
                try:
                    data = json.loads(cfg_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        if "sensitive_patterns" in data and isinstance(data["sensitive_patterns"], list):
                            self.custom_sensitive_patterns.extend(data["sensitive_patterns"])
                        if "ignore_targets" in data and isinstance(data["ignore_targets"], list):
                            self.custom_ignore_targets.extend(data["ignore_targets"])
                        if "custom_ignore_patterns" in data and isinstance(data["custom_ignore_patterns"], list):
                            for pat in data["custom_ignore_patterns"]:
                                self.ignore_patterns.add(pat)
                except Exception:
                    pass

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
        """Ensures the .aicontext directory exists, applies OS stealth mode, and updates all target ignore files."""
        self.aicontext_dir.mkdir(parents=True, exist_ok=True)
        SecurityGuard.apply_stealth_mode(self.aicontext_dir)
        SecurityGuard.ensure_all_ignores_updated(self.root_dir, custom_targets=self.custom_ignore_targets)
