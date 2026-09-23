"""
Clinical Trial MCP Server Package
"""

import os

os.environ["CLINICAL_MCP_ACTIVE"] = "1"

from .server import ClinicalMCPServer, main

__all__ = ["ClinicalMCPServer", "main"]
