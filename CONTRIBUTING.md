## 贡献指南

欢迎提交新的 skill、改进现有 skill，或补充仓库级脚本/文档。

## 开发环境

- **Python**：3.10+（CI 当前使用 3.10）

安装依赖：

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

运行测试：

```bash
pytest
```

基础 lint（与 CI 一致）：

```bash
flake8 .
```

## 新增或修改 skill

目录约定：

- 路径：`skills/<skill-name>/`
- 至少包含：`SKILL.md`
- 如包含脚本：放在 `skills/<skill-name>/scripts/` 下，并在 `SKILL.md` 里写清入口、参数与输出

请确保：

- **可复现**：脚本具备清晰的输入/输出约定，避免硬编码本地路径
- **合规**：若涉及患者/受试者数据，必须在文档中强调去标识化与数据治理要求
- **许可证**：在 `SKILL.md` 中明确引用/依赖的许可证信息（尤其是外部数据源或 SDK）

## 仓库级脚本

与单个 skill 无关的脚本放在 `scripts/` 下；生成物默认输出到 `reports/`（该目录的二进制产物默认不入库）。

## 提交规范（建议）

- **小步提交**：一次提交聚焦一类变更（例如“新增一个 skill”或“重构 README”）
- **不要提交生成物**：如 `.docx`、大文件数据、下载缓存等

