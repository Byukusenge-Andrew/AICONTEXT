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
    py_file.write_text('''
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
    assert "Dependency Graph" in content

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
