from ..schemas import EXTRACT_PDF_TEXT, EXTRACT_DOCX_CONTENT, CONVERT_DOCUMENT, GENERATE_CLINICAL_DOCX
from ..session import load_script_module

def _handle_extract_pdf_text(args: dict) -> dict:
    # Example logic, assumes a script `scripts/document_tools/pdf_extractor.py` or similar
    module = load_script_module("pdf_tools") # or wherever extract_pdf_text lives
    if hasattr(module, "extract_pdf_text"):
        return {"text": module.extract_pdf_text(args["file_path"])}
    return {"error": "extract_pdf_text not implemented in scripts"}

def _handle_extract_docx_content(args: dict) -> dict:
    module = load_script_module("docx_tools")
    if hasattr(module, "extract_docx_content"):
        return {"text": module.extract_docx_content(args["file_path"])}
    return {"error": "extract_docx_content not implemented in scripts"}

def _handle_convert_document(args: dict) -> dict:
    module = load_script_module("document_converter")
    if hasattr(module, "convert_document"):
        return {"result": module.convert_document(args["input_path"], args["output_format"])}
    return {"error": "convert_document not implemented in scripts"}

def _handle_generate_clinical_docx(args: dict) -> dict:
    module = load_script_module("docx_generator")
    if hasattr(module, "generate_clinical_docx"):
        return {"result": module.generate_clinical_docx(args["content"], args["output_path"])}
    return {"error": "generate_clinical_docx not implemented in scripts"}

DOCUMENT_TOOLS = [
    {
        "name": "extract_pdf_text",
        "description": "Extract text from PDF file",
        "inputSchema": EXTRACT_PDF_TEXT,
        "_handler": _handle_extract_pdf_text,
    },
    {
        "name": "extract_docx_content",
        "description": "Extract text from Word DOCX",
        "inputSchema": EXTRACT_DOCX_CONTENT,
        "_handler": _handle_extract_docx_content,
    },
    {
        "name": "convert_document",
        "description": "Convert between document formats",
        "inputSchema": CONVERT_DOCUMENT,
        "_handler": _handle_convert_document,
    },
    {
        "name": "generate_clinical_docx",
        "description": "Generate clinical report DOCX",
        "inputSchema": GENERATE_CLINICAL_DOCX,
        "_handler": _handle_generate_clinical_docx,
    },
]
