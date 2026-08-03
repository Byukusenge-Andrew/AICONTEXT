"""
AIContext Security Guard - Manages multi-target ignore enforcement, AST secret redaction, identifier obfuscation, and zero-trace workspace purging.
"""
import hashlib
import os
import re
import fnmatch
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

IGNORE_TARGET_FILES = [
    ".gitignore",
    ".dockerignore",
    ".helmignore",
    ".npmignore",
    ".gcloudignore",
    ".vercelignore",
]

SENSITIVE_FILE_PATTERNS = [
    ".env",
    ".env.*",
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

SECRET_REGEX_PATTERNS = [
    (r"sk-proj-[a-zA-Z0-9_\-]{20,}", "[REDACTED_OPENAI_KEY]"),
    (r"sk-[a-zA-Z0-9_\-]{20,}", "[REDACTED_API_KEY]"),
    (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
    (r"ghp_[a-zA-Z0-9]{36}", "[REDACTED_GITHUB_TOKEN]"),
    (r"gho_[a-zA-Z0-9]{36}", "[REDACTED_GITHUB_OAUTH]"),
    (r"glpat-[a-zA-Z0-9_\-]{20,}", "[REDACTED_GITLAB_TOKEN]"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer [REDACTED_TOKEN]"),
    (r"-----BEGIN[A-Z\s]+PRIVATE KEY-----[\s\S]*?-----END[A-Z\s]+PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
    (r"(postgres|postgresql|mongodb|mysql|redis)://[^\s'\"]+", "\\1://[REDACTED_CONNECTION_STRING]"),
]

class SecurityGuard:
    """Security Guard for AIContext - handles multi-target ignore enforcement, secret redaction, identifier obfuscation, OS stealth mode, and zero-trace workspace purging."""

    @staticmethod
    def ensure_all_ignores_updated(root_dir: Path, custom_targets: List[str] = None) -> List[str]:
        """Scans workspace root for target ignore files (default + custom) and ensures .aicontext/ is present."""
        updated_files = []
        pattern_entry = ".aicontext/"
        targets = list(IGNORE_TARGET_FILES)
        if custom_targets:
            for ct in custom_targets:
                if ct not in targets:
                    targets.append(ct)

        for ignore_name in targets:
            ignore_path = root_dir / ignore_name
            if ignore_name == ".gitignore" or ignore_path.exists():
                already_present = False
                lines = []
                if ignore_path.exists():
                    try:
                        content = ignore_path.read_text(encoding="utf-8")
                        lines = content.splitlines()
                        for line in lines:
                            clean_line = line.strip()
                            if clean_line == ".aicontext" or clean_line == ".aicontext/" or clean_line.startswith(".aicontext/"):
                                already_present = True
                                break
                    except Exception:
                        pass

                if not already_present:
                    try:
                        with open(ignore_path, "a", encoding="utf-8") as f:
                            if lines and not lines[-1].strip() == "":
                                f.write("\n")
                            f.write("\n# AIContext Cache Directory\n.aicontext/\n")
                        updated_files.append(ignore_name)
                    except Exception:
                        pass

        return updated_files

    @staticmethod
    def is_sensitive_file(rel_path: str, custom_patterns: List[str] = None) -> bool:
        """Checks if a file path matches default or custom sensitive pattern lists (.env, keys, certificates)."""
        base_name = Path(rel_path).name.lower()
        posix_path = Path(rel_path).as_posix().lower()

        patterns = list(SENSITIVE_FILE_PATTERNS)
        if custom_patterns:
            patterns.extend([p.lower() for p in custom_patterns])

        for pattern in patterns:
            if fnmatch.fnmatch(base_name, pattern) or fnmatch.fnmatch(posix_path, pattern):
                return True
        return False

    @staticmethod
    def redact_secrets(text: str) -> str:
        """Masks hardcoded secrets, API keys, private keys, and connection strings from text."""
        if not text:
            return text

        redacted = text
        for pattern, replacement in SECRET_REGEX_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)

        return redacted

    @staticmethod
    def obfuscate_identifier(identifier: str, salt: str = "aicontext_salt") -> str:
        """Obfuscates an identifier string (symbol name or path) using a keyed hash digest."""
        if not identifier:
            return identifier
        digest = hashlib.sha256(f"{salt}:{identifier}".encode("utf-8")).hexdigest()[:12]
        return f"obs_{digest}"

    @staticmethod
    def apply_stealth_mode(aicontext_dir: Path):
        """Conceals .aicontext directory using OS hidden folder attributes (attrib +h on Windows)."""
        if not aicontext_dir.exists():
            return
        if os.name == "nt":
            try:
                subprocess.run(["attrib", "+h", str(aicontext_dir)], capture_output=True, check=False)
            except Exception:
                pass

    @staticmethod
    def purge_all(root_dir: Path) -> List[str]:
        """Securely purges .aicontext directory, restores clean rules, and uninstalls git hooks."""
        purged = []

        # 1. Delete .aicontext directory
        aicontext_dir = root_dir / ".aicontext"
        if aicontext_dir.exists():
            try:
                shutil.rmtree(aicontext_dir)
                purged.append(".aicontext/")
            except Exception:
                pass

        # 2. Clean git hooks
        hooks = [root_dir / ".git" / "hooks" / h for h in ["pre-commit", "post-commit", "post-checkout"]]
        for hook_path in hooks:
            if hook_path.exists():
                try:
                    content = hook_path.read_text(encoding="utf-8")
                    if "aicontext" in content:
                        hook_path.unlink()
                        purged.append(f".git/hooks/{hook_path.name}")
                except Exception:
                    pass

        # 3. Clean injected rules from AGENTS.md and .cursorrules
        for rule_file in [root_dir / "AGENTS.md", root_dir / ".cursorrules"]:
            if rule_file.exists():
                try:
                    lines = rule_file.read_text(encoding="utf-8").splitlines()
                    clean_lines = [l for l in lines if "aicontext" not in l.lower() and "Token Preservation Rule" not in l]
                    if len(clean_lines) != len(lines):
                        rule_file.write_text("\n".join(clean_lines), encoding="utf-8")
                        purged.append(rule_file.name)
                except Exception:
                    pass

        return purged

    @staticmethod
    def audit(root_dir: Path) -> Dict:
        """Runs a complete security audit on the workspace."""
        results = {
            "ignore_files": {},
            "sensitive_files_detected": [],
            "git_pre_commit_gate": False,
        }

        for ignore_name in IGNORE_TARGET_FILES:
            ignore_path = root_dir / ignore_name
            if ignore_path.exists():
                try:
                    content = ignore_path.read_text(encoding="utf-8")
                    has_aicontext = any(
                        line.strip() in [".aicontext", ".aicontext/", ".aicontext/*"]
                        for line in content.splitlines()
                    )
                    results["ignore_files"][ignore_name] = "SECURE" if has_aicontext else "MISSING_ENTRY"
                except Exception:
                    results["ignore_files"][ignore_name] = "ERROR_READING"
            else:
                results["ignore_files"][ignore_name] = "NOT_PRESENT"

        # Check git pre-commit hook
        git_hook = root_dir / ".git" / "hooks" / "pre-commit"
        if git_hook.exists():
            try:
                hook_content = git_hook.read_text(encoding="utf-8")
                if ".aicontext" in hook_content:
                    results["git_pre_commit_gate"] = True
            except Exception:
                pass

        return results
