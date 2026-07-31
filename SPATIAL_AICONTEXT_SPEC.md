# AIContext Specification: Graph-Native Context Engine & Tiered Summarization

> **Refined Architectural Specification**: Grounded in exact graph adjacency, $\mathcal{O}(1)$ hash-map import resolution, $N$-hop neighborhood pruning, and interactive 3D dependency visualization.

---

## 1. Executive Summary & Vision

AI coding assistants often burn tokens by re-reading entire repositories or indiscriminately loading large context windows. 

**AIContext** solves this using an incremental, graph-native approach:
* **$\mathcal{O}(1)$ HashMap Import Resolution**: Resolves package and relative imports instantly via indexed module-to-filepath lookup tables.
* **Exact $N$-Hop Neighborhood Scoping**: Uses deterministic BFS graph radius traversal ($R$-hop adjacency) to extract strictly relevant dependent files without risking missed dependencies.
* **Tiered Context Summarization**: Delivers multi-level context payloads (Global Architecture, Graph Neighborhood, File-Level AST Signatures) to drastically optimize token usage.
* **Interactive 3D Visualizer**: Renders the codebase graph as an interactive 3D WebGL network in the browser dashboard.

---

## 2. Core Architecture: Exact Graph Radius Traversal

```
                       [ TARGET MODIFIED FILE ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
            [ 1-Hop Dependent ]             [ 1-Hop Dependent ]
                  │                               │
           ┌──────┴──────┐                 ┌──────┴──────┐
           ▼             ▼                 ▼             ▼
     [ 2-Hop Dep ] [ 2-Hop Dep ]     [ 2-Hop Dep ] [ 2-Hop Dep ]
```

### Deterministic $N$-Hop BFS Radius Extraction
Instead of heuristic spatial pruning (which risks dropping crucial files), AIContext uses exact BFS graph traversal:
1. **Target Identification**: Identifies active/modified files.
2. **Upstream & Downstream Traversal**: Follows incoming (`imported_by`) and outgoing (`imports`) graph edges.
3. **Depth Bounding ($R$)**: Bounds traversal to radius $R$ (default $R=2$), collecting all structural dependencies in $\mathcal{O}(V_R + E_R)$ time.

---

## 3. High-Performance Indexing

### A. HashMap Module Indexing ($\mathcal{O}(1)$ Lookups)
Import resolution maps import statements (e.g., `import aicontext.tracker`) directly to workspace relative paths using a pre-computed dictionary:
$$\text{ModuleMap}: \text{import\_path} \longrightarrow \text{file\_path}$$
* **Lookup Time**: $\mathcal{O}(1)$ per import.
* **Total Graph Build**: $\mathcal{O}(I)$ time where $I$ is total import statements.

### B. Incremental AST Symbol Caching
* Uses language-specific AST parsers to extract top-level functions, classes, docstrings, and imports.
* Stores incremental file SHA-256 hashes; only re-parses files that changed since the last git delta/sync.

---

## 4. Tiered Context Delivery (Token Optimization)

AIContext structures output payloads into 3 distinct granularity tiers:

| Tier | Scope | Content Included | Ideal Use Case |
| :--- | :--- | :--- | :--- |
| **Tier 1: Global** | Full Workspace | Module map, top-level architecture summary (`SUMMARY.md`) | Session bootstrap & system-level planning |
| **Tier 2: Neighborhood** | $R$-hop Radius | Direct dependencies, signatures, and impact radius | Feature development & refactoring |
| **Tier 3: Focus** | Single File | Full AST symbols, line-level code, and docstrings | Targeted bug fixes & unit test writing |

---

## 5. Interactive 3D WebGL Visualizer

While the backend engine uses exact graph data structures, the browser visualization dashboard (`.aicontext/index.html`) renders the graph as a **3D WebGL Force-Directed Globe/Network**:
* **Nodes**: Represent workspace files, color-coded by module/directory.
* **Edges**: Glowing 3D links representing dependency imports.
* **Interactive Filtering**: Search nodes, highlight $R$-hop impact radius, and inspect symbol maps in real time.

---

## 6. Implementation Roadmap

- [x] **Phase 1**: Incremental SHA-256 caching, AST symbol extraction, and `AGENTS.md` AI rule injection.
- [x] **Phase 2**: Exact $N$-hop impact radius computation & Mermaid dependency graph export.
- [x] **Phase 3**: Zero-config global MCP server integration for Antigravity & Cursor.
- [ ] **Phase 4**: $\mathcal{O}(1)$ HashMap lookup table enhancement in `aicontext/graph.py`.
- [ ] **Phase 5**: Interactive 3D Three.js WebGL dashboard upgrade in `aicontext/visualizer.py`.
