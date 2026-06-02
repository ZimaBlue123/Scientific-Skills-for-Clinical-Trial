# -*- coding: utf-8 -*-
"""
Unified document converter: Convert docx/doc/pdf/rtf to markdown.
Supports batch folder conversion or single file conversion.

Usage:
    # Single file
    py -3 scripts/convert_to_md.py input.docx -o output.md
    
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
from typing import Optional

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


def convert_file(src: Path, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Convert a single file to markdown.
    Supports: .docx, .pdf, .rtf, .doc
    
    Returns output path if successful, None otherwise.
    """
    if not src.exists() or not src.is_file():
        print(f"File not found: {src}", file=sys.stderr)
        return None
    
    suffix = src.suffix.lower()
    if suffix not in {".docx", ".pdf", ".rtf", ".doc"}:
        print(f"Unsupported format: {suffix}", file=sys.stderr)
        return None
    
    content = None
    
    # Try markitdown first (best quality)
    md = _get_markitdown()
    if md:
        try:
            if suffix == ".rtf":
                # markitdown may not handle RTF well, use striprtf
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
            # Old .doc format - needs Word COM, can't handle without win32
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
    extensions: Optional[set] = None
) -> list[Path]:
    """
    Convert all supported files in a folder to markdown.
    
    Args:
        input_dir: Input folder containing documents
        output_dir: Output folder for markdown files (default: input_dir/converted)
        extensions: Set of file extensions to process (default: {".docx", ".pdf", ".rtf"})
    
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
        
        result = convert_file(f, out_path)
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
  # Single file
  py -3 scripts/convert_to_md.py document.docx -o output.md
  
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
        result = convert_file(input_path, output_path)
        return 0 if result else 1
    else:
        results = convert_folder(input_path, output_path, extensions)
        return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
