"""
Clinical MCP Server — JSON-RPC 2.0 over stdio.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from .resources.registry import RESOURCE_DEFINITIONS, handle_resource_read
from .tools import TOOL_DEFINITIONS

log = logging.getLogger("clinical.mcp.server")

def _ok(request_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}

def _err(request_id: Any, code: int, message: str, data: Any = None) -> dict:
    error: dict = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}

_PARSE_ERROR = -32700
_METHOD_NOT_FOUND = -32601
_INVALID_PARAMS = -32602
_INTERNAL_ERROR = -32603

_TOOL_INDEX: dict[str, dict] = {t["name"]: t for t in TOOL_DEFINITIONS}

class UnknownToolError(Exception):
    pass

def call_tool(name: str, arguments: dict) -> dict:
    tool = _TOOL_INDEX.get(name)
    if tool is None:
        raise UnknownToolError(f"Unknown tool: {name}")
    return tool["_handler"](arguments)

def _handle_initialize(req_id: Any, params: dict) -> dict:
    return _ok(req_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {},
        },
        "serverInfo": {
            "name": "clinical-trial-mcp",
            "version": "0.1.0",
        },
    })

def _handle_tools_list(req_id: Any, _params: dict) -> dict:
    tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t["inputSchema"],
        }
        for t in TOOL_DEFINITIONS
    ]
    return _ok(req_id, {"tools": tools})

def _handle_tools_call(req_id: Any, params: dict) -> dict:
    name = params.get("name", "")
    args = params.get("arguments", {}) or {}

    try:
        result = call_tool(name, args)
    except UnknownToolError as exc:
        return _err(req_id, _METHOD_NOT_FOUND, str(exc))
    except Exception as exc:
        log.exception("Tool %s raised an exception", name)
        return _err(
            req_id, _INTERNAL_ERROR,
            f"Tool '{name}' failed ({type(exc).__name__}). See server logs for details.",
        )

    return _ok(req_id, {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
        "isError": "error" in result if isinstance(result, dict) else False,
    })

def _handle_resources_list(req_id: Any, _params: dict) -> dict:
    return _ok(req_id, {"resources": RESOURCE_DEFINITIONS})

def _handle_resources_read(req_id: Any, params: dict) -> dict:
    uri = params.get("uri", "").strip()
    if not uri:
        return _err(req_id, _INVALID_PARAMS, "uri is required")
    try:
        resource = handle_resource_read(uri)
        return _ok(req_id, {
            "contents": [
                {
                    "uri": resource["uri"],
                    "mimeType": resource.get("mimeType", "application/json"),
                    "text": resource.get("text", ""),
                }
            ]
        })
    except ValueError as exc:
        return _err(req_id, _INVALID_PARAMS, str(exc))
    except Exception as exc:
        return _err(req_id, _INTERNAL_ERROR, str(exc))

def _handle_ping(req_id: Any, _params: dict) -> dict:
    return _ok(req_id, {})

_DISPATCH = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
    "resources/list": _handle_resources_list,
    "resources/read": _handle_resources_read,
    "ping": _handle_ping,
}

class ClinicalMCPServer:
    def __init__(self, *, debug: bool = False) -> None:
        level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(stream=sys.stderr, level=level,
                            format="%(name)s %(levelname)s %(message)s")

    def dispatch(self, request: dict) -> dict | None:
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params") or {}

        handler = _DISPATCH.get(method)
        if handler is None:
            if req_id is None:
                return None
            return _err(req_id, _METHOD_NOT_FOUND, f"Method not found: {method}")

        try:
            return handler(req_id, params)
        except Exception as exc:
            log.exception("Unhandled error in method %s", method)
            if req_id is None:
                return None
            return _err(
                req_id, _INTERNAL_ERROR,
                f"Method '{method}' failed ({type(exc).__name__}). See server logs for details.",
            )

    def run(self) -> None:
        log.info("Clinical MCP server starting (stdio)")
        for raw_line in sys.stdin:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                request = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                response = _err(None, _PARSE_ERROR, f"Parse error: {exc}")
                _write(response)
                continue

            if isinstance(request, list):
                responses = []
                for req in request:
                    resp = self.dispatch(req)
                    if resp is not None:
                        responses.append(resp)
                if responses:
                    _write(responses)
            else:
                resp = self.dispatch(request)
                if resp is not None:
                    _write(resp)

def _write(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Clinical MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    ClinicalMCPServer(debug=args.debug).run()

if __name__ == "__main__":
    main()
