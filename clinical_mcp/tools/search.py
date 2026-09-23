from ..schemas import SEARCH_PUBMED
from ..session import load_script_module

def _handle_search_pubmed(args: dict) -> dict:
    module = load_script_module("literature_tools.pubmed_search_tool")
    if hasattr(module, "search_pubmed"):
        max_results = args.get("max_results", 10)
        return {"results": module.search_pubmed(args["query"], max_results=max_results)}
    return {"error": "search_pubmed not implemented in scripts/literature_tools/pubmed_search_tool.py"}

SEARCH_TOOLS = [
    {
        "name": "search_pubmed",
        "description": "Search PubMed literature",
        "inputSchema": SEARCH_PUBMED,
        "_handler": _handle_search_pubmed,
    }
]
