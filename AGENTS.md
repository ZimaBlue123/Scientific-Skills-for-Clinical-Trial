# Workspace & Agent Guidelines

## 1. 操作范围限制 (Workspace Boundary - Strict)

- **项目根目录**：当前仓库目录 (`e:/Cursor Project/2-Scientific-Skills-for-Clinical_Trial`)。
- **强制规则**：后续所有任务的操作（包括读取、创建、修改、删除文件以及命令执行）必须**严格限制在当前项目根目录及其子目录内**。
- **绝对禁止**：严禁创建、修改、删除或影响项目文件夹之外的任何文件或系统路径。

## 2. Git 提交信息规范 (Git Commit Convention - Strict)

- **语言规范**：所有 Git 提交信息（Commit Messages）**必须优先/尽量采用英文表述（English-first）**。
- **格式标准**：遵循 Conventional Commits 规范（例如 `feat:`, `fix:`, `refactor:`, `chore:`, `audit:` 等），语义清晰、简明扼要。

## 3. 脚本文件管理机制 (Script Management - Strict)

- **统一归档**：所有生成的 Python 脚本 (`.py` 文件) **必须且只能** 存放在 `scripts` 文件夹中。绝对禁止在根目录或其他非归档目录中散落临时脚本。
- **迭代清理机制**：在执行多轮迭代任务时（例如 V1 到 V10 版本的生成），一旦确认生成了最终版（Final/Latest），Agent **必须主动清理** 之前的过渡废弃脚本（如 `_v1.py` 至 `_v9.py` 等中间产物），只保留最终的执行脚本并进行重命名定档（如 `generate_[topic]_final.py`）。
- **文件命名规范**：脚本文件应具有自描述性（Self-descriptive），拒绝含糊不清的名称（如单纯的 `test.py` 或 `gen_docx.py`），应当准确指代其生成的报告内容。
