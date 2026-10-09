---
name: clinical-immunogenicity-noninferiority
description: 疫苗／生物制品临床试验的免疫原性非劣效（桥接）分析。当用户要求「做非劣效分析」「算 GMC 比值及其 95%CI」「算率差及 95%CI」「国产第几剂 vs 对照组是否非劣」「全程免后 vs 两针免后做桥接」「阳转率/4 倍增长率/阳转（4倍增长）率怎么算」「非劣效界值取 -5% 或 GMC 比值 0.65」「把 CSR 或统计分析报告里的免疫原性清单重算一遍」时使用。从 CTR/SAR/CSR 的个体级免疫原性清单（docx 表格）出发，按任意人群（免前阴性/全人群/自定义）× 分析集（PPS/FAS）二次筛选，输出多子表 Excel 交付稿（00_说明 + 01_汇总 + 每比较一页），并做三方对账与交付前自检。
allowed-tools: Read Write Edit Bash
license: MIT license
compatibility: Requires Python >=3.10；依赖 python-docx（读清单）与 openpyxl（写 Excel），无需联网。统计内核为纯标准库实现。
metadata:
  version: "1.0.0"
  skill-author: WorkBuddy
  last-reviewed: "2026-10-09"
---

# 疫苗免疫原性非劣效分析

把「几分叫 non-inferior」这句话，变成一个可对账、可复核、可直接交出去的 Excel。

## 何时用

- 试验组 vs 阳性对照组（或不同免疫程序之间）的免疫原性非劣效/桥接论证
- 需要同时给出 **GMC 比值** 与 **率差**（含各自的 95%CI 与判定）
- 官方汇总表里没有你要的分层（如自定义人群、跨时点比较），必须回到**个体级清单**重算
- 需要覆盖 **免前阴性人群**（阳转率）与 **全人群**（阳转（4 倍增长）率）两套口径

## 何时不用

- 只想要官方汇总表里已有的现成数字 → 直接引用，不要重算
- 需要确证性（confirmatory）非劣效检验与把握度计算 → 本 skill 做的是**探索性再分析**，
  须在局限性里写明「非方案预设、未做多重性调整」

## 交付物形态

多子表 Excel，与 TVAX-009B Ⅰ期 / TVAX-009-002 Ⅱ期交付稿同构：

```
00_说明    八节：目的/数据来源/人群组别/时点口径/统计方法/校准/结论依据/局限性
01_汇总    全部 人群 × 分析集 × 指标 的判定一览（一眼看结论）
比较N_...  每个「人群_指标」一页，PPS / FAS 各一行
```

版式细节见 `references/deliverable_format.md`。

## 三条铁律（最容易翻车的三件事）

1. **必须用个体级清单，不能用汇总表。**
   汇总表只提供预设分层，无法二次切分；且不同表的口径（尤其 FAS）可能与清单不一致。

2. **先校准再出数。**
   用官方已发表的数字反验自己的统计实现，**任一项不吻合就停手**，不要带着错误出表。

3. **「不成立」≠「劣效」。**
   细分层样本量往往只有几十例，CI 极宽导致下限越不过界值，这是**精度不足**
   而非**观察到下降**。必须写清点估计的方向与量级、CI 宽度、天花板效应。

## 执行流程

### Step 0：确认口径（务必先与用户对齐，不要猜）

至少确认以下五项，写进 `00_说明`：

| 项 | 常见选项 |
|---|---|
| 时点 | 第 2 剂免后 1 个月 / 全程免后 1 个月 / 两者都做 |
| 人群 | 免前阴性人群 / 全人群 / 免前阳性人群（通常只做参考） |
| 分析集 | PPS（注意多剂次研究里 PPS1 / PPS2 按时点分工）+ FAS |
| 指标与界值 | GMC 比值（常用 0.65）、率差（常用 −5%） |
| 是否分年龄层 | 分层 or 合并总人群 |

用户没说清时，用 AskUserQuestion 一次问完，不要反复追问。

### Step 1：定位个体级清单

用 `scripts/parse_immunogenicity_listing.py`：

```bash
python scripts/parse_immunogenicity_listing.py --spec <项目规格>.json --dry-run
```

**`--dry-run` 不可跳过**：它会打印实际表头与列映射（`field::免前 -> 第 6 列 「HBsAb (mIU/ml)」`），
肉眼确认 occurrence 取对了再往下走。

> **踩过的坑**：同一册里常有表头高度相似的表。TVAX-009B Ⅰ期第 2 册中，
> 「表16.2.5.9 乙肝两对半检测清单」与「表16.2.6.1 抗HBs结果清单」表头都含
> 研究编号 / HBsAb / HBcAb，按关键词匹配会命中前者（多一列「采样时间」），结果全错。
> 脚本因此按**题注**定位表格（题注段落之后的第一个 `w:tbl`），不要改回去。

### Step 2：确认分组与剂次结构

从方案/CSR 读接种程序与剂次数，**不要猜**。多剂次研究里同一个组在不同时点
实际接种的剂数可能不同（例如第 3 剂安排在首剂后 6 个月，则该组在第 2 剂后的时点
实际只接种了 2 剂）——这是减剂次桥接论证成立的前提，必须写进说明页。

### Step 3：先跑统计内核自检

```bash
python scripts/compute_noninferiority.py --self-check
```

该命令用内置的两组官方已发表值（TVAX-009B Ⅰ期 6 项 Clopper-Pearson、
TVAX-009-002 Ⅱ期 4 项 Miettinen-Nurminen + 4 项 Newcombe 交叉验证）校验实现。
**不通过就别往下走。** `compute` 子命令内部也会先跑一遍自检，不通过则拒绝出数。

### Step 4：写规格文件

复制 `assets/tvax_009b_phase1_spec.json` 改。规格是一份 JSON，驱动全流程 4 个脚本：
分析臂、清单来源、时点、人群筛选、事件类型、界值、官方校准值、说明页文案（narrative）。

关键字段：

- `populations[].rate_metric.event`
  - `seroconversion` 免前 < cutoff 且免后 ≥ cutoff（**阳转率**，用于免前阴性人群）
  - `seroconversion_or_4fold` 阴性看阳转、阳性看免后较免前 ≥4 倍（**阳转（4 倍增长）率**，用于全人群）
  - `fourfold`、`positive` 见 `references/stat_methods.md`
- `censoring.rule` 删失值处理，**必须由官方基线 GMC 反算确定**（见 Step 5）
- `verification.official` 官方校准值；每一项需指定 `sheet`（比较页名）、`analysis_set`、`arm`

### Step 5：校准（不可跳过）

删失值规则**不要凭经验选**。做法：对每个候选规则算一遍官方已发表的基线 GMC，
取能吻合的那个。TVAX-009B Ⅰ期实测：

| 规则 | 免前全人群 GMC（试验组/对照组） | 官方 | 结论 |
|---|---|---|---|
| LOD/2 = 1.00 | 3.403 / 4.279 | 3.403 / 4.279 | **吻合** |
| LOD = 2.00 | 4.812 / 5.745 | 3.403 / 4.279 | 明显偏高，弃用 |

校准清单（全部吻合才出数）：

1. 单组 **GMC 与 95%CI**：全部「人群 × 分析集 × 组别」
2. 组间 **GMC 比较 P 值**：全部组合（这是最强的口径证据）
3. 单组 **率与 n/N**、Clopper-Pearson CI
4. 若计数与官方 N 对不上：先怀疑 FAS 是否走 LOCF（见 Step 5.5）

### Step 5.5：判断 FAS 能不能重算

**FAS 官方汇总表如果对缺失值采用末次观测结转（LOCF），按清单重算必然对不上。**

- 有 LOCF → FAS **只能引用官方发表值**，PPS 逐例重算；说明页写明理由
- 无脱落/无缺失（如 TVAX-009B Ⅰ期 80 例全完成） → PPS 与 FAS **均可重算**，但仍须逐项校准

判据：`报表里的 FAS N` 是否等于「真实在集且有该时点检测结果的人数」。
若不相等但官方表仍有 N 个人的率，多半是 LOCF 或 LOCF 变体。详见
`references/case_tvax_009_phase2.md`。

### Step 6：计算与出 Excel

```bash
python scripts/parse_immunogenicity_listing.py  --spec spec.json --out subjects.csv
python scripts/compute_noninferiority.py        --spec spec.json --subjects subjects.csv --out results.json
python scripts/build_noninferiority_workbook.py --spec spec.json --results results.json --out report.xlsx
python scripts/selfcheck_output.py              --spec spec.json --xlsx report.xlsx
```

四个脚本均通过同一份 `spec.json` 驱动，路径写在 spec 里，不硬编码进脚本。

### Step 7：交付前自检

`scripts/selfcheck_output.py` 检查：sheet 命名合法、说明页八节齐全且无占位符、
**判定 == (95%CI 下限 > 界值)**（防写反）、CI 自洽、率 = n/N、
GMC 比值 = GMC1/GMC2、汇总页与比较页一致、`spec.verification.official` 三方对账。

退出码非 0 即禁止交付。

## 统计口径

一句话版：

| 对象 | 方法 |
|---|---|
| 单组率 95%CI | Clopper-Pearson |
| 组间率差 95%CI | Miettinen-Nurminen（含 `(n1+n2)/(n1+n2−1)` 小样本校正） |
| 交叉验证 | Newcombe 杂交 Wilson（与 MN 差异应 <1 个百分点） |
| 组间率检验 | 卡方 / Fisher 确切概率法 |
| GMC 与 95%CI | 对数转换 + t 分布 |
| GMC 比值与 95%CI | 对数转换后**成组 t 检验**（与 CSR 组间 GMC 比较同口径） |
| 删失值 | LOD/2（默认），须校准 |

公式、边界条件与常见变体见 `references/stat_methods.md`。

## 结果解读铁律

用户往往希望得到「可比」的结论。**不得为迎合预期而修饰结果。**
正确做法是：如实呈现 + 解释原因 + 给出后续建议。说明页第七节应覆盖：

- 点估计的方向与量级（点估计接近 0 或为正 → 数值上可比）
- 未获确证的**真实原因**（精度不足 / 样本量小 / 变异大）
- 对照组出现 100% 时的**天花板效应**（系统性拉大负向率差）
- 两个人群结论不一致时，**解释差异来源**而不是挑好看的那个讲
- 局限性里写明：探索性再分析、未做多重性调整、不可用作注册确证依据

## 环境与坑

- Bash 里 `python` 可能是别的版本；统一用绝对路径的虚拟环境解释器。
- `Write` 写入的中文引号可能被规范化，导致 f-string 提前结束报
  `SyntaxError: invalid character` —— 字符串内用【】「」代替引号。
- Python <3.12 不支持 f-string 内嵌同种引号（`f"{d[f'k']}"`），仓库 CI 用 3.10，别这么写。
- **先 `--dry-run` 看列映射**，别直接跑全流程：occurrence 取错一位，
  免前/2 剂后/全程后会整体错位，且数值看起来「仍然合理」，极易漏检。
- 交付前跑 `py_compile`，能省一轮往返。

## 脚本与资产

| 路径 | 作用 |
|---|---|
| `scripts/parse_immunogenicity_listing.py` | docx 清单 → 个体级 CSV（题注定位） |
| `scripts/compute_noninferiority.py` | 统计内核 + 自检 + 计算（纯标准库） |
| `scripts/build_noninferiority_workbook.py` | results.json → 多子表 Excel |
| `scripts/selfcheck_output.py` | 交付稿自检 + 官方值三方对账 |
| `assets/tvax_009b_phase1_spec.json` | 可直接复制改的完整规格样例 |
| `references/stat_methods.md` | 统计口径与公式 |
| `references/deliverable_format.md` | Excel 版式与说明页模板 |
| `references/case_tvax_009b_phase1.md` | 案例：Ⅰ期 全 PPS/FAS 重算路线 |
| `references/case_tvax_009_phase2.md` | 案例：Ⅱ期 FAS 走 LOCF、只能引用官方值 |

## Pre-flight Check

Before executing, the agent MUST:
1. Verify input file exists at the expected path
2. Clear any cached results from previous runs
3. Confirm required environment variables are set

## Post-execution Validation

After execution, the agent MUST:
1. Verify output file was created successfully
2. Run applicable validator (if available)
3. Report results in standardized Markdown table format
