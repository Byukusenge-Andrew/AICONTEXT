import os
import stat
from pathlib import Path
from typing import List
from .config import Config

POST_COMMIT_HOOK = """#!/bin/sh
# AIContext Git Post-Commit Hook - Auto-sync context on commit
aicontext sync --path . >/dev/null 2>&1 &
"""

POST_CHECKOUT_HOOK = """#!/bin/sh
# AIContext Git Post-Checkout Hook - Auto-sync context on branch switch
aicontext sync --path . >/dev/null 2>&1 &
"""

PRE_COMMIT_HOOK = """#!/bin/sh
# AIContext Git Pre-Commit Hook - Ensure changes and graph are updated before commit
aicontext sync --path .
"""

class GitHookInstaller:
    def __init__(self, config: Config):
        self.config = config
        self.git_dir = self.config.root_dir / ".git"
        self.hooks_dir = self.git_dir / "hooks"

    def install_hooks(self) -> List[str]:
        """Installs automated git hooks for zero-touch auto-sync on code changes."""
        if not self.git_dir.exists():
            return []

        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        installed = []

        hooks = {
            "post-commit": POST_COMMIT_HOOK,
            "post-checkout": POST_CHECKOUT_HOOK,
            "pre-commit": PRE_COMMIT_HOOK,
        }

        for hook_name, hook_content in hooks.items():
            hook_path = self.hooks_dir / hook_name
            hook_path.write_text(hook_content, encoding="utf-8")
            
            # Make executable on Unix/Mac
            try:
                current = os.stat(hook_path)
                os.chmod(hook_path, current.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            except Exception:
                pass

            installed.append(f".git/hooks/{hook_name}")

        return installed
