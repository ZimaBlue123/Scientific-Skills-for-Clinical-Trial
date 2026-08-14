"""Stricter F821-only check using pyflakes-equivalent logic.

pyflakes flags only `Name(ctx=Load)` references that are *not* bound
in the same scope chain before the reference. We approximate this by
walking AST with proper scoping (a simpler version of pyflakes).
"""
import ast
from pathlib import Path

p = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts\common_scripts\docx_utils.py")
src = p.read_text(encoding="utf-8")
tree = ast.parse(src)
imports = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for n in node.names:
            imports.add((n.asname or n.name.split(".")[0], "module"))
    elif isinstance(node, ast.ImportFrom):
        for n in node.names:
            imports.add((n.asname or n.name, "module"))

import builtins

defined = set(dir(builtins)) | {n for n, _ in imports} | {"__name__", "__file__", "__doc__"}

# At module level, look for Name nodes that are loaded but never bound
# in the module scope.
module_top_assigns = set()
for node in tree.body:
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                module_top_assigns.add(tgt.id)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        module_top_assigns.add(node.name)
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        for n in node.names:
            module_top_assigns.add(n.asname or n.name)

defined |= module_top_assigns

# Build a list of module-level Name(ctx=Load) references.
module_loads = []
for node in tree.body:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            module_loads.append((sub.lineno, sub.col_offset, sub.id))

undefined = [(ln, c, name) for (ln, c, name) in module_loads if name not in defined]

if undefined:
    print("UNDEFINED NAMES (F821 candidates):")
    for ln, c, name in undefined:
        print(f"  L{ln}:{c} {name}")
else:
    print("OK: no F821 at module level")

# Also check ALL scopes (loosely)
print()
print("=== Per-function check ===")
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        local_defined = set(defined) | {node.name}
        # function parameters
        for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
            local_defined.add(arg.arg)
        if node.args.vararg:
            local_defined.add(node.args.vararg.arg)
        if node.args.kwarg:
            local_defined.add(node.args.kwarg.arg)

        # find local assigns
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Name):
                        local_defined.add(tgt.id)
            elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                for n in sub.names:
                    local_defined.add(n.asname or n.name)

        fn_undefined = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                if sub.id not in local_defined:
                    fn_undefined.append((sub.lineno, sub.col_offset, sub.id))

        if fn_undefined:
            print(f"  {node.name}() at L{node.lineno}: {len(fn_undefined)} unresolved refs")
            # only print first 3 for brevity
            for ln, c, name in fn_undefined[:3]:
                print(f"    L{ln}:{c} {name}")
