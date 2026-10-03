# Workspace & Agent Guidelines

## 1. 操作范围限制 (Workspace Boundary - Strict)

- **项目根目录**：当前仓库目录 (`e:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial`)。
- **强制规则**：后续所有任务的操作（包括读取、创建、修改、删除文件以及命令执行）必须**严格限制在当前项目根目录及其子目录内**。
- **绝对禁止**：严禁创建、修改、删除或影响项目文件夹之外的任何文件或系统路径。

## 2. Git 提交信息规范 (Git Commit Convention - Strict)

- **语言规范**：所有 Git 提交信息（Commit Messages）**必须优先/尽量采用英文表述（English-first）**。
- **格式标准**：遵循 Conventional Commits 规范（例如 `feat:`, `fix:`, `refactor:`, `chore:`, `audit:` 等），语义清晰、简明扼要。

## 3. 脚本文件管理机制 (Script Management - Strict)

- **统一归档与写入拦截 (Write Pre-Check)**：所有生成的 Python 脚本 (`.py` 文件) **必须且只能** 存放在 `scripts` 文件夹中。**【强制动作】：在调用任何写入文件或创建文件的工具（如 write_to_file）之前，Agent 必须进行路径校验（Pre-Check）—— 若目标路径不包含 `scripts/`，则严禁执行写入并必须自行修正路径。** 绝对禁止在根目录或其他非归档目录中散落临时脚本。
- **迭代清理机制**：在执行多轮迭代任务时（例如 V1 到 V10 版本的生成），一旦确认生成了最终版（Final/Latest），Agent **必须主动清理** 之前的过渡废弃脚本（如 `_v1.py` 至 `_v9.py` 等中间产物），只保留最终的执行脚本并进行重命名定档（如 `generate_[topic]_final.py`）。
- **文件命名规范**：脚本文件应具有自描述性（Self-descriptive），拒绝含糊不清的名称（如单纯的 `test.py` 或 `gen_docx.py`），应当准确指代其生成的报告内容。

### 3.1 豁免：vendored 子项目 `scripts/clinical-automation/`

该目录是从 `ZimaBlue123/Clinical-Data-Automation` **整体迁入的外部子项目**
（保留完整提交历史），以下规则在**该目录内部不适用**：

| 规则 | 在子目录内的处理 |
|---|---|
| 脚本必须自描述命名 | 不适用：保留原有 `01_` … `34_` 编号目录与原有文件名 |
| 迭代清理过渡脚本 | 不适用：不得删除子目录内的任何脚本来"清理" |
| 依赖统一在根 `requirements.txt` | 不适用：子目录使用自己的 `requirements.txt`，**禁止**合并进根目录 |
| 根 `README.md` / `AGENTS.md` 覆盖 | 子目录有自己的同名文件，二者互相独立 |

- **约束**：新增脚本**不得**放进该子目录；它只作为只读能力库使用。
- **规则冲突时**：一律以本文件（仓库根 `AGENTS.md`）为准，子目录内的 `AGENTS.md` 仅作参考。
- **能力入口**：`skills/clinical-*`、`skills/document-format-convert` 等 SKILL.md
  是调用这些脚本的推荐入口，**不要绕过它们直接改子目录里的脚本**。

## 4. 强制代码与技能复用 (Mandatory Code & Skill Reuse)

- **核心原则**：严禁在未排查现有资产的情况下“重复造轮子”（Reinventing the wheel）。
- **执行 SOP (Pre-Flight Check)**：在着手编写任何新脚本或提供复杂解决方案之前，Agent **必须强制执行**以下前置排查：
  1. **排查脚本库**：使用 `find_by_name`、`grep_search` 或 `list_dir` 搜索 `scripts/`（及其子目录 `pipeline/`、`utils/`、`literature_tools/`、`_tools/` 等）中是否已存在类似功能的脚本（如 Office 处理、PDF 解析、数据对齐）。
  2. **查阅内置技能**：浏览 Agent 提示词中提供的 `<skills>` 列表，确认是否有官方或项目定制的 Skill 可直接处理该任务。
- **扩展与优化**：只有在确认现有工具库无法直接满足需求时，才允许基于现有通用模块（如 `scripts/pipeline/ingest/docx_reader.py`、`scripts/pipeline/extract/table_extractor.py`）进行扩展开发；除非是全新的独立业务逻辑，否则避免从零开始写新文件。

## 5. 严格输出与认知护栏 (Strict Output & Cognitive Guardrail)
- **无废话原则 (Zero-Filler)**：在处理临床数据提取、报告审查或与自动化管道交互时，Agent 必须直接输出结果。严禁使用诸如 Here is the..., Hope this helps! 等过渡性或客套话。若需要输出 JSON/代码，必须且只能输出代码块，防止破坏下游的 Parser。
- **强制指令**：全面应用 skills/clinical-strict-extractor 规范，所有多步任务必须量化并编号。确保内容高信噪比。

## 6. 批量操作安全协议 (Batch Operation Safety Protocol - Strict)

> **背景**：2026-10-03 事故复盘——一次批处理正则替换脚本对 150+ 个 `SKILL.md` 文件执行了未经验证的写入，导致三轮连续 CI 失败（YAML 畸形值、字段错位、换行吞噬）。以下规则旨在永久杜绝此类问题。

### 6.1 批量写入前置验证 (Pre-Write Validation — Mandatory)

当 Agent 需要对 **≥3 个文件** 执行批量修改（包括正则替换、模板注入、frontmatter 重写等）时，**必须**按以下 SOP 执行：

1. **Dry-Run 先行**：先在 ≤3 个样本文件上执行修改并打印 diff，肉眼确认输出符合预期后，再扩展到全量文件。
2. **结构化后验证 (Post-Write Spot Check)**：全量修改完成后、`git add` 之前，**必须**至少抽查 3 个代表性文件（首个、中间、末尾）的关键修改区域，确认无畸形输出。
3. **YAML 专项校验**：若修改涉及 YAML frontmatter，必须对修改后的文件执行以下检查：
   - `---` 开闭标记各自独占一行
   - 所有 `key: value` 的冒号后有空格
   - 含特殊字符的值已加双引号（如 `skill-author: "K-Dense Inc."`）
   - 字段层级正确（如 `version` 在 `metadata:` 缩进下）

### 6.2 正则替换防御性编码 (Defensive Regex Rules)

- **禁止贪婪通配**：涉及文件结构边界（如 `---`）的正则，必须使用非贪婪匹配 (`*?`) 并显式锚定行首/行尾。
- **保留换行**：任何 `re.sub` 替换的 `ReplacementContent` 必须显式保留原始内容中的换行符 `\n`，严禁隐式吞掉行边界。
- **避免多层引号嵌套**：替换结果中不得产生连续双引号 (`""`) 或引号缺失，替换后应断言引号配对正确。

### 6.3 推送前 CI 预演 (Pre-Push Gate)

- 若项目配有 CI 测试（如 `.github/workflows/skill-tests.yml`），在 `git push` 前应优先在本地执行等效验证（如运行 `python tests/_meta/test_skill_structure.py`），或至少确认修改文件的 YAML 可被 `python -c "import yaml; yaml.safe_load(open(...))"` 正常解析。
- **严禁盲推 (No Blind Push)**：禁止在批量修改后未经任何验证直接执行 `git push`。

