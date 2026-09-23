"""Apply the 2026-09-18 review comments as a Word track-changes ("痕迹版") revision.

The starting point is the already-updated minutes

    review_materials/15-F2F会议/Minutes/
        TVAX-009 III期临床试验启动前沟通会（EoP2）线上会议纪要-2026年9月18日-updated.docx

and every requested edit is written as a **tracked revision** rather than a plain
edit, so that Word shows "删除原文 + 插入新文" and the recipient can accept or
reject each change one by one.

How it works
------------
Word itself is never launched. The script builds the OOXML revision nodes:

* the original runs of a paragraph are wrapped in ``<w:del>`` and their ``<w:t>``
  nodes are retagged as ``<w:delText>`` (this is what renders as strikethrough);
* a brand new ``<w:ins>`` run carrying the replacement text is appended, cloning
  the run properties of the first original run so the inserted text inherits the
  document typography.

Both elements carry the mandatory ``w:id`` / ``w:author`` / ``w:date`` triple.

Usage
-----
    python scripts/generators/revise_cde_eop2_meeting_minutes_trackchanges.py
"""

from __future__ import annotations

import copy
import logging
import sys
from datetime import datetime, timezone
from itertools import count
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from docx import Document  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

LOG_FORMAT = "%(asctime)s [%(levelname)s] track_changes: %(message)s"
logger = logging.getLogger("track_changes")

MINUTES_DIR = ROOT / "review_materials" / "15-F2F会议" / "Minutes"
BASENAME = "TVAX-009 III期临床试验启动前沟通会（EoP2）线上会议纪要-2026年9月18日"

SOURCE = MINUTES_DIR / f"{BASENAME}-updated.docx"
OUTPUT = MINUTES_DIR / f"痕迹版-{BASENAME}-updated.docx"

AUTHOR = "Rock Lee"
REVISION_DATE = "2026-09-18T22:30:00Z"

# (label, exact original paragraph text, replacement text)
REVISIONS: list[tuple[str, str, str]] = [
    (
        "一、会议目的：删除多余的'种'字",
        "一、会议目的：就本品种Ⅲ期临床试验设计的完善进行沟通，"
        "落实2026年9月16日Ⅲ期临床试验启动前沟通会（EoP2）专家面对面会议的相关意见。",
        "一、会议目的：就本品Ⅲ期临床试验设计的完善进行沟通，"
        "落实2026年9月16日Ⅲ期临床试验启动前沟通会（EoP2）专家面对面会议的相关意见。",
    ),
    (
        "问题2 共同观点：改为免疫规划年代背景表述",
        "共同观点：本研究人群聚焦于无乙肝疫苗接种史成人。申请人需收集国内乙肝无接种史人群的"
        "流行病学调查数据，确保研究人群的年龄构成与真实世界中无接种史人群的年龄构成保持一致，"
        "以保障研究人群的代表性。",
        "共同观点：本临床研究应充分考虑乙肝免疫规划实施年代背景，18-25岁人群基本均有接种史，"
        "25岁以上人群既往接种史构成目前未明确，申请人需收集、调研，确保本研究人群的代表性。",
    ),
    (
        "问题4 问题描述：补入2026年9月16日专家面对面会议背景",
        "问题4：关于老年人群数据：Ⅱ期临床试验中60岁以上人群两剂接种后的免疫原性数据有限，"
        "两剂接种有效性方面申请人自行评估。如果60岁以上人群做三剂接种要优效于阳性对照。",
        "问题4：关于老年人群数据：2026年9月16日Ⅲ期临床试验启动前沟通会（EoP2）专家面对面会议上，"
        "专家提出60岁以上老年人群可采用两剂接种程序；本次会议提醒申请人关注Ⅱ期临床试验中"
        "60岁以上人群两剂接种后的免疫原性数据有限，两剂接种有效性方面由申请人自行评估；"
        "若60岁以上人群采用三剂接种，需优效于阳性对照。",
    ),
    (
        "问题5 问题描述：终点明确为免前阴性人群阳转率",
        "问题5：关于主要终点：Ⅲ期临床试验的主要终点及其评价时间点应设置为"
        "全程免疫后相同时间点的阳转率。",
        "问题5：关于主要终点：Ⅲ期临床试验的主要终点及其评价时间点应设置为"
        "全程免疫后相同时间点的免前阴性人群阳转率。",
    ),
    (
        "问题5 共同观点：明确阳性对照时间点与试验组拉齐",
        "共同观点：主要终点为抗体阳转率非劣效于阳性对照。评价时间点可选择全程免疫后1个月或2个月，"
        "不同免疫程序的时间节点须保持一致，且应符合本品免疫应答规律的数据依据。",
        "共同观点：主要终点为免前阴性人群抗体阳转率非劣效于阳性对照。"
        "试验组与阳性对照组的评价时间点须保持一致，均可选择全程免疫后1个月或2个月，"
        "且应符合本品免疫应答规律的数据依据。",
    ),
    (
        "问题6 问题描述：期中分析 -> 中期分析",
        "问题6：关于随访周期与期中分析：建议Ⅲ期临床试验的安全性与免疫持久性随访至"
        "全程免疫后12个月，不建议开展期中分析。",
        "问题6：关于随访周期与中期分析：建议Ⅲ期临床试验的安全性与免疫持久性随访至"
        "全程免疫后12个月，不建议开展中期分析。",
    ),
    (
        "问题6 共同观点：期中分析 -> 中期分析",
        "共同观点：需完成全程免疫后12个月的免疫持久性随访与安全性随访，获得相应数据后方可申报；"
        "不针对免疫原性替代指标开展期中分析并提前揭盲。",
        "共同观点：需完成全程免疫后12个月的免疫持久性随访与安全性随访，获得相应数据后方可申报；"
        "不针对免疫原性替代指标开展中期分析并提前揭盲。",
    ),
    (
        "四、后续工作安排第2点：编制->修订，需->建议",
        "2. 本次调整后的Ⅲ期临床试验方案完成编制后，需重新提交沟通交流申请，"
        "并同步提请药审中心统计专业参与审核。",
        "2. 本次调整后的Ⅲ期临床试验方案修订完成后，建议重新提交沟通交流申请，"
        "并同步提请药审中心统计专业参与审核。",
    ),
]


def _stamp() -> str:
    """Fallback revision date, used only when REVISION_DATE is cleared."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def revise_paragraph(paragraph, new_text: str, ids) -> bool:
    """Rewrite ``paragraph`` as a tracked deletion plus a tracked insertion."""
    paragraph_element = paragraph._element
    runs = [run for run in paragraph_element.findall(qn("w:r")) if run.getparent() is paragraph_element]
    if not runs:
        logger.warning("paragraph has no direct w:r children; skipped")
        return False

    first_rpr = runs[0].find(qn("w:rPr"))

    # One single <w:del> holding every original run keeps Word from rendering
    # a fragmented strikethrough (the source files often split a paragraph into
    # many runs, which would otherwise become many small deletions).
    # remember where the first run sits so the deletion goes back to that spot
    previous_sibling = runs[0].getprevious()

    deletion = OxmlElement("w:del")
    deletion.set(qn("w:id"), str(next(ids)))
    deletion.set(qn("w:author"), AUTHOR)
    deletion.set(qn("w:date"), REVISION_DATE or _stamp())
    for run in runs:
        for text_node in run.findall(qn("w:t")):
            text_node.tag = qn("w:delText")
            text_node.set(qn("xml:space"), "preserve")
        run.getparent().remove(run)
        deletion.append(run)
    if previous_sibling is not None:
        previous_sibling.addnext(deletion)
    else:
        paragraph_element.insert(0, deletion)

    insertion = OxmlElement("w:ins")
    insertion.set(qn("w:id"), str(next(ids)))
    insertion.set(qn("w:author"), AUTHOR)
    insertion.set(qn("w:date"), REVISION_DATE or _stamp())

    new_run = OxmlElement("w:r")
    if first_rpr is not None:
        new_run.append(copy.deepcopy(first_rpr))
    new_text_node = OxmlElement("w:t")
    new_text_node.text = new_text
    new_text_node.set(qn("xml:space"), "preserve")
    new_run.append(new_text_node)
    insertion.append(new_run)
    paragraph_element.append(insertion)
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    if not SOURCE.exists():
        logger.error("source minutes not found: %s", SOURCE)
        return 2

    doc = Document(str(SOURCE))
    ids = count(1000)

    revised = 0
    for label, original, replacement in REVISIONS:
        matches = [p for p in doc.paragraphs if p.text.strip() == original]
        if len(matches) != 1:
            logger.error(
                "expected exactly 1 match for '%s', found %d", label, len(matches)
            )
            return 3
        revise_paragraph(matches[0], replacement, ids)
        revised += 1
        logger.info("revised: %s", label)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    logger.info("track-changes paragraphs: %d", revised)
    logger.info("saved: %s", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
