# 临床与学术 PPT 防“AI 模板味”视觉规范（Anti-AI-Slop Visual Guide）

借鉴 `Nutlope/hallmark`（Floor / Reflex / Finish 三层门控）与 `pbakaus/impeccable`（确定性反粗糙度审查），为竞品分析、临床进展汇报与 CSR 摘要 PPT 建立可落地的版式克制与高信息密度准则。

---

## 1. 三层门控体系（Three-Tier Gate）

| 门控层级 | 严重度 | 处理策略 | 典型检查项 |
|---|:---:|---|---|
| **Floor（底线阻断）** | **P0** | **严禁交付**，必须修复 | 未替换占位符（`TODO`/`TBD`/`[待补充]`）、正文/表格字号 `< 9 pt`、文本与底色对比度 `< 3.0:1`、表格/结论框重叠溢出、GraphPad Prism 图表被栅格化为 PNG/JPG 丢失 OLE 数据 |
| **Reflex（AI 惯性预警）** | **P1–P2** | 默认禁止；若因业务需要保留须有明确理由 | 单页字体族 `> 3` 种、非表格大段散文堆砌（`> 450` 词/字）、卡片套卡片（`>= 3` 层嵌套填充框）、全片重复大写英文眉标（`eyebrow-cliche`）、高饱和彩虹配色（`> 5` 种） |
| **Finish（工艺打磨）** | **P3** | 建议收口，不阻断交付 | 孤立空装饰矩形框、表格列宽与页边距微调、页脚页码与对齐精修 |

---

## 2. 七大“AI 模板味”反模式与临床级替代方案

1. **禁止紫蓝渐变与霓虹科技风底色**：
   - 临床汇报与竞品分析统一采用**白底 / 浅灰微底（`#FFFFFF` / `#F7F8FA`）+ 1 个主品牌色（如深红 `#C00000` 或深海军蓝 `#1B365D`）+ 1 个语义状态色**，拒绝大面积渐变卡片背景。
2. **禁止每页标题上方强加全大写英文眉标（Eyebrow Tag）**：
   - 如 `CLINICAL PROGRESS` / `COMPETITIVE LANDSCAPE` 小药丸标签；直接用**结论导向的中文主标题 + 一句话核心副标题**承载信息。
3. **禁止“标题单字/半句强行变色”**：
   - 主标题保持单一深色（`#1A1A1A`），避免在一句话中把一两个词标成亮色制造廉价营销感。
4. **禁止“卡片套卡片 + 圆角图标方块”**：
   - 用**结构化对比矩阵表（Table）**或**无边框留白分栏（细分隔线 `0.5pt #D9DCE0`）**替代多层嵌套阴影/填充矩形框，提升同屏有效数据密度。
5. **禁止大段散文墙（Text Wall）**：
   - 叙事文本框精简为“结论句 + 关键指标”；多维度对比（适应症、试验分期、样本量、主要终点、注册路径）一律收口进**整齐表格**。
6. **禁止结论框与膨胀表格碰撞遮挡**：
   - 表格底边与底部结论框（Conclusion Box）之间必须留足实测安全间距，防止字体替换后行高膨胀遮挡结论。
7. **禁止用静态截图替代 GraphPad Prism 原生图表**：
   - 遵循 `AGENTS.md` §9，所有 Prism 图表必须保留 `ppt/embeddings/` OLE 嵌入对象，确保双击可编辑原始数据。

---

## 3. 交付前双引擎确定性质检（Dual-Validator QA）

1. **跨平台样式与 Slop 扫描（无 LLM 依赖）**：
   ```bash
   python scripts/pipeline/validate/pptx_slop_detector.py <deck.pptx>
   ```
   - 加 `--strict` 可同时拦截 Reflex（P1–P2）问题。
2. **Windows PowerPoint COM 实测溢出与底边核验**：
   ```bash
   python scripts/pipeline/validate/pptx_overflow_checker.py <deck.pptx> --max-bottom 6.27
   ```
3. **OLE 包完整性校验（含 Prism 图表时）**：
   ```bash
   python scripts/pipeline/review/compare_pptx_package.py <before.pptx> <after.pptx>
   ```
