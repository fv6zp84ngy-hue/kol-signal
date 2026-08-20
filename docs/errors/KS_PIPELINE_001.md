# KS_PIPELINE_001

## 错误原因

核心流程无法安全继续。常见原因包括输入格式不支持、Header 无效、工作表未确认、Mapping 存在歧义、Campaign 条件未确认，或 Review/Feedback 文件不符合要求。终端中错误码后的文本会说明本次具体原因。

## 数据风险

该错误通常在生成或重写结果前停止。它不表示原始输入已丢失；系统不会静默修改原始 CSV/XLSX。若错误发生在 Review 或 Feedback，请先保留当前 Run。

## 下一步

1. 按错误文本修正输入、`--sheet`、Mapping 或 Campaign 确认。
2. 运行 `kol-signal doctor` 检查本地环境。
3. 如果已有 Run，生成脱敏诊断包：

```bash
kol-signal diagnostics --run RUN_ID --output diagnostics.zip
```

## 脱敏信息

可提交产品版本、Python 版本、操作系统、公开错误码、输入列名、工作表名称、Adapter 判断和脱敏诊断包。不要提交单元格原值、Email、Handle、Profile URL、Campaign 文本、Token 或绝对路径。

