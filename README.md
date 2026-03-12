# K-Dense-AI-for-Clinical_Trial

临床试验 / 临床研究 AI 辅助系统（仓库核心内容：`skills/`）。

## 项目定位

本仓库维护一组面向临床研究与临床试验的 AI skills/技能，覆盖临床试验检索、循证/决策支持、临床报告与合规文档、统计与建模、生存分析、可解释性，以及常用医学/科研数据库访问等工作流。

## 快速开始

### 环境要求

- **Python**：3.10+（CI 当前使用 3.10）
- **AI 客户端**：Cursor / Claude Code / Codex（需要支持 skills 机制）

### 安装（Python 依赖）

```bash
python -m pip install -r requirements.txt
```

### 安装（skills 到客户端）

如果你的客户端支持“直接引用项目目录”，推荐直接指向本仓库的 `skills/`；否则可复制到客户端的全局 skills 目录。

Windows（PowerShell）示例：

```powershell
$dst = Join-Path $env:USERPROFILE ".cursor\skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force ".\skills\*" $dst
```

macOS/Linux（bash）示例：

```bash
mkdir -p ~/.cursor/skills
cp -r ./skills/* ~/.cursor/skills/
```

## 仓库结构（长期维护版）

```
K-Dense-AI-for-Clinical_Trial/
├── skills/                # 每个 skill 一个目录（核心内容）
├── docs/                  # 长文档（索引见 docs/README.md）
├── scripts/               # 仓库级可执行脚本入口
├── reports/               # 生成产物（默认不入库；见 .gitignore）
├── tests/                 # 测试
├── requirements.txt
├── requirements-dev.txt
└── CONTRIBUTING.md
```

维护约定与更详细解释见 `docs/repo_layout.md`。

## 常用入口

- **Skills 导览（推荐工作流）**：`docs/skills_guide.md`
- **Skills 清单与 prompt 模板**：`docs/skills_catalog.md`
- **贡献指南**：`CONTRIBUTING.md`

## 示例：生成一份 docx 报告（本地产物）

```bash
python scripts/generate_norovirus_review_docx.py
```

生成的 `.docx` 默认输出到 `reports/`，该目录下的二进制产物默认不会被提交（见 `.gitignore`）。

## 来源与归属（合规声明）

- **上游项目**：本仓库从 [`K-Dense-AI/claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills.git) 提取并裁剪出更聚焦“临床研究/临床试验”场景的一部分 skills。
- **许可证**：上游与本仓库均为 MIT License；本仓库在再分发时保留上游版权与许可声明。
- **改动范围（摘要）**：删除与临床研究无关的 skills/文档，仅保留并重组与临床研究相关的 skills；补充本仓库的目录规范、依赖与 CI。
- **非背书声明**：本仓库为社区维护的裁剪/整理版本，不代表上游作者或组织的官方立场、认证或背书。

## 许可证

本项目采用 MIT 许可证，详见 `LICENSE.md`。

注意：各 skill 可能有独立许可证或对外部数据源/SDK 有额外限制，使用前请查看对应 skill 的 `SKILL.md`。

另见：`THIRD_PARTY_NOTICES.md`（外部数据源/第三方条款提醒）。
