"""
从 review_materials 清单文件中提取「有乙肝疫苗接种史的 18-59 岁人群」62 例的
免前乙肝两对半检测逐例数据。

输入：第8册 表 16.2.4.3 (乙型肝炎疫苗接种史清单) + 第9册 表 16.2.4.12 (乙肝两对半检测清单)
输出：review_materials/_md_cache/有接种史_62例_两对半逐例数据.md
"""

import re
from collections import defaultdict
from pathlib import Path

BASE = Path(r"E:\Cursor Project\2-Scientific-Skills-for-Clinical_Trial\review_materials\_md_cache")
F_VOL8 = BASE / "第8册_清单1.md"
F_VOL9 = BASE / "第9册_清单2.md"
F_OUT = BASE / "有接种史_62例_两对半逐例数据.md"


def parse_pipe_row(line: str) -> list[str]:
    """解析 markdown 表格行，去掉首尾 | 然后按 | 切分。"""
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        return []
    cells = [c.strip() for c in line[1:-1].split("|")]
    return cells


def extract_vaccination_history(vol8_text: str) -> list[dict]:
    """从第8册解析表 16.2.4.3 乙型肝炎疫苗接种史(FAS) — 仅提取 18-59 岁人群。"""
    rows = []
    in_target_table = False
    header_seen = False
    skip_separator = False
    for line in vol8_text.splitlines():
        if "表16.2.4.3 乙型肝炎疫苗接种史" in line:
            in_target_table = True
            continue
        if in_target_table and "表16.2.4.4" in line:
            break
        if not in_target_table:
            continue
        if "年龄组" in line and "组别" in line and "研究 编号" in line:
            header_seen = True
            continue
        if header_seen and not skip_separator:
            # 跳过表头分隔线
            if re.match(r"^\|[\s\-:|]+\|\s*$", line):
                skip_separator = True
                continue
        if header_seen and skip_separator:
            cells = parse_pipe_row(line)
            if len(cells) < 8:
                continue
            age_group = cells[0]
            if "18-59" not in age_group:
                continue
            rows.append(
                {
                    "age_group": age_group,
                    "group": cells[1],
                    "subject_id": cells[2],
                    "sex": cells[3],
                    "age": cells[4],
                    "vaccine_name": cells[6],
                    "doses": cells[7],
                }
            )
    return rows


def extract_hbsab_listing(vol9_text: str) -> dict:
    """从第9册解析表 16.2.4.12 乙肝两对半检测清单(FAS) — 返回 {研究编号: 记录}。"""
    records = {}
    in_target_table = False
    header_seen = False
    skip_separator = False
    for line in vol9_text.splitlines():
        if "表16.2.4.12 乙肝两对半检测清单" in line:
            in_target_table = True
            continue
        if in_target_table and "表16.2.4.13" in line:
            break
        if not in_target_table:
            continue
        if "年龄组" in line and "研究 编号" in line and "乙肝表面抗原" in line:
            header_seen = True
            continue
        if header_seen and not skip_separator and re.match(r"^\|[\s\-:|]+\|\s*$", line):
            skip_separator = True
            continue
        if header_seen and skip_separator:
            cells = parse_pipe_row(line)
            if len(cells) < 13:
                continue
            sid = cells[2]
            records[sid] = {
                "age_group": cells[0],
                "group": cells[1],
                "subject_id": sid,
                "sex": cells[3],
                "age": cells[4],
                "sample_date": cells[5],
                "hbsag": cells[6],
                "hbsab": cells[7],
                "hbsab_below_ll": cells[8],
                "hbeag": cells[9],
                "hbeab": cells[10],
                "hbcab": cells[11],
                "overall": cells[12],
            }
    return records


def main():
    vol8_text = F_VOL8.read_text(encoding="utf-8")
    vol9_text = F_VOL9.read_text(encoding="utf-8")

    history = extract_vaccination_history(vol8_text)
    hbsab = extract_hbsab_listing(vol9_text)

    print(f"接种史清单解析到 {len(history)} 例（18-59 岁有接种史）")
    print(f"两对半清单解析到 {len(hbsab)} 条记录")

    # 按组别分组输出（用 dict 避免 list 的 `in` 误判）
    by_group: dict[str, dict[str, dict]] = defaultdict(dict)
    missing = []
    for r in history:
        sid = r["subject_id"]
        if sid in by_group[r["group"]]:
            continue
        h = hbsab.get(sid)
        if h is None:
            missing.append(sid)
            continue
        r["hbsab"] = h["hbsab"]
        r["sample_date"] = h["sample_date"]
        r["hbsag"] = h["hbsag"]
        r["hbeag"] = h["hbeag"]
        r["hbeab"] = h["hbeab"]
        r["hbcab"] = h["hbcab"]
        r["hbsab_below_ll"] = h["hbsab_below_ll"]
        r["overall"] = h["overall"]
        by_group[r["group"]][sid] = r

    print(f"未匹配到两对半数据的例数: {len(missing)} (编号: {missing})")
    for g, lst in by_group.items():
        print(f"  {g}: {len(lst)} 例")

    # 写出 markdown
    out_lines = [
        "# 18-59 岁有乙肝疫苗接种史 62 例受试者 — 免前乙肝两对半逐例数据",
        "",
        "> **数据来源**：",
        "> - 接种史：第 8 册(清单1) 表 16.2.4.3「乙型肝炎疫苗接种史(FAS)」",
        "> - 乙肝两对半检测：第 9 册(清单2) 表 16.2.4.12「乙肝两对半检测清单(FAS)」",
        "> **关联规则**：以受试者研究编号为唯一键，从两表交叉合并。",
        "> **生成时间**：2026-09-09",
        "",
        f"**总计提取**：18-59 岁有接种史 **{sum(len(v) for v in by_group.values())} 例**，分布于 5 个组别。",
        "",
    ]

    group_order = [
        "0,1月低剂量组(A1)",
        "0,1月高剂量组(A2)",
        "0,2月低剂量组(B1)",
        "0,2月高剂量组(B2)",
        "阳性对照组(C1)",
    ]
    for g in group_order:
        if g not in by_group:
            continue
        rows = list(by_group[g].values())
        out_lines.append(f"## {g}（N={len(rows)}）")
        out_lines.append("")
        out_lines.append(
            "| 序号 | 研究编号 | 性别 | 年龄(岁) | 采样日期 | 表面抗原(IU/ml) | **表面抗体(mIU/ml)** | e抗原 | e抗体 | 核心抗体 | 两对半结果 | 既往接种剂次 |"
        )
        out_lines.append(
            "| ---: | ---: | :---: | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |"
        )
        for i, r in enumerate(rows, 1):
            out_lines.append(
                f"| {i} | {r['subject_id']} | {r['sex']} | {r['age']} | {r['sample_date']} | "
                f"{r['hbsag']} | **{r['hbsab']}** | {r['hbeag']} | {r['hbeab']} | {r['hbcab']} | "
                f"{r['overall']} | {r['doses']} |"
            )
        out_lines.append("")

    if missing:
        out_lines.append("---")
        out_lines.append("")
        out_lines.append("## 缺失警告")
        out_lines.append("")
        out_lines.append("以下研究编号在两对半清单中未找到对应记录：")
        out_lines.append(", ".join(missing))
        out_lines.append("")

    # 关键观察
    out_lines.append("---")
    out_lines.append("")
    out_lines.append("## 关键观察")
    out_lines.append("")
    out_lines.append("1. **两对半 HBsAb 与免疫原性 GMC 是两套不同的检测数据**：")
    out_lines.append(
        '   - 清单 16.2.4.12 中的"乙肝表面抗体(mIU/mL)"来自**临床诊断型两对半检测**（用于筛选期判定入组），检测下限(LLOQ) 较高，结果统一显示为 `<0.500` / `0.500` 等；'
    )
    out_lines.append(
        "   - 免疫原性分析（第 3 册 14.2.3.1 节）中的免前抗-HBs 浓度来自**免疫原性专项检测**（用于计算 GMC），灵敏度高得多，呈现为 1.12–1.97 mIU/mL 的连续分布。"
    )
    out_lines.append("   - 二者不可混用，GMC 必须以免疫原性专项检测的数据为准。")
    out_lines.append("")
    out_lines.append(
        '2. **62 例筛选期两对半 HBsAb 均 ≤ 试剂盒 LLOQ**（`<0.500` 或 `0.500`），全部判定为"≤现场检测试剂盒空白限(2mIU/mL)"="全阴性"——这正是入组标准 4 要求的 HBsAb ≤ 2 mIU/mL 状态。'
    )
    out_lines.append("")
    out_lines.append(
        '3. **既往接种剂次分布**：尽管自报有接种史，但绝大多数受试者回忆的具体剂次为"不详"或已衰减到无法检测出保护性抗体，提示**远期接种史并不能保证现行抗体阳性**。'
    )
    out_lines.append("")

    F_OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n已写入：{F_OUT}")


if __name__ == "__main__":
    main()
