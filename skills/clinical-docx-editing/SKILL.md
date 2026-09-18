---
name: clinical-docx-editing
description: Batch-edit Word .docx files at OOXML level - remove unused custom styles and normalize Chinese style names, or run batch find/replace across body, tables, headers and footers. Use when the user asks for "Word 样式清理 / 批量替换 docx / 占位符替换 / 研究编号 替换 / 页眉页脚 替换 / 日期占位符".
license: MIT
compatibility: Requires Python 3.10+ with python-docx, lxml and PyYAML. Both modules rewrite documents in place, so back up before running.
allowed-tools: Read Write Edit Bash
metadata:
  version: "1.0"
  skill-author: Scientific Skills for Clinical Trial Contributors
  last-reviewed: "2026-09-18"
---

# Word 文档批量编辑

## 一、样式清理与命名规范化

脚本：`scripts/clinical-automation/10_Word_Style_Cleaner/word_style_cleaner.py`

只删除**未使用的自定义样式**（内置样式保留不动），并对保留样式做中文命名规范化
（标题 / 正文 / 表格 / 题注等）。

```bash
cd scripts/clinical-automation/10_Word_Style_Cleaner
python word_style_cleaner.py --input "input" --output "output" --overwrite
```

写入时保留 `styles.xml` 原始命名空间声明，并处理样式继承依赖与孤儿引用，
以降低 Word 打开时弹出「修复」对话框的风险。
输出 `*_styles_cleaned.docx` 与报告。

## 二、OOXML 批量文本替换

脚本：`scripts/clinical-automation/11_Word_Text_Replace/`

对 CSR / 方案等 docx 做批量查找替换（日期占位符、研究编号、固定短语等），
覆盖**正文、表格、页眉页脚**，支持**跨 run 拆分**的文本。

```bash
cd scripts/clinical-automation/11_Word_Text_Replace
python replace_docx.py --yes
python util_check_docx.py --latest        # 输出校验，务必跑
```

替换规则写在 `replace_rules.example.yaml`（复制后修改）。
核心实现在 `lib/ooxml_replace.py`。

## 输入 / 输出约定
- 输入：各模块 `input/`（不入库）
- 输出：`*_styles_cleaned.docx` / `*_updated.docx` 写入各模块 `output/`

## 依赖
`python-docx`、`lxml`、`PyYAML`

## 注意事项
- **改前先备份**：这两个模块都是原地改写文档，Word 不提供撤销
- 样式清理只删「未使用」的自定义样式，但样式继承关系复杂，
  建议先小批量试跑再放开全量
- 跨 run 替换能处理被格式打断的文本，但仍建议替换后用
  `util_check_docx.py --latest` 逐项核对
- 与 `word-audit-report-format` 技能配合：先用本技能改内容，再按那个技能统一字体
