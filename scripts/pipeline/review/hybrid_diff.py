# -*- coding: utf-8 -*-
"""
Hybrid Review Diffing Module (Inspired by Alibaba open-code-review).
Generates deterministic, precise paragraph-level diffs between two clinical docs.
Provides numbered context for the LLM to prevent "position drift" hallucinations.
"""

import difflib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from pipeline.document_facade import UnifiedDocument

def generate_numbered_diff(doc1_path, doc2_path):
    """
    Extracts text from both documents and creates a line-numbered diff.
    The LLM uses this output to specify EXACT lines for QA flags.
    """
    doc1 = UnifiedDocument(doc1_path)
    doc2 = UnifiedDocument(doc2_path)
    
    text1 = doc1.extract_text().splitlines()
    text2 = doc2.extract_text().splitlines()
    
    # Filter empty lines for clinical review relevance
    text1 = [line for line in text1 if line.strip()]
    text2 = [line for line in text2 if line.strip()]
    
    differ = difflib.ndiff(text1, text2)
    
    diff_output = []
    line_num = 1
    
    for line in differ:
        # Ignore unchanged lines for brevity, or include them for context
        if line.startswith('- '):
            diff_output.append(f"[DEL L{line_num}] {line[2:]}")
        elif line.startswith('+ '):
            diff_output.append(f"[ADD L{line_num}] {line[2:]}")
            line_num += 1
        elif line.startswith('  '):
            # Unchanged context
            line_num += 1
            
    return "\n".join(diff_output)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        diff_res = generate_numbered_diff(sys.argv[1], sys.argv[2])
        print(diff_res)
    else:
        print("Usage: python hybrid_diff.py <v1.docx> <v2.docx>")
