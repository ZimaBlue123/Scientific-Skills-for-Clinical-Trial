# scripts/

仓库级可执行脚本与模块化管线入口。

> **快速检索与复用机制 (`AGENTS.md` §4)**：编写任何新脚本前，请先查阅 [`SCRIPTS_INDEX.md`](./SCRIPTS_INDEX.md) 或执行关键词检索：
> ```bash
> python scripts/_tools/generate_scripts_index.py --search <keyword>
> ```

## 目录组织

```
scripts/
├── SCRIPTS_INDEX.md                # 全局脚本能力与快速复用索引（自动生成）
├── pipeline/                       # 模块化数据处理管线（核心架构）
│   ├── ingest/                     #   文档读取（docx/pdf/pptx/rtf/xlsx）
│   ├── extract/                    #   表格/流式解析/修订文本/旧版 .doc 提取 & 规范化
│   ├── transform/                  #   统计置信区间/分位数对齐/数据清洗/临床 RAG
│   ├── convert/                    #   格式转换（.doc → .docx / 多格式 → Markdown）
│   ├── export/                     #   生成 Word/PPT 输出 & 刷新目录域
│   ├── literature/                 #   文献检索与批量下载客户端
│   ├── review/                     #   文档审查、交叉引用核查与包级比对 (diff)
│   └── validate/                   #   AST / 编码 / 清洁版 / TOC / PPTX 校验
├── _tools/                         # 内部审计 / 索引生成 / 自检 / 维护脚本
└── clinical-automation/            # 外部子项目（只读，勿修改）
```

## 核心管线模块 (`pipeline/`)

| 模块 | 功能 | 主要依赖 |
|------|------|----------|
| `ingest/docx_reader.py` | 读取 Word 文档结构与文本 | python-docx |
| `ingest/pdf_reader.py` | 读取 PDF 文本与结构化表格 | pypdf, pdfplumber |
| `ingest/pptx_reader.py` | 读取 PowerPoint 演示文稿与备注 | python-pptx |
| `ingest/rtf_reader.py` | 解析 SAS/临床 TFL RTF 文本与二维表格 | stdlib |
| `ingest/xlsx_reader.py` | 读取 Excel 工作簿 | openpyxl |
| `extract/batch_extract_materials.py` | 将资料目录（docx/pptx/xlsx/pdf）批量抽取为平行 .txt 树并输出清单 | python-docx, python-pptx, openpyxl, PyMuPDF |
| `extract/extract_docx_tracked_text.py` | 零依赖提取含修订痕迹 (`w:ins`/`w:del`) 的 `.docx` 文本与表格 | stdlib |
| `extract/extract_legacy_doc_text.py` | 通过 Word COM 批量提取旧版 `.doc` 文本与表格 | pywin32 |
| `extract/table_extractor.py` | 从文档中按表头关键词提取结构化表格 | stdlib |
| `extract/stream_docx_tables.py` | 基于 lxml iterparse 流式提取超大 .docx 表格与段落为 TSV | lxml |
| `extract/text_normalizer.py` | 编码检测、乱码诊断与空白字符规范化 | stdlib |
| `transform/clinical_rag.py` | 临床文档本地 TF-IDF 检索索引 | scikit-learn, numpy |
| `transform/immunogenicity_stats.py` | 疫苗临床 TFL 免疫原性统计与桥接样本量/把握度计算（Clopper-Pearson、Newcombe-Wilson、Farrington-Manning 评分检验、GMC 对数均值差非劣效、GMC 非劣蒙特卡洛通过率模拟 `simulate_gmc_ni_pass_rate`） | scipy, numpy |
| `transform/rate_ci_methods.py` | 二项率与率差 95% 置信区间方法库（对齐 SAS PROC FREQ / RISKDIFF） | stdlib |
| `transform/quantile_definitions.py` | 样本分位数定义库（精确复现 SAS PCTLDEF 1~5、Tukey hinges 与线性插值） | stdlib |
| `convert/convert_doc_to_docx.py` | 旧版二进制 `.doc` 转 `.docx` | pywin32 |
| `convert/convert_to_md.py` | 多格式 → Markdown 转换（支持段落/表格锚点编号） | markitdown, striprtf |
| `export/docx_builder.py` | 程序化生成 Word 文档、中英文字体规范化、OOXML 批注无损清除 (`strip_docx_comments`)、保格式段落/单元格文本替换 (`set_para_text_preserving_rpr`, `set_cell_single_text`) 与表格防跨页断行 (`enable_table_row_cant_split`) | python-docx |
| `export/pptx_builder.py` | 程序化生成 PPT 文档与高亮批量移除 (`strip_pptx_highlights`) | python-pptx |
| `export/update_docx_toc_fields.py` | 通过 Word COM 自动更新 `.docx` 目录域与页码 | pywin32 |
| `review/audit_protocol_crossrefs.py` | 核查方案 `.docx` 内部章节号与图表交叉引用 | python-docx |
| `review/audit_protocol_numeric_consistency.py` | 核查编号版方案 Markdown 占位符、单位与关键数值一致性 | stdlib |
| `review/scan_protocol_text_quality.py` | 扫描方案 Markdown 标点混用、笔误与排版质量缺陷 | stdlib |
| `review/compare_docx_content.py` | 逐包、逐块、逐样式比对两份 `.docx` 文档 | lxml |
| `review/compare_pptx_package.py` | 校验修改前后 `.pptx` 内部构件完整性 | stdlib |
| `validate/ast_validator.py` | Python AST 健壮性反模式检查 | stdlib |
| `validate/docx_clean_validator.py` | 校验 `.docx` 清洁版合规性（红蓝字、高亮、批注） | python-docx, lxml |
| `validate/docx_toc_validator.py` | 无损副本渲染核验 `.docx` 目录域与首页截图 | pywin32, PyMuPDF |
| `validate/encoding_validator.py` | 文件 UTF-8 BOM 与乱码验证 | stdlib |
| `validate/pptx_overflow_checker.py` | PowerPoint COM 实测表格单元格文字溢出与表格底边越界（防结论框遮挡） | pywin32 |
| `validate/pptx_validator.py` | PPTX 文本框越界检测 | python-pptx |

## 内部工具 (`_tools/`)

| 脚本 | 功能 |
|------|------|
| `generate_scripts_index.py` | 自动生成 `scripts/SCRIPTS_INDEX.md` 并支持 `--search` 关键词快速检索 |
| `generate_skills_index.py` | 重新生成 `SKILLS_INDEX.md` |
| `inject_skill_sop.py` | 为核心 Skill 注入 Pre-flight / Post-execution SOP |
| `skill_dedupe_report.py` | Skills 去重检测报告 |
| `validate_skills_registry.py` | 校验 Skills 注册表完整性 |
| `project_self_check.py` | 项目自检（外部命令可用性 + CLI 冒烟测试） |
| `fix_skills_frontmatter.py` | 修复 `SKILL.md` YAML Frontmatter |
| `fix_skill_broken_links.py` | 修复 `SKILL.md` 内部失效脚本链接 |
| `fix_unused_imports.py` | 清理未使用的标准库 import |
| `fix_fstrings_broad.py` | 清理无占位符的冗余 f-string |
| `audit_robustness_smells.py` | AST 级代码健壮性与坏味道审计 |
| `audit_missing_encoding.py` | 审计缺失 `encoding=` 参数的文本读写调用 |
| `inspect_docx_structure.py` | 快速导出 `.docx` 段落/表格索引结构与文本摘要 |
| `inspect_docx_word_stats.py` | 通过 Word COM 只读读取 `.docx` 页数、字数、批注与目录条目 |
| `preview_docx.py` | 通过 Word COM + PyMuPDF 渲染 `.docx` 为 PDF 与分页 PNG 以供版式目视质检 |
| `preview_xlsx.py` | 通过 Excel COM + PyMuPDF 渲染 `.xlsx` 打印版式为 PDF 与分页 PNG |
| `sync_toc_page_numbers.py` | 通过 Word COM 分页探测并无损回写 `.docx` 静态目录缓存页码 |
| `cleanup_generated_artifacts.py` | 清理可重建产物与 IDE 历史缓存 |
| `ocr_winrt.ps1` | 调用 Windows 内置 OCR（Windows.Media.Ocr / WinRT）识别扫描图片文本，零第三方依赖 |

## 常用命令

```bash
# 快速检索可复用脚本
python scripts/_tools/generate_scripts_index.py --search docx

# 重新生成脚本索引与技能索引
python scripts/_tools/generate_scripts_index.py
python scripts/_tools/generate_skills_index.py

# 代码健壮性审计
python scripts/_tools/audit_robustness_smells.py
```

## 约定

- Python ≥ 3.10，使用 `from __future__ import annotations`
- 第三方依赖必须显式声明 import 错误提示
- 不在仓库级产生可重建 artifacts（已通过 `.gitignore` 过滤）
- 一次性特定批次脚本完成后，其通用算法沉淀进 `pipeline/`，不保留历史垃圾脚本
- `clinical-automation/` 为外部子项目，保持只读，详见根 `AGENTS.md` §3.1
