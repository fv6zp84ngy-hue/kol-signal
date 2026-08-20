# Creator Signal Intelligence — Implementation Status

> 状态版本：v0.1  
> 对应代码版本：`0.5.0a1`
> 发布状态：Open Alpha local release candidate / GitHub publication blocked
> 核对日期：2026-08-17

## 1. 使用方式

本文件记录当前代码事实，用于解释冻结的 PRD/DESIGN/SPEC v0.2 与实际实现之间的差异。

状态定义：

- `Implemented`：已有代码、测试和可运行入口。
- `Partially Implemented`：核心路径可用，但格式、分发或验证范围有限。
- `Not Implemented`：文档中出现，但当前代码没有该能力。
- `Backlog`：明确不属于当前冻结 P0。

公开 README 和 CLI Help 以当前实现为准。冻结文档保留为产品决策记录，不代表每一项已经落地。

## 2. CLI 状态

| 能力 | 状态 | 当前事实 | 后续阶段 |
|---|---|---|---|
| `kol-signal run` | Implemented | 支持重复 `--input`、显式 `--sheet`、Campaign 确认、Mapping、Audit、Shortlist 和 Excel/Markdown 输出 | 保持 |
| `kol-signal campaign-preview` | Implemented | 显示已识别、未识别、冲突、警告和最终结构；可生成确认配置 | A1 完成 |
| `kol-signal mapping-preview` | Implemented | 支持 text/json 预览、显式工作表选择，不导入数据 | 保持 |
| `kol-signal review` | Implemented | 应用 `merge`、`keep_separate`、`unsure` 并重算同一 Run | 保持 |
| `kol-signal feedback` | Implemented | 导入 Feedback Template，输出描述统计和文字反馈摘要 | 保持 |
| `kol-signal demo` | Implemented | 使用 Wheel 包内 Fully Synthetic 数据，输出完整 Run | A3 完成 |
| `--no-model` | Not Implemented | 当前核心完全不依赖模型，因此没有模型开关 | R2 仍须保证无模型运行 |
| `kol-signal --version` | Implemented | 输出包版本 `0.5.0a1` | A5 完成 |
| `kol-signal doctor` | Implemented | 检查 Python、包、OpenPyXL、可写性和可选 Skill；不读取用户名单或输出路径 | A3 完成 |
| `kol-signal diagnostics` | Implemented | 为既有 Run 生成四文件固定白名单 ZIP；不读取原始名单，并过滤 PII、Campaign 文本、Token 与绝对路径 | A4 完成 |

## 3. 输入、Mapping 与 Adapter

| 能力 | 状态 | 当前事实 | 限制 |
|---|---|---|---|
| CSV 输入 | Implemented | 支持 UTF-8/UTF-8-SIG、Dialect Sniffing、空/重复 Header 校验和稳定错误 | 不支持其他编码或自动猜测 |
| XLSX 输入 | Implemented | 单一非空工作表自动使用；多个非空工作表要求 `--sheet` | 不支持 `.xls`、加密或损坏工作簿修复 |
| Generic Mapping | Implemented | 列名、样例值、置信度、歧义确认、配置复用 | 未覆盖全部第三方格式 |
| WaveInflu Native Adapter | Partially Implemented / Not Tested | WaveInflu-like 合成 Fixture 格式可用；CLI 显示验证等级 | 没有实际导出或精确官方 Header 证据 |
| Nox Native Adapter | Partially Implemented / Not Tested | Nox-like 合成 Fixture 格式可用；CLI 显示验证等级 | 没有实际导出或精确官方 Header 证据 |
| EasyKOL/CreatiVault Adapter | Generic Import / vendor format Not Tested | 使用 Generic Mapping | 没有合法格式样本，不承诺专用兼容 |
| Live API | Backlog | 无 API 调用 | 不属于 Public Beta P0 |

## 4. 核心决策链路

| 能力 | 状态 | 当前事实 |
|---|---|---|
| 数值与日期标准化 | Implemented | 支持紧凑数字、百分比、ISO/常见日期和 Invalid 保留 |
| Handle/URL 标准化 | Implemented | Handle 统一、URL 去跟踪参数 |
| 确定性身份去重 | Implemented | 同平台确定性键；强反证阻止自动合并 |
| Review Queue | Implemented | 弱匹配和身份冲突进入人工审核 |
| 数据新鲜度与冲突 | Implemented | 字段 TTL、数值相对差异、分类冲突和 Unknown 时间 |
| Campaign 解析 | Implemented | Parser v1；条件可见、冲突检测、非交互门禁、确认配置和确定性结果 | 仅支持公开表达矩阵 |
| Campaign Blocklist | Implemented | 明确 `@handle` 进入 `EXCLUDED_BLOCKLIST` | 不猜测姓名或跨平台身份 |
| Campaign Topic | Partially Implemented | 五类 Topic 可结构化保存 | 无达人 Topic 证据，明确不参与评分 |
| 四维评分 | Implemented | Brand Fit、Commercial Readiness、Contactability、Data Confidence |
| 模型增强 | Not Implemented | 无模型 Provider、Prompt 或模型事实输入 | 不阻塞核心流程 |

## 5. 输出与反馈

| 能力 | 状态 | 当前事实 |
|---|---|---|
| Data Audit | Implemented | XLSX，包含 Summary、来源、覆盖、冲突、过期和重复候选 |
| Creator Shortlist | Implemented | XLSX，包含行动等级、维度分、理由、来源和警告 |
| Merge Review | Implemented | XLSX，可回填人工决定 |
| Feedback Template | Implemented | XLSX，可回填审核与建联结果 |
| Feedback Report | Implemented | XLSX/Markdown，分母为 0 时返回 null |
| Campaign Config | Implemented | 每个 Run 保存 `campaign.json`，Manifest 与 Report 保留解析证据 | Parser Version 必须匹配 |
| Excel Formula Injection 防护 | Implemented | 所有工作簿复用 `safe_excel_value`，危险前缀写为纯文本 | 不等同于病毒、宏或 VBA 检查 |

## 6. 存储与运行目录

| 项目 | 状态 | 当前事实 |
|---|---|---|
| 默认 Run 目录 | Implemented | `./runs/<run_id>/` |
| Mapping 配置目录 | Implemented | `.kol-signal/mappings/` |
| Manifest | Implemented | 保存输入 Hash、Mapping、Reference Time、版本和审核状态 |
| Demo Run 目录 | Implemented | 默认 `./kol-signal-demo/<run_id>/`，卸载不自动删除 |
| SQLite / `store.db` | Not Implemented | 当前运行不创建 SQLite 数据库 |
| `.kol-signal/runs/` | Not Implemented | 冻结 SPEC 中出现，实际默认使用 `./runs/` |

Public Beta 当前选择 Manifest + Run Artifacts，不为对齐冻结文档而补建 SQLite。

## 7. Exit Code

| Exit Code | 状态 | 当前含义 |
|---:|---|---|
| 0 | Implemented | 成功 |
| 2 | Implemented | 输入、Mapping、Review 或 Feedback 错误 |
| 3 | Not Implemented | 冻结 SPEC 中定义的“部分成功”尚无 CLI 路径 |
| 4 | Not Implemented | 冻结 SPEC 中定义的模型/连接器错误不适用于当前离线核心 |
| 5 | Implemented | 输出写入失败 |

## 8. Codex Skill

| 能力 | 状态 | 当前事实 |
|---|---|---|
| Skill 源码 | Implemented | 位于 `skills/creator-signal-intelligence/` |
| 薄包装边界 | Implemented | Skill 只负责引导、调用和解释，不保存业务规则 |
| 用户级安装 | Documented / Not Performed | 提供 macOS、Linux、Windows 手工安装和不覆盖检查；未自动写入用户目录 |
| Wheel 分发 | Not Implemented | Python wheel 不包含 Skill |
| 自动发现验证 | Not Implemented | 尚未由陌生用户在新 Codex 任务中做安装后验证 |

## 9. 测试与分发

| 能力 | 状态 | 当前事实 |
|---|---|---|
| 开源许可证 | Implemented | MIT；版权主体使用项目贡献者，不公开个人作者 |
| 包作者元数据 | Not Implemented | 维护者明确选择不公开作者，`pyproject.toml` 不填写 `authors` |
| Project URLs | Not Implemented | 当前没有 GitHub Remote，维护者选择暂不填写 |
| Golden Contract | Implemented | 核心决策、Campaign、Adapter 证据/变异、分发和 Open Alpha 运维行为 |
| 自动化测试 | Implemented | 当前 121 项；最近一次本地完整运行全部通过 |
| Wheel 构建 | Implemented | 包含 Fully Synthetic Demo Package Data |
| Release Candidate 构建 | Implemented | 生成 Wheel、Source Archive、Checksums、Release Notes 和 Manifest |
| 干净安装测试 | Implemented | 新虚拟环境在源码目录外安装 Wheel，Doctor、Demo 与卸载后 Run 保留均已验证 |
| GitHub Actions | Configured / Not Yet Executed | PR/`main` 测试矩阵与 Alpha Tag 构建 Workflow 已建立；需推送 GitHub 后验证 |
| 跨平台声明 | Configured / Not Yet Verified | CI 声明 Ubuntu 3.11/3.12、Windows 3.12；目前本地只验证 macOS + Python 3.12 |
| PyPI 发布 | Backlog | Open Alpha 不要求 |

### 9.1 R0 本地验证记录

核对日期：2026-07-30。

- `.venv/bin/python -m unittest discover -s tests -v`：31 项通过。
- `.venv/bin/pip check`：未发现损坏的依赖关系。
- `pip wheel . --no-deps --no-build-isolation`：成功生成版本匹配的 Wheel。
- `kol-signal run` 使用 WaveInflu 与 Nox Fixture 完成冒烟运行，并生成 Audit、Shortlist、Merge Review、Feedback Template 和 Report。
- 文本文件与 Fixture XLSX 已检查 Email；除 `example.com` 虚构地址外未发现其他地址。
- 常见 Token、私钥标记、真实平台 URL 和绝对用户路径扫描未发现残留。
- 构建产物清理后，仓库目录没有 `build/`、`dist/` 或 `*.egg-info/` 临时产物。

以上只证明当前本地环境可运行，不替代干净安装、陌生用户安装或跨平台验证。

### 9.2 R1 本地验证记录

核对日期：2026-07-31。

- 先增加 8 项安全 Golden Tests，再进入实现。
- `.venv/bin/python -m unittest discover -s tests -v`：原有 31 项与新增 8 项，共 39 项通过。
- 四类 P0 输出工作簿均可重新打开，危险测试文本未产生 Formula Cell。
- 损坏 XLSX、非 UTF-8 CSV、空/重复 Header 返回稳定错误且 CLI 不显示 Traceback。
- 多个非空工作表在未选择时停止；`--sheet "INPUT=WORKSHEET"` 是显式确认入口。
- 输出目录创建失败不会修改已经存在的 Run。
- 单行无效数值保留为 Invalid，其他有效记录继续处理。

### 9.3 A1 本地验证记录

核对日期：2026-07-31。

- 先增加 11 项 Campaign Parser Golden Tests，再进入实现。
- 美国、US、United States；英语、English；`10K–500K`、`10,000–500,000`、`1万–50万` 归一结果一致。
- 模糊条件进入未识别列表；关键硬条件在非交互 Run 中阻断。
- 不同或反向粉丝范围进入冲突列表，不能确认或运行。
- 已确认配置绑定 Brief Hash，可作为显式运行输入。
- 每个 Run 保存 `campaign.json`，Manifest 和 Report 显示解析证据。
- Blocklist 是硬过滤；Topic 仅保留，不新增评分维度。
- 原有 39 项与新增 11 项共 50 项测试通过。

### 9.4 A2 本地验证记录

核对日期：2026-07-31。

- 先增加 11 项 Adapter 证据和格式变异 Golden Tests，再进入实现。
- 覆盖列顺序、无关列、可选列、Header 大小写/空格、三类数字、三类缺失值、UTF-8-SIG、单行错误、工作表名称和 Schema Drift。
- Native 签名漂移会降级 Generic Mapping；额外列保留在 Raw Payload。
- 120 条纯合成 Fixture 完成数据分类、结构清单、Ground Truth 和 PII 检查。
- WaveInflu 与 Nox Native Adapter 均明确标记为 Not Tested。
- 原有 50 项与新增 11 项共 61 项测试通过。
- Open Alpha 的“一个 Verified 或两个 Experimental”证据门槛当前仍未满足。

### 9.5 A3 本地验证记录

核对日期：2026-07-31。

- 先增加 7 项 Demo、版本、Doctor 和安装文档 Golden Tests。
- Demo 数据作为 Python Package Data 分发，不依赖源码目录、模型或 API。
- Demo Run 的 Report 与 Manifest 明确标记 `Fully Synthetic Demo` / `fully_synthetic`。
- `doctor` 不输出完整路径，不读取用户文件，也不访问网络。
- README 第一屏收敛为安装、Demo、真实文件、输出位置和限制。
- CLI 与 Skill 提供 macOS、Windows、Linux 的独立安装和安全卸载说明。
- 本地 Release Candidate 构建会拒绝把 Dirty/Tag 不一致状态标记为 Release Ready。
- Wheel 已在新的 Python 3.12 虚拟环境中从源码目录外安装；测试环境复用系统依赖并以 `--no-deps` 安装候选 Wheel。
- 源码目录外的 `--version`、`doctor` 和 Demo 均成功；Demo 将 24 条来源记录归并为 16 位达人并生成 7 个产物。
- 卸载 CLI 后 Demo Run 仍然存在；四类 XLSX 产物均可打开，扫描未发现公式错误。
- Release Candidate 的 Checksums 校验通过；当前工作树尚未提交且与既有 Tag 不一致，因此 Manifest 正确标记 `release_ready=false`。
- 原有 61 项与新增 7 项共 68 项测试通过。
- 陌生用户仅凭 README 完成安装与 Demo 尚待验证。

### 9.6 A4 本地验证记录

核对日期：2026-07-31。

- 先增加 7 项 Diagnostics、CI、Issue Template、错误目录和 README Golden Tests。
- Diagnostics 使用四个固定 JSON 文件白名单，重新构造信息而非复制或字符串替换原 Manifest。
- PII 测试主动注入 Email、Handle、Profile URL、Campaign 私密文本、Token 和绝对路径，生成 ZIP 中均未发现残留。
- Diagnostics 不读取原始 CSV/XLSX；目标已存在时返回 `KS_OUTPUT_001` 且不覆盖。
- CLI 错误输出增加 `KS_PIPELINE_001`、`KS_OUTPUT_001` 和 `KS_DIAGNOSTICS_001` 公共错误族。
- CI Workflow 配置 Ubuntu 3.11/3.12 与 Windows 3.12，执行依赖检查、Golden Tests、完整测试、CLI Help、Wheel、Wheel 重装和 Demo。
- Alpha Tag 构建 Workflow 只读取仓库内容，不使用 Secret，并复用精确 Tag 发布保护。
- Bug、Adapter、Feature、Documentation 模板和 Security 私下报告入口已建立。
- 最终 Wheel 已在新虚拟环境、源码目录外完成 `pip check`、CLI Help、Demo 和 Diagnostics；卸载后 Run 与 Diagnostics ZIP 均保留。
- Diagnostics 冒烟包只包含四个声明文件，输入 Schema 包含 Adapter、完整列名和工作表状态，不包含原始值。
- 原有 68 项与新增 7 项共 75 项测试通过。
- GitHub Actions 尚未实际执行；跨平台通过状态不得在推送前对外宣称。

### 9.7 A5 本地发布候选记录

核对日期：2026-07-31。

- 先增加 8 项版本、发布资产、公开案例和声明边界 Golden Tests。
- 包版本升级为 `0.5.0a1`，预期 Tag 为 `v0.5.0-alpha.1`，公开状态统一为 Open Alpha。
- 完全合成案例包含两份各 140 条记录的名单；测试直接复算得到 214 位达人、46 个重复组、18 个高冲突字段、35 个过期关键字段、20 位 Priority 和 27 位 Verify。
- Release Notes 包含能力、非目标、Adapter 等级、限制、隐私、安装、Demo 和反馈入口。
- Known Limitations、社交发布文案、可选反馈表和机器可读发布门禁已建立。
- 原有 75 项与新增 8 项共 83 项测试。
- 当前没有 GitHub Remote，也没有未参与开发者的外部安装记录；本地候选不得描述成已经公开发布。

### 9.8 A6 反馈运维基线

核对日期：2026-08-01。

- 先增加 9 项反馈日志、PII 拒绝、优先级、Adapter 门槛、公开空队列和文档边界 Golden Tests。
- `tools.alpha_feedback` 可校验并原子追加本地脱敏记录；公开 Schema 拒绝额外字段、Email、Handle、URL、Token 和绝对路径。
- Blocker 必须有明确 Owner；优先级按用户价值、出现频率、阻塞系数和维护成本计算。
- Native Adapter 评估同时要求两份合法脱敏 Schema、Generic Mapping 不足、需求门槛和可接受维护成本。
- Issue Template 增加用户类型、来源类别、记录量、阶段、影响、复现和 Workaround 字段。
- 公开反馈日志、Adapter 请求队列和 Issue Board 保持为空；真实反馈数、真实格式证据和已发布 Alpha Patch 均为 0。
- 原有 83 项与新增 9 项共 92 项测试通过。
- 当前实现的是反馈接收与分级基础设施，不代表 A6 的真实用户迭代目标已经达成。

### 9.9 内测用户反馈 Benchmark 工程基线

核对日期：2026-08-13。

- Benchmark 独立位于 `tools/internal_feedback_benchmark.py` 与 `benchmarks/internal_feedback/`，没有进入 `kol_signal/` 产品 runtime 或正式依赖。
- `prepare` 只读取配置白名单中的 synthetic/redacted approved Fixture，使用固定 reference time，并调用当前 `run_pipeline` 生成 Treatment artifact。
- 当前完整案例为宠物智能硬件美国 Campaign：120 条原始记录、85 位 canonical creator、3 个身份审核项；冻结硬条件 Ground Truth 覆盖 85/85 位 creator，其中 59 位 qualified。
- Baseline 使用 source record ID；Treatment 使用产品 creator ID；Verifier 通过预先冻结的 identity alias map 归一化，重复选择不会重复计分。
- `analyze` 支持严格 pair matching、确定性 Precision@K/Success、五点信心自评、pair-level bootstrap、subgroup summary、失败 trial accounting 和全链路 Hash。
- `publish` 要求至少 50 个有效 pair、至少 90% coverage、100% Ground Truth、完整 artifact integrity 和项目完整测试通过。
- 新增 Benchmark Golden Tests；当前 Benchmark 测试模块 22 项，DeepSeek 执行器测试 7 项，完整测试集 121 项并全部通过。
- P4 开发用 10-persona smoke 已完成：固定 10 个 synthetic persona、1 个 Campaign、20 条 development-only dummy trial 形成 10/10 valid pairs；该结果只验证 pipeline integrity，未作为用户反馈或公开效果数据保存。
- P5.5 正式外部模型运行已完成：固定 100 个 virtual Persona、1 个 Campaign、200 条 `execution_source=external_model` trial 形成 100/100 valid pairs，coverage 100%，`publishable=true` 且 `gate_failures=[]`。
- 正式 run 为 simulated-user artifact-level A/B internal evaluation，不是真人客户研究、Agency 访谈或生产业务效果；报告与 README 已明确这一边界。
- 正式报告路径为 `docs/INTERNAL_TEST_FEEDBACK.md`，机器可读证据位于 `runs/internal_feedback/p5_deepseek_20260813/`；Run 目录仍属于本地产物，不进入公开源码包。

### 9.10 README-only 安装 Smoke Test

核对日期：2026-08-17。

- 在源码目录外创建隔离虚拟环境，安装 `0.5.0a1` Wheel，并按 README 顺序运行 `kol-signal --version`、`kol-signal doctor` 和 `kol-signal demo`。
- Wheel 安装、版本输出、环境检查和 Fully Synthetic Demo 均通过，Demo 产物可以在隔离目录生成。
- 该次验证是本地隔离环境的 external-like smoke test；执行者仍为项目维护者，不能冒充未参与开发者或真人用户验证。真正的独立安装验证仍需由外部人员完成。

## 10. 明确 Backlog

- Gmail 草稿和自动发送。
- 飞书真实连接器。
- Live API。
- 自建平台爬虫。
- 竞品分析。
- 复杂内容分析和个性化开头。
- A/B/C 建联实验。
- 自动调整评分权重。
- SaaS 前端、账号体系和多人协作。
- 自动谈判、报价预测和完整 CRM。

## 11. 当前公开表述

允许：

> KOL List Auditor Open Alpha 可以在本地比较多份达人名单，发现重复、缺失、过期和冲突数据，并生成可解释的联系优先级。该状态不代表已经验证业务效果或所有第三方格式。

不允许：

> 已稳定支持所有 Nox/WaveInflu 导出。

> 已经是可自助安装的 Public Beta。

> 全自动 KOL Agent。
