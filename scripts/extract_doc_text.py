#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract plain text from legacy Microsoft Word `.doc` files via the
Windows-only Win32 COM interface (Word.Application).

This script is intentionally defensive: COM resources are released in a
`finally` block, and the user is given a clear error message when
`pywin32` is missing or Word is not installed.

Usage
-----
    py -3 scripts/extract_doc_text.py <input.doc> [-o <output.txt>]

If `-o` is omitted, the output is written next to the input as
``<input>.doc.txt`` (matching the legacy convention).
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

LOG_FORMAT = "%(asctime)s [%(levelname)s] extract_doc_text: %(message)s"
logger = logging.getLogger("extract_doc_text")


def _format_err(prefix: str, exc: BaseException) -> str:
    return f"{prefix}: {type(exc).__name__}: {exc}"


def extract_doc_text(filepath: Path) -> str:
    """Open ``filepath`` in Word (COM) and return its full text content.

    Raises
    ------
    ImportError
        When ``pywin32`` (win32com / pythoncom) is not importable.
    FileNotFoundError
        When ``filepath`` does not exist or is not a regular file.
    RuntimeError
        When Word fails to open or read the document.
    """
    if not filepath.exists() or not filepath.is_file():
        raise FileNotFoundError(f"input file not found: {filepath}")

    try:
        import win32com.client  # type: ignore[import-not-found]
        import pythoncom  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - platform specific
        raise ImportError(
            "pywin32 is required to read legacy .doc files. "
            "Install via: python -m pip install pywin32"
        ) from exc

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        try:
            word = win32com.client.Dispatch("Word.Application")
        except Exception as exc:  # noqa: BLE001 - COM errors are heterogeneous
            raise RuntimeError(
                "failed to launch Word.Application. Ensure Microsoft Word "
                "is installed and accessible."
            ) from exc

        word.Visible = False
        # Word.Application.Documents.Open raises COMErrors for invalid files;
        # we surface them as RuntimeError with a clean message.
        try:
            doc = word.Documents.Open(str(filepath.resolve()))
            return str(doc.Content.Text or "")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"failed to read content from {filepath}"
            ) from exc
        finally:
            # Always close the document (if it was opened) before quitting Word.
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:  # noqa: BLE001
                    logger.debug("doc.Close raised", exc_info=True)
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


def _default_output_path(input_path: Path) -> Path:
    """Return ``<input>.doc.txt`` next to the source file."""
    return input_path.with_suffix(input_path.suffix + ".txt")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_doc_text",
        description="Extract plain text from legacy .doc files using Win32 COM.",
    )
    parser.add_argument("input", type=Path, help="Input .doc file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output .txt path (default: <input>.doc.txt next to source)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity (default: %(default)s)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format=LOG_FORMAT)

    input_path: Path = args.input
    output_path: Path = args.output or _default_output_path(input_path)

    try:
        text = extract_doc_text(input_path)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 2
    except ImportError as e:
        logger.error("%s", e)
        return 2
    except RuntimeError as e:
        logger.error("%s", _format_err("Word COM error", e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.exception("unexpected error: %s", e)
        return 1

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    except OSError as e:
        logger.error("failed to write %s: %s", output_path, e)
        return 1

    logger.info("extracted %d chars to %s", len(text), output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())