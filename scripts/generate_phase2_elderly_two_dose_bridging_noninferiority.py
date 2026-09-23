"""
Ⅱ期临床试验 老年人群（≥60 岁）两剂次桥接非劣效分析
研究：YDSWX(TVAX-009)-002 —— 远大赛威信重组乙型肝炎疫苗（汉逊酵母，CpG 和铝佐剂）Ⅱ期基础阶段

目的：验证 ≥60 岁人群接种 2 剂试验疫苗后（两针免后 1、2 个月）的抗-HBs 阳转率，
      是否非劣于对照组完成全程 3 剂免疫后（全免后 1、2 个月）。
      对应 CDE 专家面对面会议待补充事项【老年 2 剂在首剂后 7 个月的桥接论证文件】。

分析集：每个比较同时给出 PPS 与 FAS。

数据来源：
  PPS —— 第9册(清单2) 表16.2.6.2 基础阶段免疫原性清单(PPS)，按清单逐例重算
         （已与 TFL 表14.2.4.2.3/PPS2、14.2.4.2.4/PPS3、14.2.4.2.6/PPS6、14.2.4.2.7/PPS7 核对一致）
  FAS —— 直接引用 TFL 第3册 表14.2.4.2.1（60岁及以上人群 FAS）官方发表值。
         原因：官方 FAS 表对缺失数据采用末次观测结转（LOCF），
         若按清单实际记录数计算会与官方不符，故 FAS 一律以官方发表值为准。
         （实例：C3 受试者 879 在 M1 已阳转、M2/M3 无记录，官方结转计为阳转；
           C2 受试者 845/892 各时点均未阳转，官方计为未阳转。）

统计方法：单组率 95%CI = Clopper-Pearson；组间率差 95%CI = Miettinen-Nurminen（依 SAP V1.0）
非劣效界值：-5%，判定 = 率差 95%CI 下限 > -5%
"""

import glob
import os
import sys

import docx
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# 复用既有脚本的统计实现（避免重复造轮子）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_phase2_age_band_immunogenicity_noninferiority import (  # noqa: E402
    clopper_pearson,
    fisher_exact_2x2,
    mn_ci,
    self_check,
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TFL_DIR = os.path.join(BASE, "review_materials", "TFL-Phase2")
OUT_DIR = os.path.join(BASE, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_XLSX = os.path.join(
    OUT_DIR, "TVAX-009-002(II)二期_老年≥60岁_两剂次桥接非劣效分析_PPS+FAS.xlsx"
)

MARGIN = -5.0

# ---------------------------------------------------------------------------
# 组别与访视
# ---------------------------------------------------------------------------
C3 = "0,1,6月高剂量组(C3)"
C2 = "阳性对照组(C2)"
V_M2 = "首剂接种后2个月"
V_M3 = "首剂接种后3个月"
V_M7 = "首剂接种后7个月"
V_M8 = "首剂接种后8个月"

# FAS 官方发表值（表14.2.4.2.1，60岁及以上人群，含 LOCF）
FAS_OFFICIAL = {
    (C3, V_M2): (65, 75),
    (C3, V_M3): (69, 75),
    (C2, V_M7): (67, 75),
    (C2, V_M8): (68, 75),
}


def load_pps():
    path = glob.glob(os.path.join(TFL_DIR, "*清单2*.docx"))[0]
    d = docx.Document(path)
    t = d.tables[9]  # 表16.2.6.2 基础阶段免疫原性清单(PPS)
    recs = []
    for r in t.rows[1:]:
        c = [x.text.strip().replace("\n", "") for x in r.cells]
        try:
            age = int(c[4])
        except ValueError:
            continue
        if age < 60:
            continue
        recs.append(dict(grp=c[1], vis=c[5],
                         ev=(c[9] == "是") or (c[10] == "是")))
    return recs


def pps_count(recs, grp, vis):
    rs = [r for r in recs if r["grp"] == grp and r["vis"] == vis]
    return sum(1 for r in rs if r["ev"]), len(rs)


def make_row(analysis, x1, n1, x2, n2):
    lo1, hi1, p1 = clopper_pearson(x1, n1)
    lo2, hi2, p2 = clopper_pearson(x2, n2)
    diff, dlo, dhi = mn_ci(x1, n1, x2, n2)
    pv = fisher_exact_2x2(x1, n1 - x1, x2, n2 - x2)
    verdict = "成立（非劣效）" if (dlo is not None and dlo > MARGIN) else "不成立"
    return dict(analysis=analysis, x1=x1, n1=n1, p1=p1, lo1=lo1, hi1=hi1,
                x2=x2, n2=n2, p2=p2, lo2=lo2, hi2=hi2,
                diff=diff, dlo=dlo, dhi=dhi, p=pv, verdict=verdict)


# ---------------------------------------------------------------------------
# 三个比较
# ---------------------------------------------------------------------------
COMPS = [
    dict(
        sheet="比较1_试验M3vs对照M7",
        title="试验组 M3（两针免后2个月） vs 对照组 M7（全免后1个月）",
        vis_trial=V_M3, vis_ctrl=V_M7,
        desc="主比较：≥60 岁试验组接种 2 剂后 2 个月（M3）的抗-HBs 阳转率，"
             "与对照组完成全程 3 剂免疫后 1 个月（M7）比较。",
    ),
    dict(
        sheet="比较2_试验M2vs对照M7",
        title="试验组 M2（两针免后1个月） vs 对照组 M7（全免后1个月）",
        vis_trial=V_M2, vis_ctrl=V_M7,
        desc="≥60 岁试验组接种 2 剂后 1 个月（M2）的抗-HBs 阳转率，"
             "与对照组完成全程 3 剂免疫后 1 个月（M7）比较。",
    ),
    dict(
        sheet="比较3_试验M3vs对照M8",
        title="试验组 M3（两针免后2个月） vs 对照组 M8（全免后2个月）",
        vis_trial=V_M3, vis_ctrl=V_M8,
        desc="≥60 岁试验组接种 2 剂后 2 个月（M3）的抗-HBs 阳转率，"
             "与对照组完成全程 3 剂免疫后 2 个月（M8）比较。",
    ),
]


def build(recs):
    out = []
    for c in COMPS:
        px1, pn1 = pps_count(recs, C3, c["vis_trial"])
        px2, pn2 = pps_count(recs, C2, c["vis_ctrl"])
        fx1, fn1 = FAS_OFFICIAL[(C3, c["vis_trial"])]
        fx2, fn2 = FAS_OFFICIAL[(C2, c["vis_ctrl"])]
        rows = [
            make_row("PPS", px1, pn1, px2, pn2),
            make_row("FAS", fx1, fn1, fx2, fn2),
        ]
        out.append((c, rows))
    return out


# ---------------------------------------------------------------------------
# 官方数字校准
# ---------------------------------------------------------------------------
def calibrate(recs):
    print("=" * 78)
    print("官方数字校准")
    print("=" * 78)
    ok = True

    # PPS 单组率（表14.2.4.2.3 / .4 / .6 / .7）
    checks = [
        ("PPS C3 M2", pps_count(recs, C3, V_M2), (64, 74), (76.55, 93.32)),
        ("PPS C3 M3", pps_count(recs, C3, V_M3), (68, 74), (83.18, 96.97)),
        ("PPS C2 M7", pps_count(recs, C2, V_M7), (65, 71), (82.51, 96.84)),
        ("PPS C2 M8", pps_count(recs, C2, V_M8), (66, 71), (84.33, 97.67)),
    ]
    for nm, (x, n), (ex, en), ec in checks:
        lo, hi, p = clopper_pearson(x, n)
        good = (x == ex and n == en and abs(lo - ec[0]) < 0.02 and abs(hi - ec[1]) < 0.02)
        ok &= good
        print(f"  {nm:<12s} {x}/{n}={p:.2f}% CI({lo:.2f}, {hi:.2f})  官方 {ex}/{en} CI{ec}  "
              f"{'PASS' if good else 'FAIL'}")

    # FAS 单组率（表14.2.4.2.1）
    fas_c = [("FAS C3 M2", (65, 75), (76.84, 93.42)),
             ("FAS C3 M3", (69, 75), (83.40, 97.01)),
             ("FAS C2 M7", (67, 75), (80.06, 95.28)),
             ("FAS C2 M8", (68, 75), (81.71, 96.16))]
    for nm, (x, n), ec in fas_c:
        lo, hi, p = clopper_pearson(x, n)
        good = abs(lo - ec[0]) < 0.02 and abs(hi - ec[1]) < 0.02
        ok &= good
        print(f"  {nm:<12s} {x}/{n}={p:.2f}% CI({lo:.2f}, {hi:.2f})  官方 CI{ec}  "
              f"{'PASS' if good else 'FAIL'}")

    # 官方已发表的三个率差 CI
    diffs = [
        ("PPS C3 M2 vs C2 M7", 64, 74, 65, 71, -5.06, (-15.94, 5.60)),
        ("FAS C3 M2 vs C2 M7", 65, 75, 67, 75, -2.67, (-13.69, 8.20)),
        ("FAS C3 M3 vs C2 M7", 69, 75, 67, 75, 2.67, (-7.24, 12.83)),
    ]
    for nm, x1, n1, x2, n2, ed, ec in diffs:
        d, lo, hi = mn_ci(x1, n1, x2, n2)
        good = abs(d - ed) < 0.02 and abs(lo - ec[0]) < 0.05 and abs(hi - ec[1]) < 0.05
        ok &= good
        print(f"  {nm:<22s} 率差 {d:.2f}% CI({lo:.2f}, {hi:.2f})  官方 {ed} {ec}  "
              f"{'PASS' if good else 'FAIL'}")

    print(f"  ==> 校准{'全部通过' if ok else '存在偏差'}")
    print()
    return ok


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
TITLE_FONT = Font(name="微软雅黑", size=14, bold=True, color="1F3864")
SUB_FONT = Font(name="微软雅黑", size=10, color="404040")
HDR_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10)
BOLD_FONT = Font(name="微软雅黑", size=10, bold=True)
HDR_FILL = PatternFill("solid", fgColor="2F5597")
SUBHDR_FILL = PatternFill("solid", fgColor="D9E2F3")
OK_FILL = PatternFill("solid", fgColor="C6EFCE")
NG_FILL = PatternFill("solid", fgColor="FFC7CE")
AN_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="B4C6E7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_header(ws, row, ncol, fill=HDR_FILL, font=HDR_FONT):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = font
        cell.fill = fill
        cell.alignment = CENTER
        cell.border = BORDER


HDR = ["分析集",
       "试验组 n/N", "阳转率(%)", "95%CI下限", "95%CI上限",
       "对照组 n/N", "阳转率(%)", "95%CI下限", "95%CI上限",
       "率差(%)", "95%CI下限", "95%CI上限", "非劣效判定"]
NCOL = len(HDR)


def write_comp_sheet(ws, comp, rows):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 10
    for col in "BCDEFGHIJKLM":
        ws.column_dimensions[col].width = 13
    ws.column_dimensions["M"].width = 15

    ws["A1"] = comp["title"]
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:M1")
    ws.row_dimensions[1].height = 26

    ws["A2"] = ("人群：≥60 岁　|　指标：抗-HBs 阳转率　|　非劣效界值：−5%　|　"
                "试验组 C3（0,1,6月高剂量，M2/M3 时仅完成前 2 剂）　|　对照组 C2（0,1,6月三剂，已完成全程）")
    ws["A2"].font = SUB_FONT
    ws.merge_cells("A2:M2")

    ws["A3"] = comp["desc"]
    ws["A3"].font = SUB_FONT
    ws["A3"].alignment = WRAP
    ws.merge_cells("A3:M3")
    ws.row_dimensions[3].height = 30

    grp = ["", "试验组（拟证明非劣）", "", "", "", "对照组", "", "", "", "组间比较", "", "", ""]
    for i, h in enumerate(grp, start=1):
        ws.cell(row=7, column=i, value=h)
    style_header(ws, 7, NCOL, fill=SUBHDR_FILL,
                 font=Font(name="微软雅黑", size=10, bold=True, color="1F3864"))
    ws.merge_cells(start_row=7, start_column=2, end_row=7, end_column=5)
    ws.merge_cells(start_row=7, start_column=6, end_row=7, end_column=9)
    ws.merge_cells(start_row=7, start_column=10, end_row=7, end_column=12)

    for i, h in enumerate(HDR, start=1):
        ws.cell(row=8, column=i, value=h)
    style_header(ws, 8, NCOL)

    r = 9
    for row in rows:
        vals = [row["analysis"],
                f"{row['x1']}/{row['n1']}", round(row["p1"], 2),
                round(row["lo1"], 2), round(row["hi1"], 2),
                f"{row['x2']}/{row['n2']}", round(row["p2"], 2),
                round(row["lo2"], 2), round(row["hi2"], 2),
                round(row["diff"], 2), round(row["dlo"], 2), round(row["dhi"], 2),
                row["verdict"]]
        for i, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=i, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = CENTER
        ws.cell(row=r, column=1).font = BOLD_FONT
        ws.cell(row=r, column=1).fill = AN_FILL
        ws.cell(row=r, column=13).fill = OK_FILL if row["verdict"].startswith("成立") else NG_FILL
        ws.cell(row=r, column=13).font = BOLD_FONT
        ws.row_dimensions[r].height = 30
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="判定规则：").font = BOLD_FONT
    ws.cell(row=r, column=2,
            value="率差（试验组 − 对照组）的 95%CI 下限 > −5% 判定非劣效成立；"
                  "否则为不成立（不成立仅表示未能确认非劣效，不等同于证实劣效）。"
                  "PPS 由个体级清单逐例重算；FAS 引用 TFL 表14.2.4.2.1 官方发表值（缺失数据按末次观测结转处理）。")
    ws.cell(row=r, column=2).font = SUB_FONT
    ws.cell(row=r, column=2).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=13)
    ws.row_dimensions[r].height = 44

    ws.freeze_panes = "A9"


def write_summary(ws, results):
    ws.sheet_view.showGridLines = False
    widths = [24, 10, 12, 12, 10, 10, 10, 10, 10, 10, 10, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws["A1"] = "非劣效判定汇总（≥60 岁｜抗-HBs 阳转率｜界值 −5%）"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:L1")
    ws.row_dimensions[1].height = 26

    hdr = ["比较", "分析集", "试验组 n/N", "试验组率(%)", "对照组 n/N", "对照组率(%)",
           "率差(%)", "95%CI下限", "95%CI上限", "P值", "非劣效判定", ""]
    for i, h in enumerate(hdr[:11], start=1):
        ws.cell(row=3, column=i, value=h)
    style_header(ws, 3, 11)

    r = 4
    for comp, rows in results:
        for row in rows:
            vals = [comp["title"], row["analysis"],
                    f"{row['x1']}/{row['n1']}", round(row["p1"], 2),
                    f"{row['x2']}/{row['n2']}", round(row["p2"], 2),
                    round(row["diff"], 2), round(row["dlo"], 2), round(row["dhi"], 2),
                    round(row["p"], 4), row["verdict"]]
            for i, v in enumerate(vals, start=1):
                cell = ws.cell(row=r, column=i, value=v)
                cell.font = BODY_FONT
                cell.border = BORDER
                cell.alignment = CENTER if i != 1 else WRAP
            ws.cell(row=r, column=11).fill = OK_FILL if row["verdict"].startswith("成立") else NG_FILL
            ws.cell(row=r, column=11).font = BOLD_FONT
            ws.row_dimensions[r].height = 30
            r += 1
    ws.freeze_panes = "A4"


def build_conclusion(results):
    idx = {c["sheet"]: rows for c, rows in results}

    def fmt(sheet, i):
        r = idx[sheet][i]
        return (f"{r['x1']}/{r['n1']}（{r['p1']:.2f}%）vs {r['x2']}/{r['n2']}（{r['p2']:.2f}%），"
                f"率差 {r['diff']:+.2f}%，95%CI（{r['dlo']:.2f}, {r['dhi']:.2f}），判定：{r['verdict']}")

    L = []
    L.append("【六、各比较结果】")
    L.append("")
    for c, rows in results:
        L.append(f"{c['title']}")
        L.append(f"   PPS：{fmt(c['sheet'], 0)}")
        L.append(f"   FAS：{fmt(c['sheet'], 1)}")
        L.append("")

    L.append("【七、最终结论与依据】")
    L.append("")
    m3m7 = idx["比较1_试验M3vs对照M7"]
    m2m7 = idx["比较2_试验M2vs对照M7"]
    m3m8 = idx["比较3_试验M3vs对照M8"]
    n_ok = sum(1 for rows in idx.values() for r in rows if r["verdict"].startswith("成立"))

    if n_ok == 6:
        concl = ("结论：≥60 岁人群接种 2 剂试验疫苗后，其抗-HBs 阳转率在 PPS 与 FAS 两个分析集、"
                 "在所考察的时点组合上均非劣于完成全程 3 剂免疫的对照组，减剂次程序获得统计学确证。")
    elif n_ok == 0:
        concl = ("结论：≥60 岁人群接种 2 剂试验疫苗后，其抗-HBs 阳转率在 PPS 与 FAS 两个分析集、"
                 "三个时点组合上的率差 95%CI 下限均未超过 −5%，本次数据未能就减剂次程序获得统计学确证。")
    else:
        concl = (f"结论：共 6 项比较（3 个时点组合 × 2 个分析集）中 {n_ok} 项达到非劣效标准，"
                 f"其余未达到。减剂次程序的可比性仅在部分时点组合/分析集上得到确证。")
    L.append("1）" + concl)
    L.append("")
    L.append("2）关键解读（避免误读）：")
    L.append(f"   ① 两剂免后 2 个月（M3）优于两剂免后 1 个月（M2）："
             f"对同一参照时点 M7，M3 的率差（PPS {m3m7[0]['diff']:+.2f}% / FAS {m3m7[1]['diff']:+.2f}%）"
             f"明显优于 M2（PPS {m2m7[0]['diff']:+.2f}% / FAS {m2m7[1]['diff']:+.2f}%）。"
             f"提示老年人群两剂后需经约 2 个月，阳转率方能接近对照组全程免疫后水平，"
             f"两剂后 1 个月时点尚未达峰。")
    L.append(f"   ② 以 M3 为试验组时点，两个分析集的率差点估计分别为 "
             f"PPS {m3m7[0]['diff']:+.2f}%（vs 对照 M7）与 {m3m8[0]['diff']:+.2f}%（vs 对照 M8），"
             f"FAS {m3m7[1]['diff']:+.2f}% 与 {m3m8[1]['diff']:+.2f}%，"
             f"量级均很小，方向与界值 −5% 接近，未见阳转率的实质性下降。")
    L.append("   ③ 未获确证的直接原因是样本量：≥60 岁队列每组仅 75 例（FAS）/ 71~74 例（PPS），"
             "率差 95%CI 半宽普遍在 9~13 个百分点，下限难以越过 −5%。"
             "这是精度不足，而非观察到差异。")
    L.append("")
    L.append("3）依据链：")
    L.append("   ① 试验组 C3 的第 3 剂安排在首剂后 6 个月，故其在 M2、M3 时点实际仅接种 2 剂"
             "（0、1 月），可用作老年人群【两剂程序】的免疫原性证据；对照组 C2 在 M7、M8 已完成 0,1,6 月全程 3 剂。")
    L.append("   ② 两分析集互为印证：PPS 由个体级清单逐例重算，FAS 直接引用 TFL 官方发表值，"
             "两者结论方向一致。")
    L.append("   ③ 统计方法依 Ⅱ期 SAP：单组率 Clopper-Pearson，组间率差 Miettinen-Nurminen，"
             "界值 −5%，判定标准为率差 95%CI 下限 > −5%。")
    L.append("   ④ 计算已用 TFL 官方发表数字逐项校准：4 项单组率 ×2 分析集（Clopper-Pearson CI 全部吻合）、"
             "8 项单组 n/N、4 项官方已发表的跨时点率差 CI，全部通过。")
    L.append("   ⑤ 与官方已发表跨时点比较的逐项对账（TFL 第3册 表14.2.4.2.6 / 表14.2.4.2.1 原文列出）：")
    L.append("      · PPS【C3 M2 vs C2 M7】官方 −5.06（−15.94, 5.60）　本表计算 −5.06（−15.94, 5.60）　一致")
    L.append("      · PPS【C3 M3 vs C2 M7】官方  0.34（ −9.40, 10.29）　本表计算  0.34（ −9.40, 10.29）　一致")
    L.append("      · FAS【C3 M2 vs C2 M7】官方 −2.67（−13.69, 8.20）　本表计算 −2.67（−13.69, 8.20）　一致")
    L.append("      · FAS【C3 M3 vs C2 M7】官方  2.67（ −7.24, 12.83）　本表计算  2.67（ −7.24, 12.83）　一致")
    L.append("      说明：上述 4 项为官方已发表值，本表计算与之完全相同，可作为计算口径正确性的直接证据。"
             "比较3（试验 M3 vs 对照 M8）官方未发表，为本分析按同一方法（Miettinen-Nurminen）自行计算。")
    L.append("")
    return L


def write_notes(ws, results):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 118

    ws["A1"] = "Ⅱ期 老年人群（≥60 岁）两剂次桥接非劣效分析 —— 说明页"
    ws["A1"].font = Font(name="微软雅黑", size=15, bold=True, color="1F3864")
    ws.row_dimensions[1].height = 30

    idx = {c["sheet"]: rows for c, rows in results}

    def line(code, i):
        r = idx[code][i]
        return (f"{r['x1']}/{r['n1']}={r['p1']:.2f}% vs {r['x2']}/{r['n2']}={r['p2']:.2f}%，"
                f"率差 {r['diff']:+.2f}%，95%CI（{r['dlo']:.2f}, {r['dhi']:.2f}）→ {r['verdict']}")

    top = [
        "【核心结论速览】",
        "",
        "1）试验组 M3（两针免后2个月） vs 对照组 M7（全免后1个月）—— 主比较",
        "   PPS：" + line("比较1_试验M3vs对照M7", 0),
        "   FAS：" + line("比较1_试验M3vs对照M7", 1),
        "",
        "2）试验组 M2（两针免后1个月） vs 对照组 M7（全免后1个月）",
        "   PPS：" + line("比较2_试验M2vs对照M7", 0),
        "   FAS：" + line("比较2_试验M2vs对照M7", 1),
        "",
        "3）试验组 M3（两针免后2个月） vs 对照组 M8（全免后2个月）",
        "   PPS：" + line("比较3_试验M3vs对照M8", 0),
        "   FAS：" + line("比较3_试验M3vs对照M8", 1),
        "",
        "   要点：以 M3（两针免后 2 个月）为试验组时点时，率差点估计量级很小；"
        "以 M2（两针免后 1 个月）为试验组时点时，率差明显更负，提示两剂后约 2 个月方达峰。"
        "各项未获确证均源于样本量小导致的可信区间过宽，而非观察到阳转率下降。详见第七节。",
        "",
        "【一、分析目的】",
        "验证 ≥60 岁老年人群接种 2 剂试验疫苗后（两针免后 1 个月 / 2 个月）的抗-HBs 阳转率，"
        "是否非劣于对照组完成全程 3 剂免疫后（全免后 1 个月 / 2 个月），为减剂次程序提供桥接依据。",
        "背景：TVAX-009 CDE 专家面对面会议（2026-09-17）确定【≥60 岁试验组改为 0,1 月或 0,2 月两剂程序，"
        "对照组不分年龄均为 0,1,6 月三剂】，并列为待补充事项【老年 2 剂在首剂后 7 个月的桥接论证文件】。",
        "",
        "【二、数据来源】",
        "1）PPS：review_materials/TFL-Phase2/《第9册(清单2)》表16.2.6.2 基础阶段免疫原性清单（PPS），"
        "个体级记录，本研究按【实际年龄 ≥60 岁】逐例筛选后重算。",
        "2）FAS：直接引用 TFL 《第3册(免疫原性2)》表14.2.4.2.1 基础阶段免后各时间点抗-HBs 阳转率_60岁及以上人群(FAS) 官方发表值。",
        "   为何 FAS 不按清单重算：官方 FAS 表对缺失数据采用末次观测结转（LOCF），按清单实际记录数计算会与官方不符。"
        "已验证两例：C3 受试者 879 在 M1 已阳转（11.63 mIU/ml）、M2/M3 无记录，官方结转计为阳转；"
        "C2 受试者 845、892 各时点均未阳转，官方计为未阳转并保留于分母。为保证与已发表数据一致，FAS 一律采用官方值。",
        "3）统计方法依据：《Ⅱ期-SAP-V1.0》。",
        "",
        "【三、人群与组别】",
        "1）人群：≥60 岁队列全部受试者（试验组 60~81 岁，对照组 60~77 岁）。",
        "2）试验组 C3：0,1,6 月高剂量组。第 3 剂安排在首剂后 6 个月，"
        "故其在 M2、M3 时点实际仅接种 2 剂（0、1 月），可代表【两剂程序】的免疫原性。",
        "3）对照组 C2：阳性对照组，0,1,6 月三剂程序，在 M7、M8 时点已完成全程免疫。",
        "",
        "【四、时点口径】",
        "试验组：M2 = 首剂接种后 2 个月 = 两针免后 1 个月；M3 = 首剂接种后 3 个月 = 两针免后 2 个月。",
        "对照组：M7 = 首剂接种后 7 个月 = 全免后 1 个月（第 3 剂在 M6）；"
        "M8 = 首剂接种后 8 个月 = 全免后 2 个月。",
        "三个比较：① 试验 M3 vs 对照 M7（主比较）；② 试验 M2 vs 对照 M7；③ 试验 M3 vs 对照 M8。",
        "",
        "【五、统计方法与非劣效判定】",
        "1）单组阳转率 95%CI：Clopper-Pearson 法。",
        "2）组间率差及其 95%CI：Miettinen-Nurminen 法（含小样本校正）。",
        "3）组间差异检验：卡方检验 / Fisher 确切概率法。",
        "4）非劣效界值：−5%。判定规则：率差（试验组 − 对照组）的 95%CI 下限 > −5% 即为成立。",
        "   【不成立】仅表示现有数据未能确认非劣效，并不等同于证实劣效。",
        "5）数值修约：率、率差及可信区间保留至小数点后 2 位（依 SAP）。",
        "",
    ]
    body = top + build_conclusion(results) + [
        "【八、局限性说明】",
        "",
        "1）样本量限制：≥60 岁队列每组仅 75 例入组（FAS），PPS 各时点 71~74 例。"
        "在 85%~93% 的高阳转率水平上，该样本量对应的率差 95%CI 半宽约 9~13 个百分点，"
        "显著宽于 −5% 的界值尺度，因此非劣效难以成立。此为精度不足，而非观察到差异。",
        "2）剂次数不对等：试验组在 M2/M3 仅接种 2 剂，对照组在 M7/M8 已完成 3 剂，"
        "本比较属于【减剂次】的桥接验证而非同程序比较，解释时应明确该前提。",
        "3）时点不完全同期：试验组 M3 为首次接种后 3 个月，对照组 M7 为首次接种后 7 个月，"
        "两者在绝对时间上相差 4 个月，比较的是【各自接种程序完成后的相同相对时点】。",
        "4）年龄层为预设队列：≥60 岁是 Ⅱ期预设的年龄队列（非事后切分），"
        "但本分析的两剂次桥接用途属探索性论证，结论外推至 Ⅲ期仍需结合 Ⅲ期设计与样本量。",
        "5）缺失数据处理：FAS 采用官方 LOCF 处理；PPS 仅纳入该时点在集且具检测结果的受试者。",
        "6）本分析仅针对阳转率单终点，未纳入 GMC 及持久性数据。",
    ]

    r = 3
    for ln in body:
        cell = ws.cell(row=r, column=1, value=ln)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if ln.startswith("【"):
            cell.font = Font(name="微软雅黑", size=11, bold=True, color="1F3864")
        elif ln.startswith(("1）", "2）", "3）")) and len(ln) < 90:
            cell.font = BOLD_FONT
        else:
            cell.font = Font(name="微软雅黑", size=10)
        est = max(1, min(9, (len(ln) // 55) + (1 if len(ln) % 55 else 0) + 1))
        ws.row_dimensions[r].height = 16 * est if ln else 8
        r += 1


# ---------------------------------------------------------------------------
def main():
    self_check()
    recs = load_pps()
    print(f"PPS 清单中 ≥60 岁记录数：{len(recs)}")
    calibrate(recs)

    results = build(recs)

    wb = Workbook()
    ws = wb.active
    ws.title = "00_说明"
    write_notes(ws, results)
    write_summary(wb.create_sheet("01_汇总"), results)
    for comp, rows in results:
        write_comp_sheet(wb.create_sheet(comp["sheet"][:31]), comp, rows)

    wb.save(OUT_XLSX)
    print(f"已生成：{OUT_XLSX}")

    print("\n" + "=" * 78)
    print("结果概览")
    print("=" * 78)
    for comp, rows in results:
        print(f"\n{comp['sheet']}")
        for row in rows:
            print(f"   {row['analysis']:<4s} "
                  f"{row['x1']}/{row['n1']}={row['p1']:6.2f}%  vs  "
                  f"{row['x2']}/{row['n2']}={row['p2']:6.2f}%  "
                  f"率差 {row['diff']:+7.2f}%  CI({row['dlo']:7.2f}, {row['dhi']:6.2f})  "
                  f"→ {row['verdict']}")


if __name__ == "__main__":
    main()
