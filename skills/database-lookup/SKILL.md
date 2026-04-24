---
name: database-lookup
description: 聚合查询临床与科研常用数据库。优先将任务路由到本仓库已有的原子 skills（ClinicalTrials/PubMed/OpenAlex/FDA/ClinVar/ClinPGx/COSMIC），用于避免重复安装并统一入口。
license: MIT
metadata:
    skill-author: Scientific-Skills-for-Clinical_Trial maintainers
---

# Database Lookup (Aggregator)

## Overview

`database-lookup` 是一个聚合路由 skill，不替代现有数据库 skills，而是统一入口并把任务分发到最合适的原子 skill。

目标：
- 减少重复安装与重复提示词维护
- 保持原子 skill 深度能力不变
- 让用户先用一个入口完成多数检索任务

## Routing Rules

优先按下述规则分发：

1. 临床试验注册/招募/状态检索  
   -> `clinicaltrials-database`

2. 生物医学文献（PMID、MeSH、E-utilities）  
   -> `pubmed-database`

3. 文献计量与跨学科文献图谱（作者/机构/引用网络）  
   -> `openalex-database`

4. 监管与安全（openFDA，不良事件、召回、标签、器械）  
   -> `fda-database`

5. 临床变异致病性与证据等级  
   -> `clinvar-database`

6. 药物基因组学与 CPIC 相关建议  
   -> `clinpgx-database`

7. 肿瘤体细胞突变与癌症基因目录  
   -> `cosmic-database`

## When To Use

当用户表达为“帮我查数据库/查证据/查试验/查变异/查监管信息”，但没有明确指定具体数据库时，优先使用本 skill。

## Output Contract

每次响应至少包含：
- 使用了哪些原子 skill（1 个或多个）
- 选择这些 skill 的原因（1-2 句）
- 关键检索参数（疾病、药物、时间范围、状态、地区等）
- 结果摘要（可复核）

## Best Practices

- 先确认检索目标：发现试验、补充证据、监管核查、遗传注释。
- 避免一次性调用过多数据库；先主库后补库。
- 若用户请求已明确具体数据库，直接调用对应原子 skill，不经过聚合层。
- 涉及受试者或患者信息时，仅处理去标识化数据。

## Example Requests -> Routing

### Example 1
请求：`检索 NSCLC 在美国 RECRUITING 的 PD-1/PD-L1 试验，并给出前 20 条摘要。`  
路由：`clinicaltrials-database`  
原因：核心需求是试验注册状态与地区筛选。

### Example 2
请求：`阿司匹林近 5 年不良事件和召回概况。`  
路由：`fda-database`  
原因：核心数据来自 openFDA 监管与安全端点。

### Example 3
请求：`TP53 变异的临床致病性结论，并补充药物基因组学影响。`  
路由：`clinvar-database` + `clinpgx-database`  
原因：先做变异致病性，再做用药相关解释。

## Local References

见 `references/INDEX.md` 的路由映射与示例。
