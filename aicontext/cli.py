import time
import sys
from pathlib import Path
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
def sync(path: str):
    """Incrementally scans workspace, updates context cache, changes, and connection graph."""
    config = Config(path)
    sync_impl(config)

def sync_impl(config: Config):
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
