import json
import os
import tempfile
from pathlib import Path
import pytest

from aicontext.config import Config
from aicontext.tracker import ChangeTracker
from aicontext.parser import SymbolExtractor
from aicontext.graph import ConnectionGraph
from aicontext.generator import ContextGenerator
from aicontext.visualizer import Visualizer
from aicontext.rules import RuleInjector
from aicontext.hooks import GitHookInstaller

def test_config_initialization(tmp_path):
    config = Config(tmp_path)
    config.ensure_dir()
    assert config.aicontext_dir.exists()
    assert config.aicontext_dir.is_dir()

def test_tracker_and_hash_caching(tmp_path):
    config = Config(tmp_path)
    config.ensure_dir()
    file1 = tmp_path / "main.py"
    file1.write_text("def hello(): pass\n", encoding="utf-8")

    tracker = ChangeTracker(config)
    cache, added, modified, deleted = tracker.scan_files()

    assert "main.py" in cache
    assert "main.py" in added
    assert len(modified) == 0

    tracker.save_cache(cache)

    # Re-scan without modifications
    tracker2 = ChangeTracker(config)
    cache2, added2, modified2, deleted2 = tracker2.scan_files()
    assert len(added2) == 0
    assert len(modified2) == 0

    # Modify file
    file1.write_text("def hello(): print('world')\n", encoding="utf-8")
    tracker3 = ChangeTracker(config)
    cache3, added3, modified3, deleted3 = tracker3.scan_files()
    assert "main.py" in modified3

def test_symbol_extraction(tmp_path):
    py_file = tmp_path / "app.py"
    py_file.write_text('''"""Module description explaining app functionality."""
import os
from pathlib import Path

class User:
    """User representation class."""
    def __init__(self, name: str):
        self.name = name

def calculate_total(a: int, b: int) -> int:
    """Calculates sum."""
    return a + b
''', encoding="utf-8")

    extractor = SymbolExtractor()
    result = extractor.parse_file(py_file, "app.py")

    assert result.language == "python"
    assert "Module description" in result.module_docstring
    assert "os" in result.imports
    assert "pathlib" in result.imports
    
    sym_names = [s.name for s in result.symbols]
    assert "User" in sym_names
    assert "calculate_total" in sym_names

def test_connection_graph_and_impact_radius(tmp_path):
    config = Config(tmp_path)
    
    utils_file = tmp_path / "utils.py"
    utils_file.write_text("def helper(): pass\n", encoding="utf-8")

    main_file = tmp_path / "main.py"
    main_file.write_text("import utils\ndef run(): utils.helper()\n", encoding="utf-8")

    tracker = ChangeTracker(config)
    extractor = SymbolExtractor()

    cache, _, _, _ = tracker.scan_files()
    parse_results = {rel: extractor.parse_file(tmp_path / rel, rel) for rel in cache}

    graph = ConnectionGraph(tmp_path)
    graph.build_graph(parse_results)

    assert "main.py" in graph.nodes
    assert "utils.py" in graph.nodes.get("main.py").imports_files

    # Impact radius: modifying utils.py should impact main.py
    impact = graph.get_impact_radius(["utils.py"])
    assert "main.py" in impact["utils.py"]

    mermaid_out = graph.export_mermaid()
    assert "main.py" in mermaid_out
    assert "utils.py" in mermaid_out

def test_visualizer_dashboard_generation(tmp_path):
    config = Config(tmp_path)
    visualizer = Visualizer(config)
    
    html_file = visualizer.write_dashboard(
        current_cache={"main.py": None},
        parse_results={},
        graph_mermaid="graph TD\nnode_main_py[\"main.py\"]",
        changes_md="No changes"
    )

    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert "AIContext" in content
    assert "3D Code Globe" in content

def test_rule_injector(tmp_path):
    config = Config(tmp_path)
    config.ensure_dir()
    injector = RuleInjector(config)
    files = injector.inject_rules()

    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / ".cursorrules").exists()
    assert (tmp_path / ".aicontext" / "rules.md").exists()

    agents_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "Token Preservation Rule" in agents_content
    assert "aicontext sync" in agents_content

def test_git_hook_installer(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = Config(tmp_path)
    
    installer = GitHookInstaller(config)
    installed = installer.install_hooks()

    assert len(installed) == 3
    assert (git_dir / "hooks" / "post-commit").exists()
    assert (git_dir / "hooks" / "post-checkout").exists()
    assert (git_dir / "hooks" / "pre-commit").exists()

def test_hashmap_lookup_and_neighborhood(tmp_path):
    config = Config(tmp_path)
    
    utils_file = tmp_path / "utils.py"
    utils_file.write_text("def helper(): pass\n", encoding="utf-8")

    main_file = tmp_path / "main.py"
    main_file.write_text("import utils\ndef run(): utils.helper()\n", encoding="utf-8")

    tracker = ChangeTracker(config)
    extractor = SymbolExtractor()

    cache, _, _, _ = tracker.scan_files()
    parse_results = {rel: extractor.parse_file(tmp_path / rel, rel) for rel in cache}

    graph = ConnectionGraph(tmp_path)
    graph.build_graph(parse_results)

    # Check HashMap module indexing
    assert "utils" in graph.module_map
    assert graph.module_map["utils"] == "utils.py"

    # Check N-hop neighborhood (both directions)
    neighborhood = graph.get_neighborhood(["main.py"], max_depth=1)
    assert "utils.py" in neighborhood["main.py"]

    # Check Tiered Context Generation
    generator = ContextGenerator(config)
    payload = generator.generate_tiered_context(["main.py"], graph, parse_results, radius=1, tier=2)
    assert "main.py" in payload
    assert "utils.py" in payload
    assert "[TARGET]" in payload

def test_security_guard_and_anti_leakage(tmp_path):
    from aicontext.security import SecurityGuard

    # 1. Test multi-target ignore auto-injection (.gitignore, .dockerignore, etc.)
    docker_ignore = tmp_path / ".dockerignore"
    docker_ignore.write_text("node_modules/\n", encoding="utf-8")

    updated = SecurityGuard.ensure_all_ignores_updated(tmp_path)
    assert ".gitignore" in updated
    assert ".dockerignore" in updated

    git_content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    docker_content = (tmp_path / ".dockerignore").read_text(encoding="utf-8")
    assert ".aicontext/" in git_content
    assert ".aicontext/" in docker_content

    # 2. Test sensitive file filter
    assert SecurityGuard.is_sensitive_file(".env")
    assert SecurityGuard.is_sensitive_file(".env.local")
    assert SecurityGuard.is_sensitive_file("server.key")
    assert SecurityGuard.is_sensitive_file("credentials.json")
    assert not SecurityGuard.is_sensitive_file("main.py")

    # 3. Test secret redaction
    raw_doc = "Connect using sk-proj-1234567890abcdef1234567890 and postgres://user:pass@localhost/db"
    redacted = SecurityGuard.redact_secrets(raw_doc)
    assert "sk-proj" not in redacted
    assert "[REDACTED_OPENAI_KEY]" in redacted
    assert "[REDACTED_CONNECTION_STRING]" in redacted

    # 4. Test identifier obfuscation
    obs_path = SecurityGuard.obfuscate_identifier("aicontext/tracker.py")
    assert obs_path.startswith("obs_")
    assert len(obs_path) == 16

    # 5. Test zero-trace workspace purge
    (tmp_path / ".aicontext").mkdir(exist_ok=True)
    (tmp_path / "AGENTS.md").write_text("Token Preservation Rule\naicontext sync\nCustom User Content\n", encoding="utf-8")
    purged = SecurityGuard.purge_all(tmp_path)
    assert ".aicontext/" in purged
    assert "AGENTS.md" in purged
def test_project_custom_config(tmp_path):
    # Create .aicontext.json with custom sensitive patterns and custom ignore targets
    custom_cfg = tmp_path / ".aicontext.json"
    custom_cfg.write_text(json.dumps({
        "sensitive_patterns": ["custom_secret.txt"],
        "ignore_targets": [".customignore"],
        "custom_ignore_patterns": ["custom_build/"]
    }), encoding="utf-8")

    (tmp_path / ".customignore").write_text("# Custom ignore file\n", encoding="utf-8")

    config = Config(tmp_path)
    config.ensure_dir()

    assert "custom_secret.txt" in config.custom_sensitive_patterns
    assert ".customignore" in config.custom_ignore_targets
    assert "custom_build/" in config.ignore_patterns

    # Verify custom sensitive file check
    from aicontext.security import SecurityGuard
    assert SecurityGuard.is_sensitive_file("custom_secret.txt", custom_patterns=config.custom_sensitive_patterns)

    # Verify custom ignore target auto-protection
    assert (tmp_path / ".customignore").exists()
    assert ".aicontext/" in (tmp_path / ".customignore").read_text(encoding="utf-8")




