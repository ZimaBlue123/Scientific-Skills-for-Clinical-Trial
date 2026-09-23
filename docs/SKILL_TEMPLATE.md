---
name: <skill-folder-name>
description: <Concise trigger-friendly description, max 1024 chars. Include both English and Chinese keywords if applicable.>
license: MIT
compatibility: Requires Python >=3.10 with <specific packages>
allowed-tools: Read Write Edit Bash
metadata:
  version: "1.0.0"
  skill-author: "<Author Name>"
  last-reviewed: "YYYY-MM-DD"
---

<!-- ============================================================
  SKILL TEMPLATE — Scientific Skills for Clinical Trial
  Two variants below: choose the one that fits your skill type.
  Delete the variant you don't use.
============================================================ -->

<!-- ======================= VARIANT A ==========================
  For upstream scientific / modeling skills (English, detailed)
================================================================= -->

# <Skill Display Name>

## Overview

Brief description of what this skill does and what problem it solves.

## When to Use This Skill

- Trigger scenario 1
- Trigger scenario 2
- **Do NOT use** when: <alternative skill recommendation>

## Quick Start

```bash
python scripts/<entry_script>.py --help
```

## Core Capabilities

### Capability 1

Description and usage example.

### Capability 2

Description and usage example.

## Pre-flight Check

Before executing, the agent MUST:
1. Verify input file exists at the expected path
2. Clear any cached results from previous runs
3. Confirm required environment variables are set

## Post-execution Validation

After execution, the agent MUST:
1. Verify output file was created successfully
2. Run applicable validator (e.g., `check_pptx_overflow.py`)
3. Report results in standardized Markdown table format

## Output Format

Results should be reported as:

| Field | Value |
|-------|-------|
| Input | `<input_path>` |
| Output | `<output_path>` |
| Status | ✅ Success / ❌ Failed |
| Details | <summary> |

## Best Practices & Pitfalls

- ⚠️ Common mistake 1
- ⚠️ Common mistake 2

---

<!-- ======================= VARIANT B ==========================
  For clinical automation adapter skills (Chinese-first, concise)
================================================================= -->

# <技能显示名>

## 适用场景

当用户要求「<中文触发关键词>」或需要 <功能描述> 时触发。

## 脚本位置

```
scripts/clinical-automation/<XX_module>/
├── <main_script>.py
└── requirements.txt
```

## 用法 / 运行命令

```bash
python scripts/clinical-automation/<XX_module>/<main_script>.py \
    --input <input_path> \
    --output <output_path>
```

## 环境变量（必配 / 选配）

| 变量名 | 必选 | 说明 |
|--------|------|------|
| `API_TOKEN` | ✅ | OpenAI-compatible API token |

## 输入 / 输出约定

- **输入目录**: `input/` (相对于脚本运行目录)
- **输出目录**: `output/` (自动创建)

## 依赖与合规

- 依赖安装: `pip install -r scripts/clinical-automation/<XX_module>/requirements.txt`
- ⚠️ 不得将含有受试者数据的文件提交到 Git

## 注意事项

1. 运行前确认输入文件编码为 UTF-8
2. Windows 环境下中文路径需使用 8.3 短名称
3. 输出结果需人工审核后方可用于正式报告
