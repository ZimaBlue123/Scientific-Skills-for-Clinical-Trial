"""
Shared session / module loader logic.
"""
import sys
import os

_scripts_added = False

def get_scripts_path() -> str:
    global _scripts_added
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(base_dir, "scripts")
    
    if not _scripts_added:
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        _scripts_added = True
    return scripts_dir

def load_script_module(module_name: str):
    get_scripts_path()
    import importlib
    return importlib.import_module(module_name)
