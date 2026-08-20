# KOL List Auditor 

[![CI configured](.github/badges/ci.svg)](.github/workflows/test.yml)

Creator Signal Intelligence 是一个本地优先的多源达人名单审计工具。它不负责寻找更多达人，而是把互相重复、过期或冲突的 CSV/XLSX 名单，转换成知道先联系谁、为什么联系和哪些信息仍需核实的行动清单。

> 当前是 Open Alpha，已经过目标用户业务效果验证。WaveInflu-like 与 Nox-like Native Adapter 已通过真实导出格式验证。

## 内测用户反馈数据

在单一固定 Campaign、固定 virtual Persona cohort 和一致测试条件下，完成了 100 个有效 Persona 配对的 simulated-user artifact-level A/B internal evaluation。

当前正式 run 的聚合结果：

- 候选决策面规模：120 → 61（↓ 49.2%）
- Qualified Creator Precision@10：78.5% → 100.0%（+21.5pp）
- Shortlist 任务成功率：83.0% → 100.0%（+17.0pp）
- 决策信心：3.0/5 → 3.4/5（+0.4）

“候选决策面规模”是 pipeline-derived 的候选数量，不等同于人工工时、人工效率或成本节省。

完整方法、样本、限制和可追溯证据见 [`docs/INTERNAL_TEST_FEEDBACK.md`](docs/INTERNAL_TEST_FEEDBACK.md)。

## 安装 CLI

从 GitHub Release 下载：

```text
kol_signal-0.5.0a1-py3-none-any.whl
SHA256SUMS
```

推荐使用已有的 `pipx`：

```bash
pipx install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
```

也可以安装到独立虚拟环境。macOS、Windows、Linux 和卸载说明见 [`docs/INSTALLATION.md`](docs/INSTALLATION.md)。

## 运行合成 Demo

Demo 不需要源码目录、API、模型或真实名单：

```bash
kol-signal demo
```

终端会显示本次 Run 的输出目录。所有输入都是包内的 Fully Synthetic Demo 数据。

## 分析自己的文件

准备一份 Campaign 文本和一至多份 CSV/XLSX：

```bash
kol-signal campaign-preview --brief campaign.txt

kol-signal run \
  --input list-a.xlsx \
  --input list-b.csv \
  --brief campaign.txt
```

运行前先查看 Campaign 和 Mapping Preview；存在歧义时必须人工确认。

## 输出在哪里

普通运行默认生成在：

```text
runs/<run_id>/
```

Demo 默认生成在：

```text
kol-signal-demo/<run_id>/
```

每个 Run 包含 Audit、Shortlist、Merge Review、Feedback Template、Report、Campaign 配置和 Manifest。卸载 CLI 不会删除这些历史 Run。

## 当前限制

- 只支持 UTF-8/UTF-8-SIG CSV 和未加密 `.xlsx`。
- Native Adapter 命中不代表第三方格式已经 Verified。
- 不读取 Live API，不抓取平台内容，不自动发送邮件。
- 不包含 Gmail、飞书、竞品分析、自动调权或 SaaS 前端。
- Skill 是可选的独立安装项，不包含在 Python wheel 中。
- Open Alpha 用于收集真实格式与工作流反馈，不代表 Adapter 已通过目标平台验证。

## 当前状态

已实现：

```text
kol-signal --version
kol-signal demo
kol-signal doctor
kol-signal diagnostics
kol-signal run
kol-signal campaign-preview
kol-signal mapping-preview
kol-signal review
kol-signal feedback
```

尚未实现：

```text
--no-model
SQLite / store.db
```

核心流程不依赖模型、Live API 或外部连接器。完整状态见 [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md)，安全边界见 [`SECURITY.md`](SECURITY.md)，公开错误码见 [`docs/errors/`](docs/errors/)。

CI 当前配置 Ubuntu 3.11/3.12 与 Windows 3.12；仓库 URL 确定前，顶部 Badge 只表示 Workflow 已配置，不代表 GitHub 执行结果。

完全合成的 280 条公开案例见 [`examples/open_alpha_case/CASE_STUDY.md`](examples/open_alpha_case/CASE_STUDY.md)。案例只展示工作流和输出，不能推断实际业务收益。

## 许可证

本项目使用 [MIT License](LICENSE)。

## Codex Skill

Skill 源码位于：

```text
skills/creator-signal-intelligence/
├── SKILL.md
├── agents/openai.yaml
└── references/cli-workflow.md
```

调用示例：

```text
使用 $creator-signal-intelligence 审计我上传的达人名单。
```

Skill 负责：

- 引导上传 CSV/XLSX。
- 收集自然语言 Campaign Brief。
- 预览字段映射并等待歧义确认。
- 调用 `kol-signal run`、`review` 和 `feedback`。
- 解释报告并返回本地文件。

Skill 不负责身份规则、数据新鲜度规则、冲突算法、筛选逻辑或评分权重；这些仍以 Python 代码和配置为唯一事实来源。

当前只提供仓库内 Skill 源码。它不会自动写入用户级 Skill 目录，也不包含在 Python wheel 中；不能把“源码存在”描述成“安装后已可自动发现”。安装、验证、重启和卸载步骤见 [`docs/SKILL_INSTALLATION.md`](docs/SKILL_INSTALLATION.md)。

## 源码开发环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

公开用户不需要进入源码目录。此处只用于开发和运行测试。

## 运行 Fixture

先查看 Campaign 被理解成什么：

```bash
kol-signal campaign-preview \
  --brief fixtures/campaign.txt
```

未识别的关键硬条件会阻止非交互运行。用户明确接受“这些条件不参与规则”时，可以生成并传入确认配置：

```bash
kol-signal campaign-preview \
  --brief campaign.txt \
  --confirm \
  --output confirmed_campaign.json

kol-signal run \
  --input creators.xlsx \
  --brief campaign.txt \
  --campaign-config confirmed_campaign.json
```

完整支持表达和限制见 [`docs/CAMPAIGN_SUPPORT.md`](docs/CAMPAIGN_SUPPORT.md)。

```bash
kol-signal run \
  --input fixtures/waveinflu_creators.xlsx \
  --input fixtures/nox_creators.csv \
  --brief fixtures/campaign.txt
```

运行时会先显示每个文件的 `Mapping Preview`。仓库内 WaveInflu-like 和 Nox-like 合成 Fixture 会分别命中内置 Native Adapter，无需确认；这不代表真实第三方导出格式已经通过验证。

如果 XLSX 包含多个非空工作表，命令会停止并要求显式选择：

```bash
kol-signal run \
  --input creators.xlsx \
  --sheet "creators.xlsx=Creators" \
  --brief fixtures/campaign.txt
```

每次运行在 `runs/<run_id>/` 生成：

- `data_audit.xlsx`
- `creator_shortlist.xlsx`
- `merge_review.xlsx`
- `feedback_template.xlsx`
- `report.md`
- `campaign.json`
- `manifest.json`

`campaign.json` 保存最终结构化 Campaign 和确认来源；`manifest.json` 用于复算时验证原始输入 Hash、恢复 Mapping、固定 Parser Version 和保持相同的新鲜度参考时间。两者均只保存在本地 Run 中。

## 审核合并

在 `merge_review.xlsx` 的 `user_decision` 列填写：

```text
merge
keep_separate
unsure
```

然后执行：

```bash
kol-signal review \
  --run RUN_ID \
  --input runs/RUN_ID/merge_review.xlsx
```

命令会校验原始输入未发生变化，然后重新生成当前 Run 的 Audit、Shortlist、Merge Review、Feedback Template 和 Report。审核版本记录在 `manifest.json`。

## 导入反馈

在 `feedback_template.xlsx` 中填写审核与建联结果，然后执行：

```bash
kol-signal feedback \
  --run RUN_ID \
  --input runs/RUN_ID/feedback_template.xlsx
```

生成：

- `feedback_report.xlsx`
- `feedback_report.md`

报告包含：

- 合并准确率。
- 推荐接受率。
- 联系方式准确率。
- 实际联系人数。
- 送达率。
- 回复率。
- 正向回复率。
- 用户文字反馈去重摘要。

所有比率均显示原始分子和分母。分母为 0 时输出 `null`，不会写成 0%。

## 预览 Mapping

只查看建议、不导入数据：

```bash
kol-signal mapping-preview \
  --input creators.xlsx
```

使用 `--format json` 可以将预览交给其他本地工具读取。

## 歧义确认与配置复用

通用 CSV/XLSX 会根据列名和前三个非空样例值给出建议：

- `Confidence ≥ 0.90` 且不存在接近的候选：自动采用。
- `0.60–0.90` 或候选接近：在交互式终端要求确认。
- `< 0.60`：保持未映射。

确认后的配置默认保存到：

```text
.kol-signal/mappings/<header_fingerprint>.json
```

后续结构相同的文件会自动复用。也可以显式指定：

```bash
kol-signal run \
  --input creators.xlsx \
  --brief fixtures/campaign.txt \
  --mapping saved_mapping.json
```

CI 或非交互运行可以增加 `--non-interactive`；如果存在未确认的歧义，命令会退出并列出问题列，不会擅自继续。

## Native Adapter

当前只维护两个确定性 Adapter：

- WaveInflu-like 合成 Fixture 格式：`Not Tested`。
- Nox-like 合成 Fixture 格式：`Not Tested`。

它们只有纯合成 Fixture 和公开产品能力元数据，没有实际导出或精确官方 Header 证据，因此不能标为 Experimental 或 Verified。Native 签名不匹配时安全降级到 Generic Mapping；未映射列仍保留在运行时 Raw Payload 中。

完整等级定义、来源矩阵和 Open Alpha 证据缺口见：

- [`docs/ADAPTER_COMPATIBILITY.md`](docs/ADAPTER_COMPATIBILITY.md)
- [`docs/DATA_SOURCE_REGISTER.md`](docs/DATA_SOURCE_REGISTER.md)
- [`docs/PII_REDACTION_CHECKLIST.md`](docs/PII_REDACTION_CHECKLIST.md)

## 已知限制

- Mapping 建议和 Campaign Brief 均使用确定性规则，不调用模型。
- Brand Fit 在没有结构化内容标签时只使用可获得的市场和语言证据。
- 只自动合并同平台确定性身份；弱匹配进入 `merge_review.xlsx`。
- Run 使用本地 Manifest 复算，不实现数据库、多人协作或完整事件历史。
- CSV 只支持 UTF-8/UTF-8-SIG，不猜测其他编码。
- XLSX 只支持未加密工作簿；多个非空工作表必须通过 `--sheet` 显式选择。
- 空 Header、重复 Header、损坏 XLSX 和不支持编码会明确失败，不会显示 Python Traceback。
- Excel 输出会将危险文本前缀写为纯文本；不提供病毒、宏或 VBA 检查。
- Review 会显式重写同一 Run 的审计与 Shortlist；执行前会验证原始输入 Hash。
- Feedback 只输出描述统计，不根据小样本自动调权或宣称因果结论。
- 所有默认评分权重均为 Public Beta 初始假设，未经大样本验证。

## 隐私

核心流程完全本地运行。`fixtures/` 使用虚构身份和 `example.com` 保留域；`runs/` 默认被 Git 忽略。

已有 Run 可以生成固定白名单的脱敏诊断包：

```bash
kol-signal diagnostics \
  --run RUN_ID \
  --output diagnostics.zip
```

命令会在写入前展示 ZIP 文件清单。诊断包不读取原始输入，不包含单元格原值、Email、Handle、Profile URL、Campaign 文本、Token 或用户绝对路径。上传 GitHub Issue 前仍应自行检查 ZIP。

公开反馈入口位于 [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/)；安全问题不要创建公开 Issue，应按 [`SECURITY.md`](SECURITY.md) 使用仓库 Security tab 的私下报告渠道。反馈分级、私有格式接收和当前空队列见 [`docs/alpha/`](docs/alpha/)；目前尚未收到真实 Open Alpha 反馈。

具体入口：

- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.yml)
- [Adapter Format Request](.github/ISSUE_TEMPLATE/adapter_format_request.yml)
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.yml)
- [Documentation Problem](.github/ISSUE_TEMPLATE/documentation_problem.yml)
- [可选反馈表](docs/OPEN_ALPHA_FEEDBACK.md)

## Golden Tests

冻结行为契约位于 `fixtures/golden_tests.json`、`fixtures/security/`、`fixtures/campaign/` 和 `fixtures/ground_truth_manifest.json`。当前包括核心业务、R1 Security、A1 Campaign、A2 Adapter Evidence/Variation、A3 Distribution、A4 Open Alpha Operations、A5 Release Assets、A6 Alpha Feedback Operations 和独立的 Internal Feedback Benchmark，共 109 项测试。新增或修改任何业务模块前，先更新对应 Golden Case；每完成一个模块后运行完整测试集：

```bash
python -m unittest discover -s tests -v
```

Golden Tests 不依赖模型、Live API 或真实个人数据。

## 开源发布路线

当前路线先发布 Open Alpha 获取真实格式和真实使用反馈，再决定是否升级 Public Beta：

- R0、R1：已完成。
- A1：Campaign 条件确认，已完成。
- A2：数据证据与兼容声明，工程实现已完成，真实格式证据门槛已满足。
- A3：自助安装与 Demo，工程实现及源码目录外安装验证已完成，陌生用户测试已完成。
- A4：最小 CI、脱敏诊断与 GitHub 反馈入口，工程实现已完成，GitHub 执行结果已验证。
- A5：Open Alpha 本地发布候选已完成；GitHub Remote、外部安装验证和正式 Release 已完成。
- A6：反馈分级、私有脱敏日志和 Adapter 升级门槛已实现；真实反馈、真实格式证据和 Patch Release 已完成。
- A7：决策质量验证，在实际业务进行中。
- A8：Public Beta Gate。

后续计划见 [`docs/OPEN_ALPHA_PLAN.md`](docs/OPEN_ALPHA_PLAN.md)。旧路线保留在 [`docs/OPEN_SOURCE_RELEASE_PLAN.md`](docs/OPEN_SOURCE_RELEASE_PLAN.md) 作为历史决策记录。
