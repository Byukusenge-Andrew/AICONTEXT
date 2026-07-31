import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import pathspec

from .config import Config

class FileState:
    def __init__(self, rel_path: str, file_hash: str, mtime: float, size: int):
        self.rel_path = rel_path
        self.file_hash = file_hash
        self.mtime = mtime
        self.size = size

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "hash": self.file_hash,
            "mtime": self.mtime,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileState":
        return cls(
            rel_path=data["rel_path"],
            file_hash=data["hash"],
            mtime=data["mtime"],
            size=data.get("size", 0),
        )

class ChangeTracker:
    def __init__(self, config: Config):
        self.config = config
        self.spec = pathspec.PathSpec.from_lines("gitignore", list(config.ignore_patterns))
        self.previous_cache: Dict[str, FileState] = {}
        self.load_cache()

    def load_cache(self):
        """Loads previous scan cache from .aicontext/cache.json."""
        if self.config.cache_file.exists():
            try:
                with open(self.config.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    files_data = data.get("files", {})
                    for rel_path, info in files_data.items():
                        self.previous_cache[rel_path] = FileState.from_dict(info)
            except Exception:
                self.previous_cache = {}

    def save_cache(self, current_cache: Dict[str, FileState]):
        """Saves current scan cache to .aicontext/cache.json."""
        self.config.ensure_dir()
        data = {
            "files": {rel: info.to_dict() for rel, info in current_cache.items()}
        }
        with open(self.config.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def compute_file_hash(self, file_path: Path) -> str:
        """Computes SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def scan_files(self) -> Tuple[Dict[str, FileState], List[str], List[str], List[str]]:
        """
        Scans workspace directory.
        Returns:
            current_cache: dict of all active files
            added_files: list of relative paths
            modified_files: list of relative paths
            deleted_files: list of relative paths
        """
        current_cache: Dict[str, FileState] = {}
        added: List[str] = []
        modified: List[str] = []

        root = self.config.root_dir
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            
            try:
                rel_path = path.relative_to(root).as_posix()
            except ValueError:
                continue

            if self.spec.match_file(rel_path):
                continue

            # Skip large files (> 2MB)
            stat = path.stat()
            if stat.st_size > 2 * 1024 * 1024:
                continue

            mtime = stat.st_mtime
            
            # Check fast mtime match first
            prev_state = self.previous_cache.get(rel_path)
            if prev_state and prev_state.mtime == mtime and prev_state.size == stat.st_size:
                file_hash = prev_state.file_hash
            else:
                file_hash = self.compute_file_hash(path)

            file_state = FileState(rel_path, file_hash, mtime, stat.st_size)
            current_cache[rel_path] = file_state

            if prev_state is None:
                added.append(rel_path)
            elif prev_state.file_hash != file_hash:
                modified.append(rel_path)

        deleted = [rel for rel in self.previous_cache if rel not in current_cache]

        return current_cache, added, modified, deleted

    def get_git_status(self) -> Dict[str, List[str]]:
        """Interrogates local git status if available."""
        result = {"staged": [], "unstaged": [], "untracked": [], "recent_commits": []}
        try:
            status_out = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.config.root_dir,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            for line in status_out.splitlines():
                if not line.strip():
                    continue
                index_status = line[0]
                work_status = line[1]
                file_path = line[3:].strip()
                if index_status in ["M", "A", "R"]:
                    result["staged"].append(file_path)
                if work_status == "M":
                    result["unstaged"].append(file_path)
                elif index_status == "?" and work_status == "?":
                    result["untracked"].append(file_path)

            log_out = subprocess.check_output(
                ["git", "log", "-n", "5", "--oneline"],
                cwd=self.config.root_dir,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            result["recent_commits"] = [line.strip() for line in log_out.splitlines() if line.strip()]
        except Exception:
            pass

        return result

    def get_git_diff_summary(self) -> str:
        """Gets short git diff of uncommitted changes."""
        try:
            diff_out = subprocess.check_output(
                ["git", "diff", "HEAD", "--stat"],
                cwd=self.config.root_dir,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            return diff_out.strip()
        except Exception:
            return ""
