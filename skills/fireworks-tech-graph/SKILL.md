---
name: fireworks-tech-graph
description: Generate architecture/flow/UML technical diagrams from natural language and export SVG plus PNG assets.
metadata:
  surfaces:
    - ide
    - terminal
---

# Fireworks Tech Graph

将自然语言描述转成技术图（架构图、流程图、序列图、UML 等），输出 SVG，并可进一步导出 PNG。

## 适用场景

- 需要快速生成系统架构图、数据流图、时序图
- 需要统一风格的技术图素材用于文档、汇报或论文
- 需要根据描述快速迭代图结构而非手工拖拽

## 目录能力（当前项目内）

- 模板：`templates/`
- 参考样式与规范：`references/`
- 自动化脚本：`scripts/`
- 示例输入：`fixtures/`

## 推荐工作流

1. 根据需求选择图类型与风格（参考 `references/style-*.md`）
2. 用自然语言定义：
   - 图类型（architecture/flowchart/sequence/UML）
   - 关键节点与关系
   - 输出路径与命名
3. 生成 SVG 后做一次文本与布局校验
4. 如需位图，使用 `rsvg-convert` 导出 PNG

## 示例 Prompt

```text
画一个 RAG 架构图，风格使用 style 2（dark-terminal），包含：
User、Retriever、Vector DB、Reranker、LLM、Guardrails、Observability。
要求显示主流程与错误回退路径，输出到 ./output/rag-architecture.svg
```

## 输出要求

- 图中层级清晰、命名一致、箭头方向明确
- 优先输出可编辑的 SVG
- 若导出 PNG，给出分辨率参数与输出路径
