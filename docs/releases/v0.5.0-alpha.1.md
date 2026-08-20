# KOL List Auditor v0.5.0-alpha.1

> Release channel：Open Alpha  
> Python package version：`0.5.0a1`  
> Product validation：Not yet validated for target-user business outcomes

## 本版能做什么

- 导入一至多份 UTF-8/UTF-8-SIG CSV 或未加密 XLSX。
- 预览并确认 Campaign 条件和字段 Mapping。
- 执行同平台确定性身份去重。
- 检测缺失、Invalid、过期和字段冲突。
- 生成 Brand Fit、Commercial Readiness、Contactability 和 Data Confidence 四维参考分。
- 输出 Priority、Verify、Hold、Excluded 及可追溯理由。
- 生成 Audit、Shortlist、Merge Review、Feedback Template 和 Markdown Report。
- 导入人工 Merge Review 与 Outreach Feedback。
- 运行完全合成 Demo。
- 为已有 Run 生成固定白名单的脱敏 Diagnostics ZIP。

## 明确不能做什么

- 不搜索全网达人，不调用 Live API，不抓取社交平台。
- 不自动发送邮件，不安装 Gmail 或飞书连接器。
- 不进行竞品全量分析、复杂内容抓取、自动谈判或报价预测。
- 不自动调整评分权重，不承诺提高回复率或合作转化。
- 不提供 SaaS 前端、账号体系或完整 CRM。

## Adapter 验证等级

| 来源 | 入口 | 验证等级 |
|---|---|---|
| WaveInflu-like | Native signature + Mapping | Not Tested |
| Nox-like | Native signature + Mapping | Not Tested |
| EasyKOL / CreatiVault / 其他来源 | Generic Mapping | Vendor format Not Tested |

`Not Tested` 表示只有完全合成结构和公开产品能力证据，没有足够的合法真实导出格式。Native 命中不是第三方官方兼容承诺。

## 已知限制

- Open Alpha 不是 Stable、Production Ready 或 Public Beta。
- Campaign Parser 只支持公开列出的确定性表达。
- 模糊内容风格、受众画像或“不要太商业化”等表达不会被强行评分。
- 只自动合并同平台确定性身份。
- CSV 不猜测非 UTF-8 编码；不支持 `.xls`、加密 Excel、宏或 VBA 检查。
- CI 只声明 Ubuntu 3.11/3.12 与 Windows 3.12；以 Release 对应 Workflow 实际结果为准。

完整列表见 [`docs/KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md)。

## 数据隐私

- 核心流程默认在本地运行。
- Demo 和公开案例均为完全合成数据，Email 使用 `example.com`。
- Run 目录可能包含完整联系信息，默认被 Git 忽略。
- Diagnostics 不读取原始名单，只打包固定白名单字段；分享前仍需人工检查。
- 不提供遥测服务器，不默认上传用户名单或 Campaign。

## 安装

从 Release 下载 Wheel 与 `SHA256SUMS`，先校验后安装：

```bash
pipx install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
kol-signal doctor
```

macOS、Windows、Linux 说明见 [`docs/INSTALLATION.md`](../INSTALLATION.md)。

## Demo

```bash
kol-signal demo
```

Demo 不依赖 API、模型、源码目录或真实名单，并在 Report 与 Manifest 中标记 `fully_synthetic`。

280 条完全合成发布案例见 [`examples/open_alpha_case/CASE_STUDY.md`](../../examples/open_alpha_case/CASE_STUDY.md)。该案例只展示工作流和输出，不能推断实际业务收益。

## 提交反馈

- Bug Report：[`bug_report.yml`](../../.github/ISSUE_TEMPLATE/bug_report.yml)
- Adapter Format Request：[`adapter_format_request.yml`](../../.github/ISSUE_TEMPLATE/adapter_format_request.yml)
- Feature Request：[`feature_request.yml`](../../.github/ISSUE_TEMPLATE/feature_request.yml)
- Documentation Problem：[`documentation_problem.yml`](../../.github/ISSUE_TEMPLATE/documentation_problem.yml)
- 可选反馈表：[`docs/OPEN_ALPHA_FEEDBACK.md`](../OPEN_ALPHA_FEEDBACK.md)
- 安全问题：不要创建公开 Issue，按 [`SECURITY.md`](../../SECURITY.md) 使用 Security tab 私下报告。

不要上传原始达人名单、Email、Handle、Profile URL、Campaign 文本、Token 或完整 Run。

