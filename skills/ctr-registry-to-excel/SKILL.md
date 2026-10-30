---
name: ctr-registry-to-excel
description: 把 CTR 临床试验登记平台导出的 Word（.doc）关键信息，按语义对号入座录入到既有的临床试验 Excel 数据库。当用户要求「把 CTR/登记 Word 里的信息录入/更新到 Excel」「补齐/核对登记号」「按登记号倒序整理临床数据库」时使用。覆盖全流程：Word COM 提取 .doc 文本 → 字段解析（药物名去曾用名、试验设计三段拼接、试验药/对照药扒分组、终点序号+评价时间、暂未填写留空）→ 按登记号命中则补全/覆盖、未命中则新增 → 全表格式统一 → 按登记号倒序 → 逐列 diff。内含九个会静默毁掉交付物的坑：PowerShell 的 New-Object -ComObject 被安全策略拦截、按行号删行误删他行、新增行漏写主键导致排序崩溃、补日期落成序列号、None 语义不清该清空却跳过、内容变长沿用旧行高被截断、重排后 auto_filter 未更新、无源文档凭空统一格式造成造假、present_files 预览导致文件被独占锁。用户说「Excel 打不开 / 日期变成一串数字 / 行数不对 / 某行不见了」时必须优先加载本技能。
license: Unknown
metadata:
  version: "1.0.0"
  skill-author: "K-Dense Inc."
---

# CTR Registry → Excel（登记 Word 录入临床数据库）

## 适用场景

- 一批 CTR 登记平台导出的 `XXX详细信息.doc`，要录入/更新到一张**既有的**临床试验汇总 Excel
- 库里已有数据，需要判断「新增 / 补全 / 修正 / 未动」
- 需要按登记号倒序整理、去重、统一全表行文格式

**不适用**：从零新建一张表（用 `workbuddy-sheet-generation`）；
源文档是 .docx（直接用 python-docx，不需要 Word COM）。

## 环境与前置

| 项 | 说明 |
|---|---|
| 读 .doc | **系统 python（3.13，带 pip）+ `pip install pywin32`**，走 `win32com.client.Dispatch("Word.Application")` |
| 读写 xlsx | 项目 `.venv/Scripts/python.exe`（含 openpyxl） |
| 禁止 | PowerShell 工具的 `New-Object -ComObject`（被安全策略拦截） |

先确认：`python -c "import win32com.client"` 与 `.venv/Scripts/python.exe -c "import openpyxl"` 都能通过。

## SOP

### 第 1 步 备份
```bash
TS=$(date +%Y%m%d_%H%M%S)
cp 原库.xlsx 原库_备份_${TS}.xlsx
```

### 第 2 步 提取 .doc 文本
```bash
python skills/ctr-registry-to-excel/scripts/extract_ctr_doc_text.py <doc目录> <文本输出目录>
```
每份文档产出 `<stem>.txt`（正文）和 `<stem>.tables.txt`（表格 TAB 分隔）。

### 第 3 步 解析字段，写 records.json
按 `references/field-mapping.md` 的映射逐字段抽取。JSON 结构：

```json
{
  "CTR20263963": {
    "申请人": "石药集团巨石生物制药有限公司",
    "首次公示": "2026-10-21",
    "首例入组": null,
    "样本量": 496
  }
}
```
- 日期写 `YYYY-MM-DD` 字符串；**源文档标注「登记人暂未填写该信息」一律写 `null`**
- `null` 的含义是「必须清空」，不是「跳过」
- 已有正确数据要复用时，直接 `--dump` 导出为骨架再改：
  ```bash
  .venv/Scripts/python.exe skills/.../sync_ctr_registry_to_excel.py \
      --xlsx 库.xlsx --sheet 表名 --dump CTR20263963,CTR20263799 --dump-out base.json
  ```

### 第 4 步 同步入库（生成新文件，别覆盖原库）
```bash
.venv/Scripts/python.exe skills/ctr-registry-to-excel/scripts/sync_ctr_registry_to_excel.py \
    --xlsx 原库.xlsx --sheet NMPA数据库 \
    --records records.json \
    --out 新库_v2.xlsx --diff output/diff.md
```
脚本做五件事：按登记号去重 → 应用 records（补全/修正/清空/新增）→
全表格式统一 → 按登记号倒序 → 输出逐列 diff（标注 新增/补全/修正/格式统一/未动）。

### 第 5 步 自检
```bash
.venv/Scripts/python.exe skills/ctr-registry-to-excel/scripts/verify_ctr_excel.py 新库_v2.xlsx --sheet 表名
```
七个 PART：zip 完整性 / 主键非空去重 / 倒序 / 日期列类型与占位符 / 计数列类型 /
括号空格归一化 / auto_filter 范围。exit 0 才算过。

### 第 6 步 回归（可选但推荐）
用同一份 records.json 从**改动前的库**再跑一次，逐格比对两次输出应完全一致
（本次实测 0 差异）。不一致说明脚本有副作用，不许交付。

## 脚本索引

| 脚本 | 作用 |
|---|---|
| `scripts/extract_ctr_doc_text.py` | .doc → 文本 + 表格（Word COM） |
| `scripts/sync_ctr_registry_to_excel.py` | records.json → Excel（去重/补全/修正/统一/排序/diff，含 `--dump` 模式） |
| `scripts/verify_ctr_excel.py` | 交付前七项体检 |
| `references/field-mapping.md` | CTR 字段 → 列映射 + 行文风格 + 判定规则 |
| `references/cleanup-rules.md` | 录入前清洗 + 全表格式统一白名单/黑名单 |
| `references/ctr_records_herpes_zoster.json` | 7 条带疱疫苗记录示例（可作 records.json 模板） |

## 九个坑

1. **`.doc` 不读就不能开始**：python-docx 读不了；PowerShell 的 `New-Object -ComObject`
   被安全策略拦截。用系统 python + pywin32 调 Word COM，这是唯一无损路径。
2. **删除/去重绝不能按行号**：重排一次行号就失效，本技能第一版就按「第 33 行」删，
   结果误删了另一家企业的记录。**永远按登记号去重**（保留首现）。
3. **新增行必须自己写主键列**：只填充非主键字段会让 C 列为空，排序时
   `None` 与 `str` 比较直接 TypeError。脚本已加断言，排序前主键必须非空。
4. **补日期到原本空白的格子会显示成序列号**：该格 number_format 是 "General"，
   日期会被显示成 45053。写回时凡 datetime 一律强制 `yyyy-mm-dd`。
5. **`null` 的语义**：源文档写「登记人暂未填写该信息」= 该格必须为空。
   若原格有个错误值（如把未开始的试验写成 2020-04-24），也要清掉，不能跳过。
6. **内容变长的行要把 height 置 None**：沿用旧的固定行高会把单元格截断。
   置 None 后 Excel 会自动行高。
7. **重排后同步 `auto_filter.ref`**，否则筛选范围与数据不符。
8. **无源文档不得凭空统一格式**：`主要人群` 两种写法、`试验设计` 第三段的
   「安慰剂对照」（人工补录信息，Word 的「设计类型」只有「平行分组」）——
   改了就是丢信息或造假。只做 `references/cleanup-rules.md` 白名单里的替换。
9. **不要用 present_files 预览交付的 Office 文件**：预览实例持独占锁，
   用户本地打开会报「文件正在使用 / 被'另一用户'锁定」。验证完就放手。

## 交付前验证清单

- [ ] 已备份原库（文件名带时间戳）
- [ ] 新文件行数 = 旧行数 − 删除 + 新增
- [ ] 登记号：无空、无重复、倒序
- [ ] 日期列全部是日期型，无占位符残留
- [ ] 样本量列全部是整数
- [ ] `verify_ctr_excel.py` exit 0
- [ ] 回归跑一次，与首次输出逐格一致
- [ ] 逐列 diff 已给用户，状态标注齐全
- [ ] 拿不准的项单独列出（如日期列里的业务状态文本、分期措辞）

## 环境备忘（本机）

- 项目 venv 无 pip、无 pywin32；系统 python 有 pip。两个解释器分工如上。
- openpyxl 重排行的正确姿势见 `references/cleanup-rules.md` 第 3 节。
