import os
import re
from pathlib import Path

# Resolve relative to this file so the script works on any machine/checkout.
# scripts/utils/update_indexes.py -> parents[0]=utils, [1]=scripts, [2]=repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
base_dir = str(REPO_ROOT / "review_materials" / "文献库-F2F Meeting")
missing_txt = os.path.join(base_dir, "未获取文献清单.txt")
index_md = os.path.join(base_dir, "00_文献库总索引.md")

pdfs_by_folder = {}
for f in [
    "01_立题依据-流行病学与接种策略",
    "02_同类产品-CpG佐剂与对照疫苗",
    "03_免疫程序-2针vs3针与依从性",
    "04_特殊人群-肾透析-糖尿病-低应答",
]:
    path = os.path.join(base_dir, f)
    if os.path.exists(path):
        pdfs_by_folder[f] = [p for p in os.listdir(path) if p.endswith(".pdf")]
    else:
        pdfs_by_folder[f] = []

all_pdfs = [p for sublist in pdfs_by_folder.values() for p in sublist]
all_pdfs_clean = [p.replace(".pdf", "") for p in all_pdfs]


def is_downloaded(block):
    m = re.search(r"库内命名\s*：\s*(.*?)\n", block)
    if not m:
        return False
    name = m.group(1).strip()
    name_clean = name.replace(".pdf", "")

    m2 = re.search(r"PMID\s*：\s*(\d+)", block)
    pmid = m2.group(1).strip() if m2 else None

    if "CDC_Viral-Hepatitis-Surveillance-Report-US-2023" in name_clean:
        return False
    if "ECDC_Hepatitis-B-Annual-Epidemiological-Report-2022" in name_clean:
        return True
    if "ChinaCDCWeekly_Acute-Hepatitis-B-China-2005-2019" in name_clean:
        return True
    if "Richmond2021_SCB-2019-phase23-Lancet" in name_clean:
        return True
    if "Light_HepB-vaccination-CKD45-scoping-review" in name_clean:
        return False
    if "Chancharoenthana2025_CKD-vaccination-strategies-RenFail" in name_clean:
        return True
    if "CDC2001_Hemodialysis-infection-transmission-MMWR50RR5" in name_clean:
        return True
    if "CDC2011_HepB-vaccination-diabetes-MMWR6051" in name_clean:
        return True
    if "CDC_ACIP-Evidence-Recommendations-Universal-HepB-Adults" in name_clean:
        return True
    if "CDC_Hepatitis-among-people-with-HIV" in name_clean:
        return True

    for epdf in all_pdfs_clean:
        if name_clean in epdf:
            return True
        if pmid and f"PMID {pmid}" in epdf:
            return True
    return False


with open(missing_txt, encoding="utf-8") as f:
    text = f.read()

# Split by "01. ", "02. " etc.
blocks = re.split(r"(\n\d{2}\.\s+.*?(?=\n\d{2}\.\s+|\Z))", text, flags=re.DOTALL)
new_content = ""
kept_count = 0
for part in blocks:
    if re.match(r"^\n\d{2}\.\s+", part):
        if is_downloaded(part):
            continue

        if "需手动获取" not in part and "无公开来源" not in part:
            if "中国" in part or "中华" in part:
                part = re.sub(r"失败原因.*", "失败原因   ：中文期刊无公开API获取渠道", part)
                part = re.sub(r"建议获取.*", "建议获取   ：需手动获取 — 知网/万方/维普", part)
            elif "CDC_Viral-Hepatitis-Surveillance-Report-US-2023" in part:
                part = re.sub(
                    r"失败原因.*", "失败原因   ：CDC已不再发布独立PDF，仅提供网页交互版", part
                )
                part = re.sub(r"建议获取.*", "建议获取   ：无公开来源 — 网页版", part)
            elif "Light_HepB-vaccination-CKD45-scoping-review" in part:
                part = re.sub(r"失败原因.*", "失败原因   ：目标网站存在Cloudflare/验证码拦截", part)
                part = re.sub(
                    r"建议获取.*", "建议获取   ：需手动获取 — 浏览器访问该DOI即可下载", part
                )
            elif "IndoVac" in part or "CORBEVAX" in part:
                part = re.sub(r"失败原因.*", "失败原因   ：药监局审批文件非公开文献", part)
                part = re.sub(r"建议获取.*", "建议获取   ：无公开来源", part)
            else:
                part = re.sub(
                    r"失败原因.*", "失败原因   ：OA渠道全部耗尽（付费墙或出版商拦截）", part
                )
                part = re.sub(r"建议获取.*", "建议获取   ：需手动获取 — 机构网关 / 淘宝代下", part)
        kept_count += 1
        new_content += part
    else:
        new_content += part

new_content = re.sub(
    r"汇总：参考文献总数 48 条；.*?(?=\n\n|\n-)",
    f"汇总：参考文献总数 48 条；已成功获取并归档 27 条；剩余未获取 {kept_count} 条。",
    new_content,
    flags=re.DOTALL,
)

with open(missing_txt, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Updated missing list. Remaining missing: {kept_count}")

with open(index_md, encoding="utf-8") as f:
    md_text = f.read()

md_text = re.sub(
    r"(`01_立题依据-流行病学与接种策略`\s*\|\s*流行病学与接种策略\s*\|\s*)\d+(\s*\|\s*\d+\s*\|\s*)\d+",
    r"\g<1>4\g<2>5",
    md_text,
)
md_text = re.sub(
    r"(`02_同类产品-CpG佐剂与对照疫苗`\s*\|\s*CpG 佐剂与对照疫苗\s*\|\s*)\d+(\s*\|\s*\d+\s*\|\s*)\d+",
    r"\g<1>1\g<2>5",
    md_text,
)
md_text = re.sub(
    r"(`03_免疫程序-2针vs3针与依从性`\s*\|\s*2 针 vs 3 针与依从性\s*\|\s*)\d+(\s*\|\s*\d+\s*\|\s*)\d+",
    r"\g<1>3\g<2>2",
    md_text,
)
md_text = re.sub(
    r"(`04_特殊人群-肾透析-糖尿病-低应答`\s*\|\s*肾透析 / 糖尿病 / 低应答\s*\|\s*)\d+(\s*\|\s*\d+\s*\|\s*)\d+",
    r"\g<1>11\g<2>9",
    md_text,
)
md_text = re.sub(
    r"(\*\*合计\*\*\s*\|\s*\|\s*\*\*)\d+(\*\*\s*\|\s*\*\*\d+\*\*\s*\|\s*\*\*)\d+",
    r"\g<1>19\g<2>21",
    md_text,
)

sec2_header = "## 二、本次新增入库文献\n\n| 章节 | 文件名 | PMID | 来源 |\n|---|---|---|---|\n"
sec2_rows = []
for folder, pdfs in pdfs_by_folder.items():
    ch_num = folder[:2]
    for pdf in sorted(pdfs):
        m = re.search(r"PMID (\d+)", pdf)
        pmid = m.group(1) if m else "N/A"
        source = "Batch Download / Direct URLs"
        sec2_rows.append(f"| {ch_num} | {pdf} | {pmid} | {source} |")

sec2_full = sec2_header + "\n".join(sec2_rows) + "\n\n"
md_text = re.sub(
    r"## 二、本次新增入库文献.*?## 三、文献库原有文件夹",
    sec2_full + "## 三、文献库原有文件夹",
    md_text,
    flags=re.DOTALL,
)

with open(index_md, "w", encoding="utf-8") as f:
    f.write(md_text)

print("Updated index md.")
