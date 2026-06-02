# -*- coding: utf-8 -*-
"""
Extract text from docx/doc files.
Supports single file, multiple files, or all files in a folder.
Handles both modern .docx and legacy .doc formats.

Usage:
    # Single file
    py -3 scripts/extract_docx_full.py document.docx [output.txt]
    
    # Folder batch (all docx/doc files to combined output)
    py -3 scripts/extract_docx_full.py folder/ [output.txt]
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Optional


def extract_docx(filepath: Path) -> str:
    """Extract all text from docx using python-docx."""
    from docx import Document
    doc = Document(str(filepath))
    full_text = []
    
    # Extract paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    
    # Extract tables
    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text.strip():
                    row_text.append(cell.text.strip())
            if row_text:
                full_text.append(' | '.join(row_text))
    
    return '\n\n'.join(full_text)


def extract_doc_legacy(filepath: Path) -> Optional[str]:
    """Extract text from legacy .doc using Word COM (Windows only)."""
    try:
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(filepath))
            text = doc.Content.Text
            doc.Close(False)
            word.Quit()
            return text
        finally:
            pythoncom.CoUninitialize()
    except ImportError:
        print("    [win32com not available - cannot extract .doc files]", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    [COM error] {e}", file=sys.stderr)
        return None


def extract_file(filepath: Path) -> Optional[str]:
    """Extract text from a single file based on extension."""
    suffix = filepath.suffix.lower()
    
    if suffix == '.docx':
        return extract_docx(filepath)
    elif suffix == '.doc':
        return extract_doc_legacy(filepath)
    else:
        print(f"Unsupported format: {suffix}", file=sys.stderr)
        return None


def extract_folder(folder_path: Path, output_path: Optional[Path] = None) -> str:
    """
    Extract text from all docx/doc files in a folder.
    Outputs to a single combined file or returns combined text.
    """
    files = [f for f in os.listdir(folder_path) 
             if f.endswith('.docx') or f.lower().endswith('.doc')]
    
    combined = []
    combined.append(f'Found {len(files)} files\n')
    
    for fname in files:
        path = Path(folder_path) / fname
        combined.append(f'\n========== {fname} ==========\n')
        try:
            text = extract_file(path)
            if text:
                combined.append(text)
            else:
                combined.append('[FAILED to extract content]')
        except Exception as e:
            combined.append(f'Error: {e}')
        combined.append('\n')
    
    result = '\n'.join(combined)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f'Extracted {len(files)} files to: {output_path}')
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_docx_full.py <input.docx|folder> [output.txt]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    input_p = Path(input_path)
    
    if input_p.is_dir():
        out_p = Path(output_path) if output_path else None
        extract_folder(input_p, out_p)
    else:
        try:
            text = extract_file(input_p)
            if text:
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f'Extracted to: {output_path}')
                else:
                    print(text)
            else:
                print("Failed to extract content", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
