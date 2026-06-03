# -*- coding: utf-8 -*-
"""
Unified document converter: Convert docx/doc/pdf/rtf to markdown.
Supports batch folder conversion or single file conversion.

Usage:
    # Single file (standard markdown)
    py -3 scripts/convert_to_md.py input.docx -o output.md
    
    # Single file with numbered paragraphs/tables (##P1, ##T1 markers)
    py -3 scripts/convert_to_md.py input.docx -o output.md --mode numbered
    
    # Batch folder
    py -3 scripts/convert_to_md.py --folder review_materials -o review_materials/converted
    
    # As module
    from convert_to_md import convert_file, convert_folder
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Optional

# Try markitdown for better conversion (optional)
_markitdown = None
def _get_markitdown():
    global _markitdown
    if _markitdown is None:
        try:
            from markitdown import MarkItDown
            _markitdown = MarkItDown()
        except ImportError:
            _markitdown = False
    return _markitdown


def _convert_docx_basic(filepath: Path) -> Optional[str]:
    """Fallback: basic docx to text using python-docx"""
    try:
        from docx import Document
        doc = Document(str(filepath))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n\n".join(parts) if parts else None
    except Exception as e:
        print(f"    [python-docx] {e}", file=sys.stderr)
        return None


def _convert_pdf_basic(filepath: Path) -> Optional[str]:
    """Fallback: basic pdf to text using pypdf"""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(filepath))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages).strip() or None
    except ImportError:
        try:
            import pdfplumber
            with pdfplumber.open(str(filepath)) as pdf:
                return "\n\n".join((p.extract_text() or "") for p in pdf.pages).strip() or None
        except Exception as e:
            print(f"    [pdfplumber] {e}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"    [pypdf] {e}", file=sys.stderr)
        return None


# =============================================================================
# Numbered mode functions (from extract_docx_to_md.py)
# =============================================================================

def _clean_cell_text(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def table_to_md(table, max_cols: Optional[int] = None) -> str:
    """Convert a docx Table to markdown format."""
    rows: List[List[str]] = []
    for row in table.rows:
        cells = [_clean_cell_text(cell.text) for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ""

    ncol = max(len(r) for r in rows)
    if max_cols is not None:
        ncol = min(ncol, max_cols)

    norm: List[List[str]] = []
    for r in rows:
        r2 = (r + [""] * (ncol - len(r)))[:ncol]
        norm.append(r2)

    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []

    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * ncol) + " |",
    ]
    for r in body:
        md_lines.append("| " + " | ".join(r) + " |")
    return "\n".join(md_lines)


def iter_block_items(doc) -> Iterable[Tuple[str, object]]:
    """
    Yield ('p', Paragraph) and ('tbl', Table) in document order.
    """
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    
    body = doc.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield ("p", Paragraph(child, doc))
        elif isinstance(child, CT_Tbl):
            yield ("tbl", Table(child, doc))


def docx_to_md_numbered(src_path: Path, max_cols: Optional[int] = None) -> str:
    """
    Convert docx to markdown with numbered paragraphs (##P{n}) and tables (##T{n}).
    Useful for precise content location in documents.
    """
    from docx import Document
    doc = Document(str(src_path))

    out: List[str] = []
    out.append(f"# Source: {src_path.name}")
    out.append("")

    para_idx = 0
    table_idx = 0

    for kind, item in iter_block_items(doc):
        if kind == "p":
            p = item
            text = " ".join(p.text.split())
            if not text:
                continue
            para_idx += 1
            out.append(f"## P{para_idx}")
            out.append(text)
            out.append("")
        else:
            t = item
            md = table_to_md(t, max_cols=max_cols)
            if not md.strip():
                continue
            table_idx += 1
            out.append(f"## T{table_idx}")
            out.append(md)
            out.append("")

    return "\n".join(out).rstrip() + "\n"


# =============================================================================
# Main conversion functions
# =============================================================================

def convert_file(src: Path, output_path: Optional[Path] = None, 
                 mode: str = "standard", max_cols: Optional[int] = None) -> Optional[Path]:
    """
    Convert a single file to markdown.
    Supports: .docx, .pdf, .rtf, .doc
    
    Args:
        src: Source file path
        output_path: Output markdown path (optional)
        mode: Output mode - "standard" (default) or "numbered" (##P1/##T1 markers)
        max_cols: Max columns for table rendering (numbered mode only)
    
    Returns:
        Output path if successful, None otherwise.
    """
    if not src.exists() or not src.is_file():
        print(f"File not found: {src}", file=sys.stderr)
        return None
    
    suffix = src.suffix.lower()
    if suffix not in {".docx", ".pdf", ".rtf", ".doc"}:
        print(f"Unsupported format: {suffix}", file=sys.stderr)
        return None
    
    content = None
    
    # Special handling for numbered mode with docx
    if mode == "numbered" and suffix == ".docx":
        try:
            content = docx_to_md_numbered(src, max_cols=max_cols)
        except Exception as e:
            print(f"    [numbered mode] {e}", file=sys.stderr)
            # Fall back to standard mode
            content = None
    
    # Standard mode or fallback
    if not content:
        # Try markitdown first (best quality)
        md = _get_markitdown()
        if md:
            try:
                if suffix == ".rtf":
                    from striprtf.striprtf import rtf_to_text
                    text = rtf_to_text(src.read_text(encoding="utf-8", errors="ignore")).strip()
                    content = text
                else:
                    result = md.convert(str(src))
                    content = (result.text_content or "").strip()
            except Exception as e:
                print(f"    [markitdown] {e}", file=sys.stderr)
        
        # Fallback to basic converters
        if not content:
            if suffix == ".docx":
                content = _convert_docx_basic(src)
            elif suffix == ".pdf":
                content = _convert_pdf_basic(src)
            elif suffix == ".rtf":
                try:
                    from striprtf.striprtf import rtf_to_text
                    content = rtf_to_text(src.read_text(encoding="utf-8", errors="ignore")).strip()
                except Exception as e:
                    print(f"    [striprtf] {e}", file=sys.stderr)
            elif suffix == ".doc":
                print("    [.doc format requires Word COM - skipping]", file=sys.stderr)
    
    if not content or not content.strip():
        print(f"    [FAILED] Could not extract content")
        return None
    
    # Determine output path
    if output_path is None:
        output_path = src.with_suffix(".md")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"OK: {src.name} -> {output_path.name}")
    return output_path


def convert_folder(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    extensions: Optional[set] = None,
    mode: str = "standard",
    max_cols: Optional[int] = None
) -> list[Path]:
    """
    Convert all supported files in a folder to markdown.
    
    Args:
        input_dir: Input folder containing documents
        output_dir: Output folder for markdown files (default: input_dir/converted)
        extensions: Set of file extensions to process (default: {".docx", ".pdf", ".rtf"})
        mode: Output mode - "standard" or "numbered"
        max_cols: Max columns for table rendering (numbered mode only)
    
    Returns:
        List of created markdown file paths
    """
    if extensions is None:
        extensions = {".docx", ".pdf", ".rtf"}
    
    if output_dir is None:
        output_dir = input_dir / "converted"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    created = []
    skipped = []
    
    for f in sorted(input_dir.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in extensions:
            continue
        
        out_name = f.stem
        # Sanitize filename
        for c in '\\/:*?"<>|':
            out_name = out_name.replace(c, "_")
        out_path = output_dir / (out_name + ".md")
        
        result = convert_file(f, out_path, mode=mode, max_cols=max_cols)
        if result:
            created.append(result)
        else:
            skipped.append(f.name)
    
    print(f"\n--- Summary ---")
    print(f"Converted: {len(created)}")
    print(f"Skipped/Failed: {len(skipped)}")
    if skipped:
        print(f"Skipped files: {', '.join(skipped)}")
    
    return created


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert documents (docx/pdf/rtf) to markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file (standard markdown)
  py -3 scripts/convert_to_md.py document.docx -o output.md
  
  # Single file with numbered paragraphs (##P1, ##T1 markers)
  py -3 scripts/convert_to_md.py document.docx -o output.md --mode numbered
  
  # Batch folder (default output: folder/converted)
  py -3 scripts/convert_to_md.py --folder review_materials
  
  # Custom output folder
  py -3 scripts/convert_to_md.py --folder review_materials -o markdown_output/
        """
    )
    parser.add_argument("input", nargs="?", help="Input file or folder")
    parser.add_argument("--folder", "-f", help="Input folder (alternative to positional)")
    parser.add_argument("-o", "--output", help="Output file or folder")
    parser.add_argument("--extensions", default=".docx,.pdf,.rtf", 
                        help="Comma-separated extensions to process (default: .docx,.pdf,.rtf)")
    parser.add_argument("--mode", "-m", default="standard",
                        choices=["standard", "numbered"],
                        help="Output mode: standard (default) or numbered (##P1/##T1 markers)")
    parser.add_argument("--max-cols", type=int, default=None,
                        help="Max columns when rendering tables (numbered mode only)")
    
    args = parser.parse_args()
    
    # Get input path
    input_path = None
    if args.input:
        input_path = Path(args.input)
    elif args.folder:
        input_path = Path(args.folder)
    else:
        # Default to review_materials relative to script
        input_path = Path(__file__).resolve().parents[1] / "review_materials"
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1
    
    # Parse extensions
    extensions = set(args.extensions.split(","))
    
    # Determine output
    output_path = Path(args.output) if args.output else None
    
    if input_path.is_file():
        result = convert_file(input_path, output_path, mode=args.mode, max_cols=args.max_cols)
        return 0 if result else 1
    else:
        results = convert_folder(input_path, output_path, extensions, mode=args.mode, max_cols=args.max_cols)
        return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
