"""AST validation utilities for checking robustness smells."""

from __future__ import annotations
import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def check_robustness_smells(source_path: Path | str) -> list[dict[str, object]]:
    """Scan a Python file's AST for robustness anti-patterns.
    
    Checks for:
    - bare-except
    - mutable-default arguments
    - os.system calls
    """
    path = Path(source_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception as e:
        return [{"line": 0, "kind": "error", "detail": str(e)}]
        
    findings = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append({
                    "line": node.lineno,
                    "kind": "bare-except",
                    "detail": "except: without type"
                })
        elif isinstance(node, ast.Call):
            func = node.func
            fname = getattr(func, "id", None) or getattr(func, "attr", None)
            if fname == "system" and getattr(getattr(func, "value", None), "id", None) == "os":
                findings.append({
                    "line": node.lineno,
                    "kind": "os-system",
                    "detail": "os.system() used"
                })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
            for default in defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append({
                        "line": node.lineno,
                        "kind": "mutable-default",
                        "detail": "mutable default argument used"
                    })
                    
    return findings

__all__ = ["check_robustness_smells"]
