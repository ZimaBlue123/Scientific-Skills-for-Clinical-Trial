"""
Unified Document Facade (Inspired by Univer Architecture).
Abstracts python-docx and python-pptx into a unified Data Model Layer.
Provides a clean, deterministic API for AI Agents to manipulate documents
without dealing with underlying XML or format-specific quirks.
"""

import os

from docx import Document


class UnifiedDocument:
    def __init__(self, file_path):
        self.file_path = file_path
        self._doc = None
        self.doc_type = None
        self._load_document()

    def _load_document(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext == ".docx":
            self.doc_type = "docx"
            self._doc = Document(self.file_path)
        elif ext == ".pptx":
            self.doc_type = "pptx"
            # self._doc = Presentation(self.file_path) # Future implementation
            raise NotImplementedError("PPTX support in Facade coming soon.")
        else:
            raise ValueError(f"Unsupported document format: {ext}")

    def extract_text(self):
        """Returns all text from the document cleanly."""
        if self.doc_type == "docx":
            return "\n".join([p.text for p in self._doc.paragraphs if p.text.strip()])

    def replace_text(self, old_text, new_text):
        """Unified command to replace text while preserving run-level styles."""
        if self.doc_type == "docx":
            for p in self._doc.paragraphs:
                if old_text in p.text:
                    for run in p.runs:
                        if old_text in run.text:
                            run.text = run.text.replace(old_text, new_text)

    def extract_tables_as_dict(self):
        """Returns tables as a structured JSON-like dict for Agent consumption."""
        if self.doc_type == "docx":
            tables_data = []
            for i, table in enumerate(self._doc.tables):
                t_data = []
                for row in table.rows:
                    t_data.append([cell.text.strip() for cell in row.cells])
                tables_data.append({"table_index": i, "data": t_data})
            return tables_data

    def save(self, output_path):
        self._doc.save(output_path)
