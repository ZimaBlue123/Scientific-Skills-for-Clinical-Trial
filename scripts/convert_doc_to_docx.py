#!/usr/bin/env python
"""Convert old .doc to .docx format"""
import sys
import os
import win32com.client
import pythoncom

def convert_doc_to_docx(input_path, output_path=None):
    """Convert .doc to .docx using Word COM"""
    pythoncom.CoInitialize()
    
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        # Open the document
        doc = word.Documents.Open(os.path.abspath(input_path))
        
        # Determine output path
        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + ".docx"
        
        # Save as docx
        doc.SaveAs(os.path.abspath(output_path), 16)  # 16 = wdFormatXMLDocument (docx)
        doc.Close(False)
        word.Quit()
        
        return output_path
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_doc_to_docx.py <input.doc> [output.docx]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = convert_doc_to_docx(input_path, output_path)
    print(f"Converted to: {result}")