---
name: clinical-document-translation
description: Translate Excel, CSV, Word and PDF documents between Chinese and English with a free-engine-first fallback chain. Use when the user asks for "文档翻译 / Excel 翻译 / Word 翻译 / PDF 翻译 / 中英互译 / 批量翻译 文件 / en2zh / zh2en".
---

# 多格式文档双向翻译

## 适用场景
- 翻译 Excel / CSV / Word / PDF，默认**免费引擎优先**并支持多级兜底
- 方向：`en2zh`（英译中）或 `zh2en`（中译英）

## 脚本位置
`scripts/clinical-automation/24_File_Translator/file_translator.py`

## 用法
```bash
cd scripts/clinical-automation/24_File_Translator
python file_translator.py --self-test        # 先自检引擎可用性
python file_translator.py                    # 交互式
```

常用参数

| 参数 | 说明 |
|---|---|
| `--direction en2zh\|zh2en` | 翻译方向 |
| `--provider` / `--engine` | 指定翻译服务商与引擎 |
| `--columns` | 只翻译指定列（Excel / CSV） |
| `--pdf-mode` | PDF 处理方式 |
| `--cache-file` | 翻译缓存，避免重复消耗额度 |
| `--max-workers` | 并发数 |

## 输入 / 输出约定
- 输入：`24_File_Translator/input/`（不入库）
- 输出：`*_en2zh.*` / `*_zh2en.*` 写入 `output/`

## 配置
复制 `.env.example` 为 `.env` 后按需填写 API 配置。

> ⚠️ `.env` 已在 `scripts/clinical-automation/.gitignore` 中排除，**绝不要提交**。

## 注意事项
- **医学术语不可全信机器翻译**。涉及适应症、不良事件名称、剂量单位、
  法规术语时，必须人工核对；建议配合项目内的术语表使用
- 受试者相关数据属于敏感信息，翻译前确认是否允许经由第三方翻译服务
- 大文件先小批量试跑，确认术语与格式都没问题再全量
