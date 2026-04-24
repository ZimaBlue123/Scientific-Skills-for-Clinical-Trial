---
name: paper-lookup
description: 文献检索聚合入口。将检索任务按目标分发到本仓库已有文献相关 skills（PubMed/OpenAlex），并在需要时补充试验注册信息。
license: MIT
metadata:
    skill-author: Scientific-Skills-for-Clinical_Trial maintainers
---

# Paper Lookup (Aggregator)

## Overview

`paper-lookup` 用于统一处理“找论文/找综述/找最新证据/找引用趋势”等请求。  
它优先复用本仓库已有能力，避免重复安装同类文献 skill。

## Routing Rules

1. 生物医学精准检索（MeSH、字段限定、PMID）  
   -> `pubmed-database`

2. 引用趋势、机构/作者分析、跨学科扩展  
   -> `openalex-database`

3. 若用户同时需要“在研试验”背景  
   -> 追加 `clinicaltrials-database`

## Query Workflow

1. 先把需求结构化：主题、研究类型、时间窗、人群/疾病。
2. 用 `pubmed-database` 获得核心医学证据。
3. 用 `openalex-database` 做补充和引用趋势分析。
4. 需要转化到临床执行时，再补 `clinicaltrials-database`。

## Output Contract

每次输出包含：
- 检索数据库/skills 清单
- 关键检索式（或参数）
- Top 结果摘要（题名、年份、来源）
- 可复现检索建议（下轮如何扩展或收敛）

## Best Practices

- 系统综述场景优先给出 PICO/MeSH 结构化检索式。
- 最新进展查询必须注明时间窗口（如 2023-2026）。
- 结果数量过大时先分层：高证据级别 > 高被引 > 最新发表。

## Example Requests -> Routing

### Example 1
请求：`围绕 CAR-T 在自身免疫病中的证据做 2021-2026 文献综述。`  
路由：`pubmed-database` + `openalex-database`  
原因：PubMed 提供医学核心证据，OpenAlex 补充引用趋势。

### Example 2
请求：`给我 DOI=10.xxxx/xxxx 的论文元数据和开放获取情况。`  
路由：`openalex-database`（必要时补 `pubmed-database`）  
原因：先拿跨库元数据，再按需补医学语境。

### Example 3
请求：`找 RSV 疫苗最新临床证据，并补在研试验。`  
路由：`pubmed-database` + `clinicaltrials-database`  
原因：文献证据与试验注册需要联合回答。

## Local References

见 `references/INDEX.md`。
