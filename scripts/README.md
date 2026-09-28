# scripts/

仓库级可执行脚本入口。

## 目录组织

```
scripts/
├── pipeline/                       # 模块化数据处理管线（核心架构）
│   ├── ingest/                     #   文档读取（docx/pdf/pptx/xlsx）
│   ├── extract/                    #   表格/文本提取 & 规范化
│   ├── transform/                  #   数据清洗 / 临床 RAG
│   ├── convert/                    #   格式转换（→ Markdown）
│   ├── export/                     #   生成 Word/PPT 输出
│   └── validate/                   #   AST / 编码 / PPTX 校验
├── _tools/                         # 内部审计 / 自检 / 维护脚本
├── utils/                          # 跨模块共享帮助函数
├── literature_tools/               # 文献检索客户端
├── clinical-automation/            # 外部子项目（只读，勿修改）
├── _archive/                       # 已归档的一次性脚本（不追踪）
└── _archive_2026_consolidation/    # 2026 大整合归档（不追踪）
```

## 核心管线模块 (`pipeline/`)

| 模块 | 功能 | 主要依赖 |
|------|------|----------|
| `ingest/docx_reader.py` | 读取 Word 文档结构与文本 | python-docx |
| `ingest/pdf_reader.py` | 读取 PDF 文档 | pypdf, pdfplumber |
| `ingest/pptx_reader.py` | 读取 PowerPoint 演示文稿 | python-pptx |
| `ingest/xlsx_reader.py` | 读取 Excel 工作簿 | openpyxl |
| `extract/table_extractor.py` | 从文档中提取结构化表格 | — |
| `extract/text_normalizer.py` | 文本规范化处理 | — |
| `transform/clinical_rag.py` | 临床数据 RAG 转换 | — |
| `convert/convert_to_md.py` | 多格式 → Markdown 转换 | markitdown, striprtf |
| `export/docx_builder.py` | 程序化生成 Word 文档 | python-docx |
| `export/pptx_builder.py` | 程序化生成 PPT 文档 | python-pptx |
| `validate/ast_validator.py` | Python AST 语法验证 | stdlib |
| `validate/encoding_validator.py` | 文件编码验证 | stdlib |
| `validate/pptx_validator.py` | PPTX 结构验证 | python-pptx |

## 内部工具 (`_tools/`)

| 脚本 | 功能 |
|------|------|
| `generate_skills_index.py` | 重新生成 `SKILLS_INDEX.md` |
| `inject_skill_sop.py` | 为核心 Skill 注入 Pre-flight / Post-execution SOP |
| `skill_dedupe_report.py` | Skills 去重报告 |
| `validate_skills_registry.py` | 校验 Skills 注册表完整性 |
| `audit_skills.py` | Skills 审计 |
| `scan_imports.py` | 扫描 import 依赖 |
| `validate_codebase.py` | 代码库质量验证 |
| `project_self_check.py` | 项目自检（外部命令可用性 + 冒烟测试） |
| `fix_skills_frontmatter.py` | 修复 SKILL.md YAML Frontmatter |
| `fix_unused_imports.py` | 清理未使用的 import |
| `fix_fstrings_broad.py` | f-string 修复 |
| `audit_robustness_smells.py` | 代码健壮性审计 |
| `cleanup_generated_artifacts.py` | 清理可重建产物 |

## 用法

```bash
# 转换 Word 为 Markdown
python scripts/pipeline/convert/convert_to_md.py input.docx -o output.md

# 项目自检
python scripts/_tools/project_self_check.py

# 重新生成 Skills 索引
python scripts/_tools/generate_skills_index.py

# 注入 SOP 到核心 Skills
python scripts/_tools/inject_skill_sop.py --write
```

## 约定

- Python ≥ 3.10，使用 `from __future__ import annotations`
- 第三方依赖必须显式声明 import 错误提示
- 不在仓库级产生可重建 artifacts（已通过 `.gitignore` 过滤）
- 已归档的历史脚本保存在 `_archive/` 下，仅作参考，不纳入版本追踪
- `clinical-automation/` 为外部子项目，保持只读，详见根 `AGENTS.md` §3.1
