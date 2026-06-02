#!/usr/bin/env python
"""Extract text from old .doc format using win32com"""
import sys
import os

def extract_doc(filepath):
    """Extract text from .doc file using COM interface"""
    import win32com.client
    import pythoncom
    
    # Initialize COM
    pythoncom.CoInitialize()
    
    try:
        # Open Word application
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        # Open the document
        doc = word.Documents.Open(os.path.abspath(filepath))
        
        # Extract text
        text = doc.Content.Text
        
        # Close document and quit Word
        doc.Close(False)
        word.Quit()
        
        return text
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_doc_text.py <input.doc>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    text = extract_doc(filepath)
    
    # Save to file with UTF-8 encoding
    output_path = filepath + ".txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text extracted to: {output_path}")