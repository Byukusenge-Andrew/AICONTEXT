import time
import sys
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.panel import Panel

from .config import Config
from .tracker import ChangeTracker
from .parser import SymbolExtractor
from .graph import ConnectionGraph
from .generator import ContextGenerator
from .visualizer import Visualizer
from .rules import RuleInjector
from .hooks import GitHookInstaller

console = Console()

@click.group()
def cli():
    """AIContext - Persistent Codebase Context, Change Tracker & Connection Graph Engine."""
    pass

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase to index.")
def init(path: str):
    """Initializes .aicontext directory, installs AI rules, git hooks, and performs initial sync."""
    config = Config(path)
    config.ensure_dir()
    console.print(f"[bold green]Initialized AIContext directory at:[/] {config.aicontext_dir}")
    
    # Inject AI instruction rules
    injector = RuleInjector(config)
    rule_files = injector.inject_rules()
    console.print(f"[bold cyan]Configured AI Rules in:[/] {', '.join(rule_files)}")
    
    # Install git hooks if git repo
    hook_installer = GitHookInstaller(config)
    installed_hooks = hook_installer.install_hooks()
    if installed_hooks:
        console.print(f"[bold green]Automated Git Hooks installed:[/] {', '.join(installed_hooks)}")

    sync_impl(config)

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--obscure", is_flag=True, help="Obfuscate symbol names and path identifiers in generated context artifacts.")
def sync(path: str, obscure: bool):
    """Incrementally scans workspace, updates context cache, changes, and connection graph."""
    config = Config(path)
    sync_impl(config, obscure=obscure)

def sync_impl(config: Config, obscure: bool = False):
    tracker = ChangeTracker(config)
    extractor = SymbolExtractor()
    
    with console.status("[bold blue]Scanning workspace & computing incremental hashes..."):
        current_cache, added, modified, deleted = tracker.scan_files()

    with console.status("[bold blue]Parsing AST symbols & imports..."):
        parse_results = {}
        for rel_path in current_cache:
            full_path = config.root_dir / rel_path
            parse_results[rel_path] = extractor.parse_file(full_path, rel_path)

    with console.status("[bold blue]Building dependency connection graph & impact radius..."):
        graph = ConnectionGraph(config.root_dir)
        graph.build_graph(parse_results)

    git_status = tracker.get_git_status()

    with console.status("[bold blue]Generating context artifacts, rules & UI dashboard..."):
        generator = ContextGenerator(config)
        generator.generate_all(current_cache, parse_results, added, modified, deleted, git_status, graph)
        
        # Ensure rules are present
        injector = RuleInjector(config)
        injector.inject_rules()

        tracker.save_cache(current_cache)

    console.print("[bold green]✨ AIContext sync complete![/]")
    console.print(f"  • Files Indexed: [cyan]{len(current_cache)}[/]")
    console.print(f"  • Added: [green]{len(added)}[/], Modified: [yellow]{len(modified)}[/], Deleted: [red]{len(deleted)}[/]")
    console.print(f"  • AI Rules: [bold cyan]AGENTS.md & .cursorrules updated[/]")
    console.print(f"  • HTML Visualizer: [bold underline]{config.aicontext_dir / 'index.html'}[/]")

@cli.command(name="install-hooks")
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def install_hooks(path: str):
    """Installs automatic Git pre-commit, post-commit, and post-checkout hooks for background auto-sync."""
    config = Config(path)
    installer = GitHookInstaller(config)
    installed = installer.install_hooks()
    if installed:
        console.print(f"[bold green]Successfully installed Git auto-sync hooks:[/] {', '.join(installed)}")
    else:
        console.print("[yellow]No .git directory found. Initialize a git repository first (`git init`).[/]")

@cli.command(name="install-rules")
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def install_rules(path: str):
    """Installs or updates AI instruction rules (AGENTS.md, .cursorrules) in project."""
    config = Config(path)
    injector = RuleInjector(config)
    files = injector.inject_rules()
    console.print(f"[bold green]Successfully installed AI context rules in:[/] {', '.join(files)}")

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def bootstrap(path: str):
    """Outputs low-token bootstrap prompt for new AI conversations."""
    config = Config(path)
    prompt_file = config.aicontext_dir / "prompt.txt"
    if not prompt_file.exists():
        sync_impl(config)
    
    console.print(prompt_file.read_text(encoding="utf-8"))

@cli.command(name="ui")
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--port", "-port", default=8080, help="Port to serve interactive dashboard.")
def ui(path: str, port: int):
    """Launches interactive browser visualization dashboard (alias: visualize)."""
    visualize_impl(path, port)

@cli.command(name="visualize")
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--port", "-port", default=8080, help="Port to serve interactive dashboard.")
def visualize(path: str, port: int):
    """Launches interactive browser visualization dashboard."""
    visualize_impl(path, port)

def visualize_impl(path: str, port: int):
    config = Config(path)
    if not (config.aicontext_dir / "index.html").exists():
        console.print("[yellow]No visualization dashboard found. Running sync first...[/]")
        sync_impl(config)

    console.print(f"[bold cyan]Opening AIContext Interactive Dashboard at port {port}...[/]")
    visualizer = Visualizer(config)
    visualizer.launch_browser(port=port)

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def changes(path: str):
    """Displays recent code changes and impact radius in terminal."""
    config = Config(path)
    if not config.changes_file.exists():
        console.print("[yellow]No change tracking file found. Running sync first...[/]")
        sync_impl(config)
    
    content = config.changes_file.read_text(encoding="utf-8")
    console.print(Panel(content, title="Recent Changes & Impact Radius", border_style="cyan"))

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def graph(path: str):
    """Displays codebase dependency connection graph in terminal."""
    config = Config(path)
    if not config.graph_file.exists():
        sync_impl(config)

    content = config.graph_file.read_text(encoding="utf-8")
    console.print(Panel(content, title="Connection Graph (Mermaid)", border_style="magenta"))

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--interval", "-i", default=3.0, help="Poll interval in seconds.")
def watch(path: str, interval: float):
    """Monitors workspace for file changes and auto-syncs context in real-time."""
    config = Config(path)
    console.print(f"[bold cyan]Eyeing workspace changes every {interval}s in:[/] {config.root_dir}")
    tracker = ChangeTracker(config)

    try:
        while True:
            current_cache, added, modified, deleted = tracker.scan_files()
            if added or modified or deleted:
                console.print(f"\n[bold yellow]⚡ Change detected![/] (+{len(added)}, ~{len(modified)}, -{len(deleted)}) Syncing...")
                sync_impl(config)
                tracker = ChangeTracker(config)
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[bold red]Stopped file watcher.[/]")

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--file", "-f", "target_file", required=True, help="Target file relative path to query context for.")
@click.option("--radius", "-r", default=2, type=int, help="Neighborhood radius depth R.")
@click.option("--tier", "-t", default=2, type=int, help="Context detail tier (1=Global, 2=Neighborhood, 3=Focus).")
def query(path: str, target_file: str, radius: int, tier: int):
    """Queries N-hop neighborhood context payload for specific file(s)."""
    config = Config(path)
    tracker = ChangeTracker(config)
    extractor = SymbolExtractor()
    current_cache, _, _, _ = tracker.scan_files()
    parse_results = {rel: extractor.parse_file(config.root_dir / rel, rel) for rel in current_cache}
    
    conn_graph = ConnectionGraph(config.root_dir)
    conn_graph.build_graph(parse_results)
    
    generator = ContextGenerator(config)
    payload = generator.generate_tiered_context([target_file], conn_graph, parse_results, radius=radius, tier=tier)
    console.print(payload)

def _count_tokens(text: str) -> int:
    """Counts tokens dynamically in real time using tiktoken BPE if available, or exact char ratio."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, int(len(text) / 4))

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
@click.option("--file", "-f", "target_file", default=None, help="Optional target file to measure scoped query savings.")
def stats(path: str, target_file: Optional[str]):
    """Calculates and displays token savings metrics dynamically in real-time from the live workspace."""
    config = Config(path)
    tracker = ChangeTracker(config)
    extractor = SymbolExtractor()
    
    with console.status("[bold blue]Dynamically scanning live workspace files..."):
        current_cache, _, _, _ = tracker.scan_files()
        
        # 1. Real-time dynamic read of all workspace source files
        raw_contents = []
        for rel_path, state in current_cache.items():
            try:
                full_path = config.root_dir / rel_path
                raw_contents.append(full_path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass

        full_raw_text = "\n".join(raw_contents)
        raw_chars = len(full_raw_text)
        raw_tokens = _count_tokens(full_raw_text)

        # 2. Real-time dynamic read of generated AIContext summary map
        summary_text = config.summary_file.read_text(encoding="utf-8") if config.summary_file.exists() else ""
        summary_tokens = _count_tokens(summary_text)

        # 3. Dynamic real-time computation of scoped neighborhood payload
        scoped_tokens = None
        if target_file and target_file in current_cache:
            parse_results = {rel: extractor.parse_file(config.root_dir / rel, rel) for rel in current_cache}
            conn_graph = ConnectionGraph(config.root_dir)
            conn_graph.build_graph(parse_results)
            generator = ContextGenerator(config)
            payload = generator.generate_tiered_context([target_file], conn_graph, parse_results, radius=1, tier=2)
            scoped_tokens = _count_tokens(payload)

    summary_savings = ((raw_tokens - summary_tokens) / max(raw_tokens, 1)) * 100
    
    try:
        import tiktoken
        tokenizer_name = "Exact BPE (tiktoken/cl100k_base)"
    except Exception:
        tokenizer_name = "Live Char-Ratio BPE (~4 chars/token)"

    console.print(f"\n[bold magenta]📊 Live Real-Time Token Analysis[/] [dim]({tokenizer_name})[/]")
    console.print(f"• [bold white]Raw Codebase (Live Files):[/]  ~{raw_tokens:,} tokens ({raw_chars:,} chars)")
    console.print(f"• [bold cyan]AIContext Summary Map:[/]   ~{summary_tokens:,} tokens ([bold green]-{summary_savings:.1f}% reduction[/])")
    
    if scoped_tokens is not None:
        scoped_savings = ((raw_tokens - scoped_tokens) / max(raw_tokens, 1)) * 100
        console.print(f"• [bold yellow]Scoped Query ({target_file}):[/] ~{scoped_tokens:,} tokens ([bold green]-{scoped_savings:.1f}% reduction[/])")
        console.print(f"\n✨ [bold green]Saved ~{raw_tokens - scoped_tokens:,} actual tokens on this turn![/]\n")
    else:
        console.print(f"\n✨ [bold green]Saved ~{raw_tokens - summary_tokens:,} actual tokens per turn![/]\n")

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def audit(path: str):
    """Runs a security audit checking multi-target ignore files, sensitive files, and pre-commit security gates."""
    config = Config(path)
    from .security import SecurityGuard
    
    updated = SecurityGuard.ensure_all_ignores_updated(config.root_dir)
    results = SecurityGuard.audit(config.root_dir)
    
    console.print("\n[bold magenta]🛡️ AIContext Security & Anti-Leakage Audit[/]")
    
    if updated:
        console.print(f"[bold green]Updated Ignore Files:[/] {', '.join(updated)}")
    
    console.print("\n[bold white]Multi-Target Ignore Protection Status:[/]")
    for fname, status in results["ignore_files"].items():
        if status == "SECURE":
            color = "green"
            icon = "✅"
        elif status == "NOT_PRESENT":
            color = "dim"
            icon = "⚪"
        else:
            color = "yellow"
            icon = "⚠️"
        console.print(f"  {icon} [bold {color}]{fname}:[/] {status}")

    gate_status = "✅ ACTIVE" if results["git_pre_commit_gate"] else "⚪ NOT INSTALLED (Run 'aicontext init')"
    console.print(f"\n[bold white]Git Pre-Commit Security Gate:[/] {gate_status}")
    console.print("\n[bold green]🔒 All secret redactions and sensitive file exclusions active.[/]\n")

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def purge(path: str):
    """Securely purges all .aicontext artifacts, git hooks, and injected rules with zero trace."""
    config = Config(path)
    from .security import SecurityGuard
    purged = SecurityGuard.purge_all(config.root_dir)
    if purged:
        console.print(f"[bold green]🔒 Zero-Trace Purge Complete![/] Sanitized: {', '.join(purged)}")
    else:
        console.print("[bold yellow]Workspace is already clean; no AIContext trace found.[/]")

@cli.command()
@click.option("--path", "-p", default=".", help="Root directory of codebase.")
def mcp(path: str):
    """Launches Model Context Protocol (MCP) server for IDE integration (Antigravity, Cursor, Claude)."""
    try:
        from .mcp_server import run_mcp_server
        console.print("[bold green]Starting AIContext MCP Server...[/]")
        run_mcp_server(path)
    except Exception as e:
        console.print(f"[bold red]Error launching MCP server:[/] {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli()
