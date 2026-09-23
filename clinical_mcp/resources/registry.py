"""
Handlers for clinical:// URIs
"""
import json
from ..session import load_script_module

RESOURCE_DEFINITIONS = [
    {
        "uri": "clinical://skills/catalog",
        "name": "Skills Catalog",
        "description": "List all skills with categories",
        "mimeType": "application/json",
    },
    {
        "uri": "clinical://scripts/list",
        "name": "Scripts List",
        "description": "List available scripts",
        "mimeType": "application/json",
    },
    {
        "uri": "clinical://project/health",
        "name": "Project Health",
        "description": "Project health summary",
        "mimeType": "application/json",
    },
    {
        "uri": "clinical://schema/info",
        "name": "Schema Info",
        "description": "Server schema info",
        "mimeType": "application/json",
    },
]

def _handle_skills_catalog() -> dict:
    return {"text": json.dumps({"status": "not implemented"})}

def _handle_scripts_list() -> dict:
    return {"text": json.dumps({"status": "not implemented"})}

def _handle_project_health() -> dict:
    return {"text": json.dumps({"status": "not implemented"})}

def _handle_schema_info() -> dict:
    return {"text": json.dumps({"status": "not implemented"})}

_HANDLERS = {
    "clinical://skills/catalog": _handle_skills_catalog,
    "clinical://scripts/list": _handle_scripts_list,
    "clinical://project/health": _handle_project_health,
    "clinical://schema/info": _handle_schema_info,
}

def handle_resource_read(uri: str) -> dict:
    handler = _HANDLERS.get(uri)
    if not handler:
        raise ValueError(f"Unknown resource URI: {uri}")
    
    result = handler()
    result["uri"] = uri
    result["mimeType"] = "application/json"
    return result
