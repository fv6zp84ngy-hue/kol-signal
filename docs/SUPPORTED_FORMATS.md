# Supported Input Formats

> 适用版本：`0.5.0a1` Open Alpha
> 核对日期：2026-07-31

## 支持范围

### CSV

- 文件扩展名必须是 `.csv`。
- 编码必须是 UTF-8 或 UTF-8-SIG。
- 第一行必须是 Header。
- Header 不得为空，也不得在忽略大小写和首尾空格后重复。
- 不进行自动编码猜测。

非 UTF-8 CSV 会返回明确错误，不会回退到本地系统编码。

### XLSX

- 文件扩展名必须是 `.xlsx`。
- 必须是未加密、可正常打开的 Office Open XML 工作簿。
- 必须选择一个非空工作表作为数据源。
- 第一行必须是 Header。
- Header 不得为空或重复。

当工作簿只有一个非空工作表时，CLI 自动使用该表；当存在多个非空工作表时，CLI 会停止并列出工作表名称，不会静默使用活动工作表。

使用以下参数显式选择：

```bash
kol-signal mapping-preview \
  --input "creators.xlsx" \
  --sheet "creators.xlsx=Creators" \
  --format json
```

正式运行使用相同选择：

```bash
kol-signal run \
  --input "creators.xlsx" \
  --sheet "creators.xlsx=Creators" \
  --brief "campaign.txt"
```

多份 XLSX 可以重复提供 `--sheet`，每项必须对应一个已经通过 `--input` 指定的文件。

CSV/XLSX 文件可被读取，不代表某个第三方导出格式已经 Verified。Native 与 Generic Import 的证据等级见 [`ADAPTER_COMPATIBILITY.md`](ADAPTER_COMPATIBILITY.md)。

## 明确不支持

- `.xls`。
- 加密或带密码的 `.xlsx`。
- 自动修复损坏工作簿。
- 自动识别任意 CSV 编码。
- 宏、VBA 或杀毒检查。
- 依赖隐藏工作表、公式计算结果或外部链接刷新才能得到的输入。

## 输出工作簿安全

所有 Excel 输出统一经过 `safe_excel_value`：

- 以 `=`、`+`、`-`、`@`、Tab 或回车开头的文本会被写成纯文本。
- 数字和日期类型保持原类型。
- Data Audit、Creator Shortlist、Merge Review、Feedback Template 和 Feedback Report 使用同一写入路径。

该防护针对 Formula Injection，不等同于病毒、宏或恶意文件扫描。
