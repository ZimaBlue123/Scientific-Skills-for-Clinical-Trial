"""Document-to-Markdown conversion stage of the pipeline.

The canonical entry point is :mod:`scripts.pipeline.convert.convert_to_md`, a CLI
module that converts docx / pdf / rtf / doc inputs into Markdown — optionally with
numbered paragraph and table markers consumed by downstream extraction steps.

The submodule is **not** imported eagerly here: importing it pulls in heavy,
optional third-party dependencies (``python-docx``, ``pypdf``, ``markitdown``)
that most pipeline callers never need. Import it explicitly::

    from scripts.pipeline.convert import convert_to_md
    convert_to_md.convert_file(Path("input.docx"))
"""

from __future__ import annotations

__all__: list[str] = []
