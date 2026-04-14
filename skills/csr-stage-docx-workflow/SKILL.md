---
name: csr-stage-docx-workflow
description: Generates a phase/stage clinical study report (阶段性小结/CSR) as a Word .docx by strictly following a reference “shell” docx chapter structure and auto-filling key tables from PDF TLFs. Use when the user asks to “严格按照某docx章节结构重写/生成阶段性小结/重新生成CSR/导出docx”，especially on Windows with Chinese filenames (8.3 short names), and when sources include safety/immunogenicity/baseline PDFs.
---

# CSR 阶段性小结（Shell结构 + PDF自动填数）工作流

## 目标

在 **Windows** 环境下，基于：

- **结构参照**：`review_materials/...阶段性小结-shell...docx`（章节结构必须严格一致）
- **数据来源**：`review_materials/*.pdf`（人口学及基线、免疫原性、安全性part1/part3等）

生成可重复的 `.docx` 输出（默认输出到 `docs/`），并可持续迭代抽数规则。

## 现有实现入口（默认）

- 生成脚本：`scripts/generate_csr_docx.py`
- 依赖：`requirements.txt`（至少包含 `python-docx`、`pymupdf`）

运行命令：

```bash
python scripts/generate_csr_docx.py --root "项目根目录"
```

输出位置：

- `docs/CSR_ICH-E3_YDSWX_TVAX-006-002-II_阶段性_YYYY-MM-DD.docx`

## 工作流清单（严格按顺序）

### 1) 处理结构参照 docx（解决中文文件名/编码）

- **优先策略**：用 `cmd dir /x` 获取 8.3 短文件名，再用短名访问文件。

示例：

```bat
cmd /c "dir /x E:\Cursor Project\Scientific-Skills-for-Clinical_Trial\review_materials"
```

找到类似 `YDSWX~1.DOC` 的短名后，用它作为稳定路径输入。

### 2) 抽取“章节结构树”（用于强约束输出结构）

将参照 shell docx 转为文本（Markdown）以便解析目录/标题层级：

```bash
python -m markitdown "E:\...\review_materials\YDSWX~1.DOC" -o "E:\...\review_materials\_converted\shell.md"
```

抽取要点：

- **一级标题顺序**：标题页 → 摘要 → 1 概述 → 2 基线 → 3 免疫原性 → 4 安全性 → 5 讨论结论 → 6 参考文献
- **二级/三级标题**：如 `2.1–2.6`、`3.1–3.4`、`4.1–4.4`

要求：

- 输出 docx 的章节顺序与层级 **必须与 shell 完全一致**（允许内容占位，但不可增删/乱序）。

### 3) 定位并抽取 PDF 关键表格数据（优先用 PyMuPDF）

默认约定：PDF 放在 `review_materials/` 下；脚本会按文件名关键词自动定位：

- 人口学及基线：包含“人口学”“基线”
- 免疫原性：包含“免疫原性”
- 安全性 part1：包含“安全性分析”“part1”
- 安全性 part3：包含“安全性分析”“part3”

抽取策略（稳健性优先）：

- **优先锚点**：表号（如 `表格14.3.1.1.1`）+ 稳定 ASCII 片段（如 `40~49`、`VS`）
- **避免脆弱点**：直接依赖中文行名（部分环境会乱码）
- **最小化扫描页数**：表号通常靠前的，限制 max_pages；必要时扩大窗口

### 4) 生成 docx（python-docx）并强制字体

要求：

- 中文（东亚字体）：宋体
- 英文：Times New Roman

脚本内需对 `Normal/Title/Heading 1-3/Table Grid` 等样式做全局字体强制。

### 5) 校验（结构优先，其次数据）

生成后快速核对：

- **目录结构**：是否与 shell 的一级/二级标题一致
- **关键表**：受试者分布、免疫原性两表、0–14天安全性汇总、分层3级及以上、0–30天非征集性
- **追溯行**：每张表后是否有“数据来源：xxx（表号）”

## 常见问题处理

### A. 中文文件名导致找不到文件/乱码

- 使用 `cmd dir /x` 获取短名（8.3），用短名访问/复制/转换。

### B. `markitdown` 转换慢

- 优先只对 **shell结构docx** 转换；PDF 抽数优先走 `pymupdf`（无需全量转md）。

### C. PDF抽取正则不命中

处理顺序：

- 先用 PyMuPDF 打印包含表号页面的前 1–2 页文本片段
- 调整锚点：从中文词切换为表号/年龄段/数字模式
- 将规则写成“可回归”的函数（固定输入 PDF → 固定输出字段）

## 可迭代扩展点（后续优化方向）

- 将“章节树抽取”自动化：从 shell.md 解析出标题数组，再由生成器按数组渲染
- 将更多占位段落用PDF表/清单补齐（如：2.2 分析集、2.3 人口学、4.2 SOC/PT细表等）
- 增加 `--shell-docx` 参数：允许用户指定任意结构参照docx

