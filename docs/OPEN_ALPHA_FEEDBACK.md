# Open Alpha Feedback

提交反馈前，请先确认不包含真实 Email、Handle、Profile URL、Campaign 文本、Token、原始名单或完整 Run。

当前尚未收到真实 Open Alpha 反馈。公开空队列、分级规则和私有接收边界见 [`docs/alpha/`](alpha/)；请不要把原始第三方文件作为公开 Issue 附件。

## 反馈入口

- Bug：[`bug_report.yml`](../.github/ISSUE_TEMPLATE/bug_report.yml)
- Adapter 格式请求：[`adapter_format_request.yml`](../.github/ISSUE_TEMPLATE/adapter_format_request.yml)
- 功能建议：[`feature_request.yml`](../.github/ISSUE_TEMPLATE/feature_request.yml)
- 文档问题：[`documentation_problem.yml`](../.github/ISSUE_TEMPLATE/documentation_problem.yml)
- 安全问题：不要创建公开 Issue，按照 [`SECURITY.md`](../SECURITY.md) 使用 Security tab 私下报告。

## 可选反馈表

可以复制以下内容到 Issue，或在陪跑测试后保存为脱敏文本：

```text
kol-signal 版本：
操作系统 / Python：
使用的来源类型：
原始记录数量：
是否完成 Mapping：
是否理解 Data Audit：
是否认可 Priority / Verify 分类：
输出是否进入实际工作表：
Generic Mapping 最难处理的列：
节省或增加了哪个步骤：
公开错误码：
是否愿意再次使用：
其他反馈：
```

若已有成功创建的 Run，可以先生成：

```bash
kol-signal diagnostics --run RUN_ID --output diagnostics.zip
```

Diagnostics ZIP 只允许用于排查技术问题，不能替代原始数据授权。上传前必须自行打开并检查内容。

维护者将公开反馈转成内部记录前，使用：

```bash
python -m tools.alpha_feedback validate --input feedback_record.json
python -m tools.alpha_feedback add --input feedback_record.json
```

默认只写入 Git 忽略的 `.kol-signal/alpha_feedback_log.json`。流程和字段契约见 [`alpha/ALPHA_FEEDBACK_LOG.md`](alpha/ALPHA_FEEDBACK_LOG.md)。
