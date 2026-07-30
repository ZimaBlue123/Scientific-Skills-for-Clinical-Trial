"""Append a Windows-only convert_doc_to_docx() helper to scripts/common_scripts/docx_utils.py."""
from pathlib import Path

p = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\scripts\common_scripts\docx_utils.py")
src = p.read_text(encoding="utf-8")

NEW_BLOCK = '''


# -----------------------------------------------------------------------------
# Legacy .doc -> .docx conversion (Windows-only, formerly scripts/convert_doc_to_docx.py)
# -----------------------------------------------------------------------------
def convert_doc_to_docx(input_path, output_path=None):
    """Convert a legacy Word ``.doc`` file to ``.docx`` via Word COM.

    Windows-only. Requires ``pywin32``. Returns the output path as a
    ``pathlib.Path``. On Linux/macOS returns ``None`` and logs an error.

    Parameters
    ----------
    input_path : str | os.PathLike
        Path to the input ``.doc`` file.
    output_path : str | os.PathLike | None
        Target ``.docx`` path. If ``None`` the helper writes alongside
        the input file with the same stem.
    """
    try:
        import os as _os
        import win32com.client  # type: ignore[import-not-found]
        import pythoncom  # type: ignore[import-not-found]
    except ImportError:
        logger.error(
            "convert_doc_to_docx requires pywin32 on Windows; "
            "module unavailable in this environment."
        )
        return None

    import os as _os  # local alias keeps the rest of this function self-contained

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        try:
            word = win32com.client.Dispatch("Word.Application")
        except Exception as exc:  # noqa: BLE001
            logger.error("failed to launch Word.Application: %s", exc)
            return None
        word.Visible = False
        if output_path is None:
            output_path = _os.path.splitext(str(input_path))[0] + ".docx"
        try:
            doc = word.Documents.Open(_os.path.abspath(str(input_path)))
            doc.SaveAs(_os.path.abspath(str(output_path)), 16)  # 16 = wdFormatXMLDocument
        except Exception as exc:  # noqa: BLE001
            logger.error("COM error converting %s: %s", input_path, exc)
            return None
        finally:
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:  # noqa: BLE001
                    logger.debug("doc.Close raised", exc_info=True)
        return Path(str(output_path))
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:  # noqa: BLE001
                logger.debug("word.Quit raised", exc_info=True)
        try:
            pythoncom.CoUninitialize()
        except Exception:  # noqa: BLE001
            logger.debug("pythoncom.CoUninitialize raised", exc_info=True)


__all__ = [
    "apply_cn_en_fonts",
    "_apply_cn_en_fonts",
    "convert_doc_to_docx",
]
'''

# Replace old __all__ block with new one
OLD_ALL = '__all__ = ["apply_cn_en_fonts", "_apply_cn_en_fonts"]\n'
assert OLD_ALL in src, "OLD_ALL not found"
src = src.replace(OLD_ALL, NEW_BLOCK)
p.write_text(src, encoding="utf-8")
print(f"Appended convert_doc_to_docx() helper, new size: {p.stat().st_size} bytes")