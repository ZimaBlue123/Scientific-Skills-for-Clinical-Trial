#!/usr/bin/env python3
"""
One-shot helper: append a 'Section 7: Supplementary notes' block to
``review_report.md``.

NOTE: marked as a *one-shot* utility. After running this script exactly
once you can remove it — it is not part of the regular toolchain. Kept
here for audit traceability of the source-of-truth written on 2026-07-21.

Usage
-----
    py -3 append_supplement.py [-t TARGET]

Exit codes
----------
    0  appended
    1  already present (no-op)
    2  I/O error
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logger = logging.getLogger("append_supplement")

DEFAULT_TARGET = Path(
    r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_report.md"
)

SUPPLEMENT_MARKER = "## 七、补充说明（基于进一步审阅）"

SUPPLEMENT_BODY = """

---

## 七、补充说明（基于进一步审阅）

### 关于"首剂免后 60 天免疫原性采血缺失"一项

- 4 条方案偏离/违背中，此条仅描述事件，未列出受试者编号与日期。
- 建议：附录或下一版 MR 中为每条偏离项补充受试者 ID 与发生日期。

### 关于"前次报告"（MMR 2）的依托

- 多处引用"较前次报告无变化"、"较前次报告无变更"、"MMR2-表 2"，但本文为 MMR 3，未提供 MMR 1/2 的文档编号。
- 建议：在附录中补入前次报告的引用列号或页码。

### 关于进展报告与 EDC 数据的滞后

- 项目进展报告截至 2026-04-13，比 EDC 数据截止 2026-07-13 延迟 3 个月。
- 建议：未来 MMR 中落实定期同步进展报告口径。

### 关于脚本安全

- `verify_data.py` 与 `extract_review_doc_stdlib.py` 仅读取文件、不修改原 docx，可在锁库前反复运行。
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append supplementary notes to review_report.md."
    )
    parser.add_argument(
        "-t",
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Target markdown file (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=LOG_FORMAT,
    )

    if not args.target.exists():
        logger.error("target file does not exist: %s", args.target)
        return 2

    try:
        text = args.target.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("failed to read %s: %s", args.target, exc)
        return 2

    if SUPPLEMENT_MARKER in text:
        logger.info("supplement already present, skipping")
        return 1

    try:
        args.target.write_text(text + SUPPLEMENT_BODY, encoding="utf-8")
    except OSError as exc:
        logger.error("failed to write %s: %s", args.target, exc)
        return 2

    logger.info("appended %d chars to %s", len(SUPPLEMENT_BODY.strip()), args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
