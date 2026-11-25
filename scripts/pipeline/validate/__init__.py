"""Validation stage: content and robustness checkers."""

from .ast_validator import check_robustness_smells
from .docx_clean_validator import check_docx
from .docx_toc_validator import verify as verify_docx_toc
from .encoding_validator import check_bom, diagnose_encoding
from .pptx_overflow_checker import check_pptx_overflow
from .pptx_slop_detector import SlopFinding, scan_pptx_slop, summarize_slop
from .pptx_validator import check_overflow, find_overflow_slides

__all__ = [
    "check_overflow",
    "find_overflow_slides",
    "check_pptx_overflow",
    "SlopFinding",
    "scan_pptx_slop",
    "summarize_slop",
    "diagnose_encoding",
    "check_bom",
    "check_robustness_smells",
    "check_docx",
    "verify_docx_toc",
]
