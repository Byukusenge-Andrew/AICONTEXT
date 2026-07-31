import json
import http.server
import socketserver
import webbrowser
import threading
from pathlib import Path
from typing import Dict
from .config import Config

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIContext - Visual Codebase Explorer & Connection Graph</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-sidebar: #090d16;
            --accent-purple: #8b5cf6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-rose: #f43f5e;
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-primary);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
        }
        .sidebar-title h1 { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; }
        .sidebar-title span { font-size: 12px; color: var(--text-muted); }

        .nav-menu {
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .nav-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-muted);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s ease;
            text-align: left;
        }
        .nav-btn:hover, .nav-btn.active {
            background: var(--bg-card);
            color: var(--text-primary);
            border-color: var(--border-color);
        }
        .nav-btn.active {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15));
            border-color: var(--accent-purple);
            color: #fff;
        }

        .stats-box {
            margin-top: auto;
            padding: 20px;
            border-top: 1px solid var(--border-color);
            font-size: 13px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            color: var(--text-muted);
        }
        .stat-val { font-weight: 600; color: var(--accent-cyan); }

        /* Main Content */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .topbar {
            height: 60px;
            border-bottom: 1px solid var(--border-color);
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(10px);
        }
        .topbar-title { font-size: 16px; font-weight: 600; }
        .search-input {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 8px 14px;
            border-radius: 8px;
            color: #fff;
            font-family: inherit;
            width: 280px;
            outline: none;
        }
        .search-input:focus { border-color: var(--accent-cyan); }

        .content-body {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
        }

        .tab-pane { display: none; }
        .tab-pane.active { display: block; }

        /* Cards */
        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card-header {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Mermaid Graph Viewer */
        .graph-container {
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            overflow: auto;
            display: flex;
            justify-content: center;
            min-height: 500px;
        }

        /* File Symbols Tree */
        .symbol-list { list-style: none; margin-top: 10px; }
        .symbol-item {
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            padding: 6px 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 6px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tag-kind {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .tag-class { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }
        .tag-function { background: rgba(6, 182, 212, 0.2); color: #38bdf8; }
        .tag-method { background: rgba(16, 185, 129, 0.2); color: #34d399; }

        /* Changes list */
        .change-pill {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
        }
        .pill-added { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .pill-modified { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .pill-deleted { background: rgba(244, 63, 94, 0.2); color: var(--accent-rose); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="logo-icon">AI</div>
            <div class="sidebar-title">
                <h1>AIContext</h1>
                <span>Codebase & Connection Graph</span>
            </div>
        </div>
        <div class="nav-menu">
            <button class="nav-btn active" onclick="switchTab('graph')">
                🌐 Dependency Graph
            </button>
            <button class="nav-btn" onclick="switchTab('symbols')">
                🧩 Codebase & Symbols
            </button>
            <button class="nav-btn" onclick="switchTab('changes')">
                ⚡ Changes & Impact
            </button>
        </div>
        <div class="stats-box">
            <div class="stat-row"><span>Indexed Files</span><span class="stat-val" id="stat-files">0</span></div>
            <div class="stat-row"><span>Symbols Extracted</span><span class="stat-val" id="stat-symbols">0</span></div>
            <div class="stat-row"><span>Cache Status</span><span class="stat-val" style="color:var(--accent-green)">Active</span></div>
        </div>
    </div>

    <div class="main-container">
        <div class="topbar">
            <div class="topbar-title" id="tab-title">Dependency Graph</div>
            <input type="text" class="search-input" id="search-box" placeholder="Search symbols or files..." onkeyup="filterContent()">
        </div>
        <div class="content-body">
            <!-- Graph Tab -->
            <div id="tab-graph" class="tab-pane active">
                <div class="card">
                    <div class="card-header">Codebase Architecture & Dependency Connections</div>
                    <div class="graph-container">
                        <pre class="mermaid" id="mermaid-graph"></pre>
                    </div>
                </div>
            </div>

            <!-- Symbols Tab -->
            <div id="tab-symbols" class="tab-pane">
                <div id="symbols-container"></div>
            </div>

            <!-- Changes Tab -->
            <div id="tab-changes" class="tab-pane">
                <div class="card">
                    <div class="card-header">Recent Code Changes & Impact Radius</div>
                    <div id="changes-container"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let DATA = __DATA_JSON__;

        mermaid.initialize({ startOnLoad: false, theme: 'dark' });

        function init() {
            // Render Graph
            document.getElementById('mermaid-graph').textContent = DATA.mermaid;
            mermaid.run({ nodes: [document.getElementById('mermaid-graph')] });

            // Render Stats
            document.getElementById('stat-files').textContent = DATA.filesCount;
            document.getElementById('stat-symbols').textContent = DATA.symbolsCount;

            // Render Symbols
            const symContainer = document.getElementById('symbols-container');
            symContainer.innerHTML = '';
            for (const [path, fileData] of Object.entries(DATA.symbols)) {
                const card = document.createElement('div');
                card.className = 'card file-card';
                card.setAttribute('data-path', path);
                
                let symHtml = '';
                if (fileData.symbols && fileData.symbols.length > 0) {
                    symHtml = '<ul class="symbol-list">' + fileData.symbols.map(s => `
                        <li class="symbol-item">
                            <span class="tag-kind tag-${s.kind}">${s.kind}</span>
                            <strong>${s.name}</strong> (Line ${s.line_no})
                            ${s.details ? `<span style="color:var(--text-muted)">${s.details}</span>` : ''}
                        </li>
                    `).join('') + '</ul>';
                } else {
                    symHtml = '<p style="color:var(--text-muted);font-size:13px;">No explicit symbols parsed.</p>';
                }

                card.innerHTML = `
                    <div class="card-header">📄 ${path} <span style="font-size:12px;color:var(--text-muted);font-weight:400">(${fileData.language})</span></div>
                    ${symHtml}
                `;
                symContainer.appendChild(card);
            }

            // Render Changes
            const chgContainer = document.getElementById('changes-container');
            chgContainer.innerHTML = DATA.changesHtml;
        }

        function switchTab(tab) {
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
            
            const titles = { 'graph': 'Dependency Graph', 'symbols': 'Codebase & Symbols', 'changes': 'Recent Changes & Impact' };
            document.getElementById('tab-title').textContent = titles[tab];
        }

        function filterContent() {
            const q = document.getElementById('search-box').value.toLowerCase();
            document.querySelectorAll('.file-card').forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(q) ? 'block' : 'none';
            });
        }

        window.onload = init;
    </script>
</body>
</html>
"""

class Visualizer:
    def __init__(self, config: Config):
        self.config = config

    def generate_html(self, current_cache: dict, parse_results: dict, graph_mermaid: str, changes_md: str) -> str:
        symbols_count = sum(len(res.symbols) for res in parse_results.values())
        
        symbols_data = {}
        for path, res in parse_results.items():
            symbols_data[path] = res.to_dict()

        # Format changes html
        changes_html = f"<pre style='font-family:inherit;line-height:1.6;'>{changes_md}</pre>"

        data = {
            "mermaid": graph_mermaid,
            "filesCount": len(current_cache),
            "symbolsCount": symbols_count,
            "symbols": symbols_data,
            "changesHtml": changes_html,
        }

        html = HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(data))
        return html

    def write_dashboard(self, current_cache: dict, parse_results: dict, graph_mermaid: str, changes_md: str) -> Path:
        self.config.ensure_dir()
        html_content = self.generate_html(current_cache, parse_results, graph_mermaid, changes_md)
        html_file = self.config.aicontext_dir / "index.html"
        html_file.write_text(html_content, encoding="utf-8")
        return html_file

    def launch_browser(self, port: int = 8080):
        html_file = self.config.aicontext_dir / "index.html"
        if not html_file.exists():
            raise FileNotFoundError("Visualization dashboard not found. Run sync first.")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(html_file.parent), **kwargs)

        server = socketserver.TCPServer(("", port), Handler)
        url = f"http://localhost:{port}/index.html"
        
        print(f"🚀 AIContext Visualizer live at: {url}")
        webbrowser.open(url)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
