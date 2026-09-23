"""
Input schema definitions for all MCP tools.
"""

EXTRACT_PDF_TEXT = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the PDF file",
        }
    },
    "required": ["file_path"],
}

EXTRACT_DOCX_CONTENT = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the DOCX file",
        }
    },
    "required": ["file_path"],
}

CONVERT_DOCUMENT = {
    "type": "object",
    "properties": {
        "input_path": {
            "type": "string",
            "description": "Path to the input document",
        },
        "output_format": {
            "type": "string",
            "description": "Desired output format (e.g. pdf, docx)",
        }
    },
    "required": ["input_path", "output_format"],
}

SEARCH_PUBMED = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "PubMed search query",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 10,
        }
    },
    "required": ["query"],
}

GENERATE_CLINICAL_DOCX = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "Content or path to content for generating DOCX",
        },
        "output_path": {
            "type": "string",
            "description": "Output path for the DOCX file",
        }
    },
    "required": ["content", "output_path"],
}

VALIDATE_PPTX = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the PPTX file",
        }
    },
    "required": ["file_path"],
}

CHECK_ENCODING = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Path to the file to check",
        }
    },
    "required": ["file_path"],
}

RUN_SKILL_VALIDATION = {
    "type": "object",
    "properties": {
        "registry_path": {
            "type": "string",
            "description": "Path to the skills registry",
        }
    },
    "required": ["registry_path"],
}

DEDUPE_SKILLS = {
    "type": "object",
    "properties": {
        "registry_path": {
            "type": "string",
            "description": "Path to the skills registry",
        }
    },
    "required": ["registry_path"],
}

SELF_CHECK = {
    "type": "object",
    "properties": {},
}
