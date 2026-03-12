## 仓库目录规范（长期维护版）

本仓库的核心交付是 `skills/` 下的一组技能目录；其余目录用于脚本、文档与生成物的组织。

## 目录约定

```
Scientific-Skills-for-Clinical_Trial/
├── skills/                    # 每个 skill 一个目录（核心内容）
├── docs/                      # 长文档（面向使用者/维护者）
├── scripts/                   # 仓库级可执行脚本入口（不属于某个 skill）
├── reports/                   # 生成产物（默认不入库；见 .gitignore）
├── tests/                     # 测试（至少保证 CI 能跑通）
├── requirements.txt           # 运行时依赖（CI 与本地对齐）
├── requirements-dev.txt       # 开发依赖（lint/test）
└── README.md                  # 入口文档（短、稳定、指向 docs）
```

## 贡献约定（摘要）

- **新增 skill**：在 `skills/<skill-name>/` 下建立目录，至少包含 `SKILL.md` 与（如有）`scripts/`。
- **脚本入口放置**：
  - 与 skill 强绑定的脚本放在对应 skill 的 `scripts/` 下
  - 与整个仓库相关的脚本放在仓库根的 `scripts/` 下
- **生成物不入库**：报告类产物（如 `reports/*.docx`）默认忽略；如果需要入库，请放到 `docs/` 并说明来源与生成方式。
- **下载/缓存不入库**：`downloads/`、各类缓存与本地环境目录应保持在 `.gitignore` 中。

