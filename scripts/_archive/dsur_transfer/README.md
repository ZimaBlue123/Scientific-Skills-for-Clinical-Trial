# 归档说明：dsur_transfer 历史版本

本目录归档了 DSUR 内容迁移工具的历史迭代版本（`dsur_transfer.py` 及 `dsur_transfer_v2.py ~ dsur_transfer_v6.py`）。

## 保留原因

- 完整留存迭代演进轨迹，便于追溯算法假设变化（TOC 处理、字段修复、表格合并等）。
- 仅维护最新版 `scripts/dsur_transfer_v7.py`，提供生产级鲁棒性补强（异常捕获、类型提示、logging）。

## 最新版本

- **生产版本**：[`scripts/dsur_transfer_v7.py`](../../dsur_transfer_v7.py)
- **调用方式**：`python scripts/dsur_transfer_v7.py <template.docx> <source.docx> <output.docx>`
- **退出码**：
  - `0`：成功
  - `1`：运行时错误（文件读取失败、表格索引越界、写入失败）
  - `2`：参数错误（路径缺失或文件不存在）

## 维护策略

- 历史版本不再更新或修复。
- 如需复现历史行为，请使用 git tag 切换至对应提交，或直接运行对应 Python 脚本（其逻辑可能依赖未补强的 API 调用约定）。
