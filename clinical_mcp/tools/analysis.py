from ..schemas import CHECK_ENCODING, SELF_CHECK
from ..session import load_script_module

def _handle_check_encoding(args: dict) -> dict:
    module = load_script_module("analysis_tools")
    if hasattr(module, "check_encoding"):
        return {"result": module.check_encoding(args["file_path"])}
    return {"error": "check_encoding not implemented in scripts"}

def _handle_self_check(args: dict) -> dict:
    module = load_script_module("project_health")
    if hasattr(module, "run_self_check"):
        return {"result": module.run_self_check()}
    return {"error": "run_self_check not implemented in scripts"}

ANALYSIS_TOOLS = [
    {
        "name": "check_encoding",
        "description": "Diagnose encoding/mojibake",
        "inputSchema": CHECK_ENCODING,
        "_handler": _handle_check_encoding,
    },
    {
        "name": "self_check",
        "description": "Run project self-check",
        "inputSchema": SELF_CHECK,
        "_handler": _handle_self_check,
    },
]
