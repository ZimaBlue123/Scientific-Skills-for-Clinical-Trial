"""Generate the CDE EoP2 online meeting minutes (2026-09-18) from the template.

The document is produced by *patching* ``CDE会议纪要模板.docx`` in place so that
every heading / field / body paragraph keeps the formatting shipped with the
template. Nothing is rebuilt from scratch.

Structure of the generated minutes
----------------------------------
Header fields
    product line, title, meeting type/category, date & time, venue, meeting No.,
    drug name, indication, applicant, host, recorder, participants
Body
    一、会议目的
    二、会议背景
    三、会议讨论问题及结果  -> N topic blocks
        <topic question>
        双方是否达成一致：☑是
        共同观点：<consensus>
    四、后续工作安排

Usage
-----
    python scripts/generators/generate_cde_eop2_online_meeting_minutes.py
"""

from __future__ import annotations

import copy
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

LOG_FORMAT = "%(asctime)s [%(levelname)s] eop2_minutes: %(message)s"
logger = logging.getLogger("eop2_minutes")

TEMPLATE = ROOT / "review_materials" / "CDE会议纪要模板.docx"
OUTPUT = (
    ROOT
    / "review_materials"
    / "TVAX-009 III期临床试验启动前沟通会（EoP2）线上会议纪要-2026年9月18日.docx"
)

CHECKED = "双方是否达成一致：☑是"

# The template mixes ASCII roman numerals ("I期", "Ⅱ类") with full-width ones.
# Everything written into the document is normalised to the full-width forms so
# that the whole minutes read consistently.
_ROMAN_RULES: tuple[tuple[str, str], ...] = (
    ("III", "Ⅲ"),
    ("II", "Ⅱ"),
    ("I", "Ⅰ"),
)


def _normalize_roman(text: str) -> str:
    """Rewrite ASCII ``I``/``II``/``III`` immediately before 期/类 as full-width roman numerals."""
    for ascii_form, full_width in _ROMAN_RULES:
        # the negative lookbehind keeps words such as "HIV期" or "AESI" untouched
        text = re.sub(rf"(?<![A-Za-z]){ascii_form}(?=[期类])", full_width, text)
    return text

# ---------------------------------------------------------------------------
# Header fields: exact template text -> replacement
# ---------------------------------------------------------------------------
HEADER_REPLACEMENTS: list[tuple[str, str]] = [
    ("TVAX-008注射液", "重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）（TVAX-009）"),
    ("Pre-IND沟通交流会议纪要", "III期临床试验启动前沟通会（EoP2）会议纪要"),
    (
        "会议分类：新药临床试验申请前会议",
        "会议分类：II期临床试验结束/III期临床试验启动前会议（EoP2）",
    ),
    ("召开日期和时间：2019年12月10日13:30-14:40", "召开日期和时间：2026年9月18日14:00-14:30"),
    ("会议地点：药品审评中心703会议室", "会议地点：线上会议"),
    ("会议编号：2019002984", "会议编号：2026003603"),
    (
        "药品名称：TVAX-008注射液",
        "药品名称：重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）（TVAX-009）",
    ),
    ("拟定适应症（或功能主治）：慢性乙型肝炎", "拟定适应症（或功能主治）：预防乙型肝炎病毒感染"),
    ("申请人：南京远大赛威信生物医药有限公司", "申请人：远大赛威信生命科学（南京）有限公司"),
]

# Template-only header rows that must not appear in the submitted minutes.
HEADER_DROPS: tuple[str, ...] = (
    "主持人：高建超",
    "记录人：张芸、周童",
)

PARTICIPANTS_APPLICANT = (
    "申请人：李建强、葛君、鲍梦汝、王美玲、李磊、李艳萍、于家捷、左梦玲、罗艺、王永吉"
)
PARTICIPANTS_CDE = "药审中心：刘亚林"

PURPOSE = (
    "一、会议目的："
    "就本品种Ⅲ期临床试验设计的完善进行沟通，落实2026年9月16日Ⅲ期临床试验启动前"
    "沟通会（EoP2）专家面对面会议的相关意见。"
)
BACKGROUND = (
    "二、会议背景："
    "申请人于2026年9月16日就重组乙型肝炎疫苗（汉逊酵母，CpG和铝佐剂）III期临床试验方案"
    "召开III期临床试验启动前沟通会（EoP2）专家面对面会议。"
    "2026年9月18日，药审中心与申请人以线上会议形式，"
    "就该品种III期临床试验设计的进一步完善进行沟通并形成以下会议意见。"
)

# (question, consensus)
TOPICS: list[tuple[str, str]] = [
    (
        "关于产品包装变更：产品由原两瓶包装变更为预灌封包装，属于重大变更，"
        "变更前后产品的可比性应如何考虑？",
        "该变更属于重大变更。申请人需与药学、非临床专业充分沟通，"
        "确认变更前后产品可比性研究的充分性；若药学、非临床专业认为现有研究"
        "尚不能完全证实变更前后产品的可比性，不排除需先行完成临床桥接研究，"
        "再开展III期临床试验。",
    ),
    (
        "关于受试者入组：若药学、非临床专业确认变更前后产品基本可比，"
        "III期临床试验入组时是否需控制入组速度？",
        "需严格控制受试者入组速度，切实保障受试者安全。",
    ),
    (
        "关于研究人群代表性：国内乙肝疫苗免疫规划实施具有时间节点，"
        "不同年龄人群既往接种史构成存在差异，III期临床试验研究人群的年龄构成应如何考虑？",
        "本研究人群聚焦于无乙肝疫苗接种史成人。申请人需收集国内乙肝无接种史人群的"
        "流行病学调查数据，确保研究人群的年龄构成与真实世界中无接种史人群的年龄构成"
        "保持一致，以保障研究人群的代表性。",
    ),
    (
        "关于老年人群占比：III期临床试验中60岁以上人群的入组占比是否有明确要求？",
        "需重点关注60岁以上人群的入组占比，该占比不得低于对应自然人群中"
        "该年龄段的年龄构成占比。",
    ),
    (
        "关于老年人群数据：II期临床试验中60岁以上人群两剂接种的随访数据有限，"
        "是否需补充相关研究？",
        "需审慎评估II期老年人群两剂接种短期随访数据所构成的研究基础，"
        "鼓励增加细胞免疫研究的采血点，并扩大细胞因子的检测覆盖范围。",
    ),
    (
        "关于主要终点：III期临床试验的主要终点及其评价时间点应如何设置？",
        "主要终点为抗体阳转率非劣效于阳性对照。评价时间点可选择全程免疫后1个月或2个月，"
        "不同免疫程序的时间节点须保持一致，且应具备本品免疫应答规律的数据依据；"
        "以接种后7个月作为评价时间点不予认可。",
    ),
    (
        "关于随访周期与期中分析：III期临床试验的免疫持久性随访与安全性随访应如何设置，"
        "能否基于免疫原性替代指标开展期中分析？",
        "需完成全程免疫后12个月的免疫持久性随访与安全性随访，获得相应数据后方可申报；"
        "不建议针对免疫原性替代指标开展期中分析并提前揭盲。",
    ),
    (
        "关于安全性监测：III期临床试验的安全性监测条目是否需进一步完善？",
        "需进一步完善征集性不良事件（AE）与特别关注的不良事件（AESI）监测条目，"
        "参照境外已上市同类产品及CpG佐剂疫苗相关信息，补充免疫性疾病相关监测内容。",
    ),
    (
        "关于样本量：III期临床试验的样本量应如何考虑？",
        "样本量除满足免疫原性评价的统计学要求外，需兼顾安全性观察需求，"
        "至少应保证能够观察到偶见不良反应，以适配复合佐剂系统在同类疫苗中的首次应用。",
    ),
    (
        "关于后续拓展研究：若后续拟开展有接种史人群1剂程序、老年人群3剂程序等研究，"
        "是否需另行评估？",
        "可以开展，但需先行评估现有I期、II期临床试验数据对上述研究的支持程度，"
        "并按注册要求推进。",
    ),
    (
        "关于特殊人群：若拟在免疫缺陷、HIV感染等不应答特殊人群中开展临床试验，"
        "申报要求如何？",
        "本处所述特殊人群不含老年人群，特指免疫缺陷、HIV感染等无应答人群。"
        "若I期、II期临床试验未纳入该类人群，后续开展确证性临床试验须严格按照"
        "《药品注册管理办法》及配套文件要求申报。",
    ),
]

FOLLOW_UPS: list[str] = [
    "四、后续工作安排：",
    "1. 申请人需梳理本次会议沟通内容，形成会议纪要并上传，经双方确认后定稿存档。",
    "2. 本次调整后的III期临床试验方案完成编制后，需重新提交沟通交流申请，"
    "并同步提请药审中心统计专业参与审核。",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _set_element_text(element, text: str) -> None:
    """Replace the visible text of a paragraph element, keeping the first run's formatting."""
    text = _normalize_roman(text)
    nodes = element.findall(".//" + qn("w:t"))
    if not nodes:
        logger.warning("paragraph carries no w:t node; text not applied: %s", text[:30])
        return
    nodes[0].text = text
    nodes[0].set(qn("xml:space"), "preserve")
    for extra in nodes[1:]:
        extra.text = ""


def _find_paragraph(doc, needle: str, *, exact: bool = True):
    for para in doc.paragraphs:
        text = para.text.strip()
        if (text == needle) if exact else (text.startswith(needle)):
            return para
    return None


def _patch_header(doc) -> int:
    """Apply the plain field replacements; returns the number of applied patches."""
    applied = 0
    for para in doc.paragraphs:
        original = para.text.strip()
        for old, new in HEADER_REPLACEMENTS:
            if original == old and old != new:
                _set_element_text(para._element, new)
                applied += 1
                break
    return applied


def _locate_topic_blocks(doc) -> list[list]:
    """Return the paragraph elements of every existing topic block (question + 2 follow-ups)."""
    paragraphs = doc.paragraphs
    blocks: list[list] = []
    for index, para in enumerate(paragraphs):
        if para.text.strip() == CHECKED and index >= 1 and index + 1 < len(paragraphs):
            blocks.append(
                [
                    paragraphs[index - 1]._element,
                    para._element,
                    paragraphs[index + 1]._element,
                ]
            )
    return blocks


def main() -> int:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    if not TEMPLATE.exists():
        logger.error("template not found: %s", TEMPLATE)
        return 2

    doc = Document(str(TEMPLATE))

    # ---- header fields -----------------------------------------------------
    logger.info("header fields patched: %d", _patch_header(doc))

    for drop_text in HEADER_DROPS:
        drop_para = _find_paragraph(doc, drop_text)
        if drop_para is None:
            logger.warning("header row to drop not found: %s", drop_text)
            continue
        parent = drop_para._element.getparent()
        if parent is not None:
            parent.remove(drop_para._element)
        logger.info("header row dropped: %s", drop_text)

    applicant_para = _find_paragraph(
        doc,
        "申请人：李建强、周童、葛君、任苏林、谭昌耀、张方宁、王贵强、徐纯、杨剑、任明、陈霄、董钦生、张芸",
    )
    if applicant_para is None:
        logger.error("participant (applicant) paragraph not found")
        return 3
    _set_element_text(applicant_para._element, PARTICIPANTS_APPLICANT)

    cde_para = _find_paragraph(
        doc,
        "药审中心：高晨燕、高建超、魏开坤、王洪航、万志红、李京艳、赛文博、胡莹莹、刘妍彤等",
    )
    if cde_para is None:
        logger.error("participant (CDE) paragraph not found")
        return 3
    _set_element_text(cde_para._element, PARTICIPANTS_CDE)

    # ---- body: purpose / background ---------------------------------------
    purpose_para = _find_paragraph(
        doc, "一、会议目的：讨论TVAX-008注射液的I期临床方案及部分药学问题。"
    )
    if purpose_para is None:
        logger.error("purpose paragraph not found")
        return 3
    _set_element_text(purpose_para._element, PURPOSE)

    background_para = _find_paragraph(doc, "二、会议背景：", exact=False)
    if background_para is None:
        logger.error("background paragraph not found")
        return 3
    _set_element_text(background_para._element, BACKGROUND)

    # ---- body: rebuild the topic blocks -----------------------------------
    blocks = _locate_topic_blocks(doc)
    if not blocks:
        logger.error("no topic block found in the template")
        return 3
    logger.info("topic blocks found in template: %d", len(blocks))

    template_block = blocks[0]
    template_style = purpose_para._element
    for block in blocks:
        for element in block:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

    anchor = None
    for para in doc.paragraphs:
        if para.text.strip() == "临床讨论问题：":
            anchor = para._element
            break
    if anchor is None:
        logger.error("sub-heading '临床讨论问题：' not found")
        return 3

    cursor = anchor
    for question, consensus in TOPICS:
        block = [copy.deepcopy(element) for element in template_block]
        _set_element_text(block[0], question)
        _set_element_text(block[1], CHECKED)
        _set_element_text(block[2], f"共同观点：{consensus}")
        for element in block:
            cursor.addnext(element)
            cursor = element
    logger.info("topic blocks inserted: %d", len(TOPICS))

    # ---- body: follow-up section (appended at the end) --------------------
    for text in FOLLOW_UPS:
        element = copy.deepcopy(template_style)
        _set_element_text(element, text)
        cursor.addnext(element)
        cursor = element
    logger.info("follow-up paragraphs appended: %d", len(FOLLOW_UPS))

    # ---- drop the template-only transition sentence -----------------------
    for para in list(doc.paragraphs):
        if para.text.strip().startswith("此外，CDE方面提出以下临床问题"):
            parent = para._element.getparent()
            if parent is not None:
                parent.remove(para._element)
            break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    logger.info("saved: %s", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
