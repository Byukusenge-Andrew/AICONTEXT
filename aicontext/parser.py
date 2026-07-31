import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class SymbolInfo:
    def __init__(self, name: str, kind: str, line_no: int, details: str = "", docstring: str = ""):
        self.name = name
        self.kind = kind  # "class", "function", "variable", "interface", "method"
        self.line_no = line_no
        self.details = details
        self.docstring = docstring

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "line_no": self.line_no,
            "details": self.details,
            "docstring": self.docstring,
        }

class FileParseResult:
    def __init__(self, rel_path: str, language: str):
        self.rel_path = rel_path
        self.language = language
        self.symbols: List[SymbolInfo] = []
        self.imports: List[str] = []  # imported module names or file targets
        self.exports: List[str] = []

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": self.imports,
            "exports": self.exports,
        }

class SymbolExtractor:
    @staticmethod
    def detect_language(rel_path: str) -> str:
        ext = Path(rel_path).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".css": "css",
            ".html": "html",
            ".json": "json",
            ".md": "markdown",
        }
        return mapping.get(ext, "unknown")

    def parse_file(self, full_path: Path, rel_path: str) -> FileParseResult:
        lang = self.detect_language(rel_path)
        result = FileParseResult(rel_path, lang)
        
        if not full_path.exists():
            return result

        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return result

        if lang == "python":
            self._parse_python(content, result)
        elif lang in ["javascript", "typescript"]:
            self._parse_js_ts(content, result)
        else:
            self._parse_generic(content, result)

        return result

    def _parse_python(self, content: str, result: FileParseResult):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result.imports.append(node.module)

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node) or ""
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    details = f"inherits ({', '.join(bases)})" if bases else ""
                    result.symbols.append(SymbolInfo(node.name, "class", node.lineno, details, doc[:120]))
                    
                    # Methods in class
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            m_doc = ast.get_docstring(item) or ""
                            args = [a.arg for a in item.args.args]
                            result.symbols.append(SymbolInfo(f"{node.name}.{item.name}", "method", item.lineno, f"({', '.join(args)})", m_doc[:100]))

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args]
                    result.symbols.append(SymbolInfo(node.name, "function", node.lineno, f"({', '.join(args)})", doc[:120]))
        except Exception:
            self._parse_generic(content, result)

    def _parse_js_ts(self, content: str, result: FileParseResult):
        # Extract imports
        import_regex = re.compile(r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]')
        for match in import_regex.finditer(content):
            result.imports.append(match.group(1))

        # Extract functions / classes
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if line_str.startswith("//") or line_str.startswith("/*"):
                continue

            # Class
            cls_match = re.search(r'class\s+([A-Za-z0-9_]+)', line_str)
            if cls_match:
                result.symbols.append(SymbolInfo(cls_match.group(1), "class", idx))

            # Function / Arrow Function
            fn_match = re.search(r'(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)', line_str)
            if not fn_match:
                fn_match = re.search(r'(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\(', line_str)

            if fn_match:
                result.symbols.append(SymbolInfo(fn_match.group(1), "function", idx))

    def _parse_generic(self, content: str, result: FileParseResult):
        # Regex heuristics for generic functions/classes
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if re.match(r'^(?:def|func|function|fn|pub fn|class|struct|interface)\s+([A-Za-z0-9_]+)', line_str):
                match = re.search(r'^(?:def|func|function|fn|pub fn|class|struct|interface)\s+([A-Za-z0-9_]+)', line_str)
                if match:
                    kind = "class" if "class" in line_str or "struct" in line_str else "function"
                    result.symbols.append(SymbolInfo(match.group(1), kind, idx))
