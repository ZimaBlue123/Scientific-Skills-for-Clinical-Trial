---
name: clinical-sae-extraction
description: Extract structured SAE (serious adverse event) fields from clinical PDF/TXT/DOCX/Excel materials into an Excel listing. Use when the user asks for "SAE 抽取 / 严重不良事件 结构化 / SAE 列表 / SAE 汇总 Excel" or needs to consolidate SAE fields from mixed-format source documents.
license: MIT
compatibility: Requires Python 3.10+ and an OpenAI-compatible Chat Completions endpoint with a valid API token. Never commit real patient data or tokens.
allowed-tools: Read Write Edit Bash
metadata:
  version: "1.0"
  skill-author: Scientific Skills for Clinical Trial Contributors
  last-reviewed: "2026-09-18"
---

# SAE 结构化抽取

## 适用场景
- 从临床文本、PDF、DOCX、Excel 中抽取严重不良事件（SAE）字段
- 把多份来源的 SAE 汇总成一份 Excel 列表

## 脚本位置
`scripts/clinical-automation/33_SAE_Extractor/cli.py`

## 用法
```bash
cd scripts/clinical-automation/33_SAE_Extractor
python cli.py self-check   # 先自检：环境与 API 连通性
python cli.py batch        # 批量处理 input/ 下的文本类文件
python cli.py pdf-batch    # 批量处理 PDF
```

## 环境变量（必配）
```powershell
$env:SAE_API_TOKEN = "<your token>"
```
可选：`SAE_API_BASE_URL`、`SAE_MODEL_ID`、`TESSERACT_CMD`、`POPPLER_PATH`

仓库内提供了两个 PowerShell 辅助脚本：
- `scripts/clinical-automation/scripts/set_env.ps1`：设置 `SAE_API_BASE_URL`、`SAE_OUTPUT_DIR`
- `scripts/clinical-automation/scripts/start_tunnel.ps1`：SSH 本地端口转发（需 `SAE_TUNNEL_SSH_HOST`）

## 输入 / 输出约定
- 输入：`33_SAE_Extractor/input/`（临床文本 / PDF / DOCX / Excel）
- 输出：SAE 列表 xlsx，写入 `33_SAE_Extractor/output/`

## 依赖与合规
- 调用 **OpenAI 兼容的 Chat Completions 接口**，需要有效的 API Token
- 该模块自独立项目 **SAE-Extractor** 迁入，附加版权声明见
  `scripts/clinical-automation/LICENSE.md`
- ⚠️ **严禁**把真实患者数据或 API Token 提交进仓库；`input/` 与 `output/` 已在
  `scripts/clinical-automation/.gitignore` 中排除，`24_File_Translator/.env` 同样被排除

## 注意事项
- 抽取结果属于**辅助初筛**，医学判定必须由人工复核后确认
- 先跑 `self-check` 再跑 `batch`，可避免大批任务跑到一半才发现配置问题

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
