## Third-Party Notices / 第三方声明

本仓库包含对第三方开源项目、数据库与在线服务（API）的调用示例与 skills 文档。你在使用这些资源时，可能需要遵守其各自的许可协议、使用条款（ToS）、速率限制与再分发限制。

> 重要提醒：一般来说，“分发代码/脚本”与“分发从第三方获取的数据/内容”是两件事；后者往往有更严格限制。

## 上游开源项目

- **Claude Scientific Skills**
  - 仓库：`https://github.com/K-Dense-AI/claude-scientific-skills`
  - 许可证：MIT License
  - 版权：Copyright (c) 2025 K-Dense Inc.
  - 本仓库为其裁剪/重组版本（仅保留临床研究相关 skills）

## 典型外部数据源与在线服务（示例，非穷尽）

以下条目用于提醒“可能需要账号/授权/限制再分发”，请以各 skill 的 `SKILL.md` 与官方条款为准：

- **COSMIC**
  - 可能需要账号/许可；对数据下载与再分发通常有明确限制
- **ClinicalTrials.gov**
  - 官方 API 与数据导出存在速率限制与使用说明；注意对批量抓取的限制
- **PubMed / NCBI E-utilities**
  - 需要遵守 NCBI 的使用政策（包含速率限制、API key 使用建议等）
- **OpenAlex**
  - 注意其 API 使用政策与引用/归属要求
- **openFDA**
  - 注意其 API 使用政策、速率限制与字段语义
- **ClinVar**
  - 注意其数据使用与引用要求（通常允许使用，但仍需遵守声明/归属）

## 你在公开仓库时应避免提交的内容

- 任何 **API key / token / 账号密码 / `.env`** 等敏感信息
- 从第三方服务批量下载得到的 **原始数据文件、镜像数据、受限内容**
- 含真实患者/受试者信息或去标识化不足的数据与文档
- 生成物（如 `reports/*.docx`），除非你确认其内容与版权/隐私均可公开

