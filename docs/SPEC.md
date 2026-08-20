# Creator Signal Intelligence — Public Beta MVP Spec

> 规范版本：v0.2  
> Schema 版本：1  
> 范围状态：Scope Frozen  
> 产品入口：Codex Skill + `kol-signal` CLI  
> 核心要求：不依赖第三方实时 API，也能完成一次真实名单审计与 Shortlist

## 0. P0 冻结契约

首轮真实用户测试前，P0 MUST 且只能实现以下链路：

```text
上传多份名单
→ 字段映射
→ 标准化
→ 确定性去重
→ 数据审计
→ Campaign 筛选
→ Shortlist
→ Excel 导出
→ 用户反馈回收
```

以下变更 MAY 在冻结期间进入 P0：

- 修复阻断上述链路的 Bug。
- 修复数据丢失、隐私、安全或合规问题。
- 修正导致实现或验收不一致的规范歧义。

其他新增能力 MUST 进入 Backlog，不得阻塞 Public Beta 首版。

## 1. 实现基线

系统 MUST 使用：

- Python 3.11+
- SQLite
- UTF-8
- 带时区 ISO 8601 时间
- 本地 Workspace
- CSV/XLSX 输入与输出

默认工作目录：

```text
.kol-signal/
├── store.db
├── imports/
├── mappings/
└── runs/
```

目录 MUST 默认加入 `.gitignore`。

## 2. 主命令

### 2.1 一键运行

```bash
kol-signal run \
  --input wave.xlsx \
  --input nox.csv \
  --brief campaign.txt
```

行为：

1. 识别文件格式。
2. 推测来源和字段映射。
3. 生成 Mapping Preview。
4. 映射无歧义时继续运行。
5. 有歧义时生成需要确认的字段列表。
6. 导入并标准化数据。
7. 执行身份去重。
8. 生成 Data Audit。
9. 执行 Campaign 筛选。
10. 输出结果文件。

可选参数：

```text
--mapping PATH
--top INTEGER
--no-model
--output PATH
--format text|json
```

### 2.2 人工审核合并

```bash
kol-signal review --run RUN_ID --input merge_review.xlsx
```

重新应用用户的合并决定，并重新生成审计与 Shortlist。

### 2.3 导入反馈

```bash
kol-signal feedback --run RUN_ID --input feedback_template.xlsx
```

输出：

- 推荐接受率。
- 合并准确率。
- 联系方式准确率。
- 建联结果。
- 来源表现。
- 分数段表现。
- 用户反馈摘要。

### 2.4 Demo

```bash
kol-signal demo
```

使用虚构数据完整运行一次，并生成所有结果文件。

## 3. Campaign Brief

普通用户输入自然语言：

```text
我们是一个面向美国养狗用户的宠物科技品牌。
优先寻找英语内容创作者，粉丝量 1 万到 50 万。
内容最好包含宠物日常、教程或产品测评。
需要有可用的商务联系路径。
最近 30 天没有更新的达人暂不考虑。
```

系统将其转换为结构化配置：

```yaml
brand: Example Brand
markets: [US]
languages: [en]
topics: [dog_care, pet_lifestyle, tutorial, product_review]
follower_min: 10000
follower_max: 500000
latest_post_max_age_days: 30
require_contact_path: true
```

转换结果 MUST 在运行前或报告中可查看。

无法确认的条件 MUST 标记为未设置，不得由模型擅自补充。

## 4. 字段映射

支持字段：

```text
source_record_id
platform
platform_creator_id
handle
profile_url
display_name
followers
average_views
engagement_rate
country
language
email
email_role
latest_post_at
latest_sponsored_post_at
```

自动推测依据：

- 列名。
- 样例值。
- 数据类型。
- URL Host。
- Email 格式。
- 日期格式。

每个推测包含：

```text
target_field
source_column
confidence
example_values
```

规则：

- Confidence ≥ 0.90：可默认采用。
- 0.60–0.90：需要用户确认。
- < 0.60：保持未映射。

未知列 MUST 保存在 Raw Payload 中。

## 5. 数据解析

数值 MUST 支持：

```text
128000
128,000
128K
1.2M
3.5%
```

解析规则：

- Followers 和 Views 转为非负整数。
- Engagement Rate 内部保存为 0–1。
- 无法解析时保存原始值并标记 Invalid。
- 不得将无效值静默转换为 0。

日期：

- 保留原始文本。
- 转换为带时区时间。
- 时区未知时使用运行配置时区并产生 Warning。

## 6. 身份解析

### 6.1 自动合并

满足任一条件且不存在反证：

1. 相同 Platform + Platform Creator ID。
2. 相同 Platform + 规范化 Profile URL。
3. 相同 Platform + 规范化 Handle。

### 6.2 强反证

以下情况禁止自动合并：

- Platform Creator ID 不同。
- 相同 Handle 但 Profile URL 明确不同。
- 不同 Creator 共用经纪公司邮箱。
- 只有 Display Name 相同。
- 只有跨平台 Handle 相同。

### 6.3 人工审核

Review 文件包含：

```text
candidate_a
candidate_b
match_reason
conflict_reason
suggested_action
user_decision
user_note
```

用户决定：

```text
merge
keep_separate
unsure
```

首发版本不要求实现复杂拆分历史。若用户更正错误合并，系统可以从原始 Source Records 重新生成该 Run。

## 7. 数据新鲜度

默认 TTL：

| 字段 | TTL |
|---|---:|
| latest_post_at | 7 天 |
| followers | 30 天 |
| average_views | 30 天 |
| email | 90 天 |
| latest_sponsored_post_at | 45 天 |

这些阈值是 Beta 默认值，可通过配置覆盖，不宣称为行业标准。

判断：

```text
reference_time - observed_at > ttl
```

则标记为 Stale。

如果来源没有提供 `observed_at`：

- 使用文件导入时用户填写或文件导出时间。
- 无法确认时标记 `Observed Time Unknown`。
- 不得标记为 Fresh。

## 8. 字段采用值与冲突

每个关键字段的观测结构：

```json
{
  "field": "followers",
  "value": 128000,
  "source": "nox",
  "observed_at": "2026-07-28T00:00:00Z",
  "status": ["fresh"],
  "is_estimated": false
}
```

采用值优先级由字段配置决定。

默认参考：

- Platform ID/Profile URL：官方主页或确定性来源优先。
- Followers/Views：更新时间和来源可靠度共同判断。
- Email：成功送达历史 > 主页公开商务邮箱 > 明确经纪邮箱 > 第三方数据库。
- Country/Language：允许集合值。

数值冲突：

```text
relative_spread = (max - min) / max(max, 1)
```

- ≤ 5%：Low
- 5%–20%：Medium
- > 20%：High

分类字段：

- 两个高置信来源的规范值不同：Conflict。
- 影响身份、联系方式或硬筛选：Review Required。

## 9. Campaign 筛选

### 9.1 硬过滤

支持：

- Platform。
- Market。
- Language。
- Follower Range。
- Latest Post Age。
- Require Contact Path。
- User Blocklist。

输出明确排除原因：

```text
EXCLUDED_PLATFORM
EXCLUDED_MARKET
EXCLUDED_LANGUAGE
EXCLUDED_FOLLOWER_RANGE
EXCLUDED_INACTIVE
EXCLUDED_NO_CONTACT
EXCLUDED_BLOCKLIST
```

### 9.2 四维评分

每个维度 0–100。

#### Brand Fit：35%

- Market/Language：30%
- Topic Match：35%
- Product Scenario：20%
- Format Match：15%

P0 的 Topic Match、Product Scenario 和 Format Match MUST 只使用导入文件中已有字段、已确认字段映射和 Campaign Brief。系统 MUST NOT 为计算这些 Feature 抓取或分析达人近期内容；输入证据不足时按 unavailable 处理。

#### Commercial Readiness：25%

- Recent Activity：30%
- Business Contact Signal：30%
- Sponsored Signal：25%
- Ad Saturation Warning：15%

Sponsored Signal 和 Ad Saturation Warning MUST 只使用导入来源明确提供的数据，不得在 P0 中新增内容分析调用。

#### Contactability：25%

- Email Source Quality：45%
- Contact Role Clarity：20%
- Email Freshness：20%
- Delivery History：15%

无历史时，Delivery History 标记 unavailable，不计为 0。

#### Data Confidence：15%

- Critical Field Coverage：30%
- Freshness：30%
- Consistency：25%
- Source Diversity：15%

总分：

```text
0.35 × Brand Fit
+ 0.25 × Commercial Readiness
+ 0.25 × Contactability
+ 0.15 × Data Confidence
```

Public Beta 的默认权重只是初始假设，报告 MUST 明确说明尚未经过大样本验证。

### 9.3 行动等级

- Priority：满足硬条件，参考分 ≥ 75，且无高风险冲突。
- Verify：参考分 ≥ 60，但有关键缺失或冲突。
- Hold：参考分 < 60，或适配证据较弱。
- Excluded：未通过硬过滤。

用户可以覆盖系统建议。

## 10. 模型增强

模型 MAY 用于：

- Campaign Brief 结构化。
- 字段映射建议。

模型 MUST NOT：

- 决定身份自动合并。
- 无来源判断已合作或排他。
- 猜测邮箱。
- 推断敏感属性。
- 直接返回最终总分。
- 在 Public Beta P0 中执行复杂内容分析。
- 生成合作角度或个性化邮件开头。
- 在没有内容输入时虚构近期视频细节。

关闭模型后，导入、去重、审计和结构化评分 MUST 正常运行。

## 11. 输出文件

### data_audit.xlsx

工作表：

- Summary
- Source Comparison
- Field Coverage
- Conflicts
- Stale Data
- Duplicate Candidates

### creator_shortlist.xlsx

字段至少包括：

```text
creator_id
action_level
reference_score
platform
handle
profile_url
brand_fit
commercial_readiness
contactability
data_confidence
why_contact
selected_email
email_source
data_warnings
refresh_recommendation
user_accepted
user_note
```

### merge_review.xlsx

用于人工确认疑似重复。

### feedback_template.xlsx

字段：

```text
creator_id
merge_correct
shortlist_accepted
contact_correct
actually_contacted
delivered
bounced
replied
positive_reply
feedback_note
```

### report.md

包含：

- Campaign 摘要。
- 数据源质量。
- 去重结果。
- Top 候选概览。
- 主要数据风险。
- 使用限制。
- 建议下一步。

## 12. Feedback Report

指标：

```text
自动合并准确率
= merge_correct / reviewed_merges

推荐接受率
= shortlist_accepted / reviewed_shortlist

联系方式准确率
= contact_correct / reviewed_contacts

有效邮箱率
= delivered / actually_contacted

回复率
= replied / delivered

正向回复率
= positive_reply / delivered
```

分母为 0 时输出 `null`，不得输出 0%。

样本不足时只展示描述统计，不给出“某规则一定更好”的结论。

## 13. 数据模型

### import_batches

```text
id
source
input_name
content_hash
retrieved_at
imported_at
mapping_json
```

### source_records

```text
id
batch_id
row_locator
raw_payload_json
parse_status
```

### creators

```text
id
platform
platform_creator_id
handle
profile_url
display_name
```

### observations

```text
id
creator_id
source_record_id
field_name
value_json
raw_value_json
source
observed_at
status_json
is_estimated
```

### runs

```text
id
campaign_json
input_hashes_json
rule_version
model_version
status
output_path
created_at
```

### decisions

```text
run_id
creator_id
action_level
reference_score
dimension_scores_json
reasons_json
warnings_json
selected_contact_json
```

### feedback

```text
run_id
creator_id
feedback_type
value_json
note
imported_at
```

## 14. 错误处理

- 单行解析失败不得中断整个文件。
- 无法识别来源时允许使用 Generic Mapping。
- 关键身份字段全部缺失时记录进入 Invalid。
- 存在疑似错误合并时输出 Review Queue。
- 模型失败时降级为规则结果。
- 输出文件生成失败时保留数据库与中间结果。
- 系统不得静默覆盖已有 Run。

Exit Code：

- 0：成功
- 2：输入或配置错误
- 3：部分成功，存在需审核记录
- 4：可选模型不可用
- 5：输出写入失败

## 15. 测试集

必须覆盖：

1. 三个来源中的同一达人被正确合并。
2. 共享经纪邮箱的两位达人不合并。
3. Handle 相同、Platform ID 不同，进入审核。
4. `128K` 和 `1.2M` 正确解析。
5. Invalid 数值不变成 0。
6. 过期时间边界正确。
7. 粉丝数差异超过 20% 标记 High Conflict。
8. `observed_at` 无法确认时不得标记为 Fresh。
9. 缺失 Feature 不直接计 0。
10. 相同输入重复运行结果一致。
11. 一个错误行不阻断其他记录。
12. 模型关闭后仍能生成 Audit 和 Shortlist。
13. 所有 Priority 候选至少有两条明确理由。
14. 分母为 0 时反馈指标为 null。
15. 示例和测试中不包含真实个人数据。

## 16. Definition of Done

Public Beta 首发必须满足：

- 支持通用 CSV/XLSX 和两个真实来源格式。
- 使用 100 条以上虚构或脱敏记录完成端到端运行。
- 能输出 Audit、Shortlist、Merge Review、Feedback Template 和 Report。
- 自动合并固定测试集准确。
- 普通用户无需编写 YAML。
- 每个推荐可以追溯到来源数据。
- 模型和外部 API 均为可选。
- 任何路径均不会自动发送邮件。
- README 包含安装、Demo、数据隐私和已知限制。
- 至少完成三位真实用户的陪跑测试后，才对外称为 Public Beta。

## 17. 实施顺序

1. Workspace、数据库和 Run。
2. Generic CSV/XLSX。
3. 两个 Native Adapter。
4. Mapping Preview。
5. 标准化与确定性去重。
6. Data Audit。
7. Campaign Brief 与硬过滤。
8. 四维评分和行动等级。
9. Excel/Markdown 输出。
10. Review 与 Feedback Import。
11. Codex Skill 引导。
12. 陪跑测试与格式修复。

上述 12 项完成前，不得并行建设 Backlog 功能。

## 18. Backlog

以下能力不属于 Public Beta P0：

- Gmail 草稿。
- 飞书真实连接器。
- Live API。
- 竞品分析。
- 自动发邮件。
- 复杂内容分析。
- A/B/C 实验。
- 自动调整评分权重。
- SaaS 前端。

这些能力 MUST NOT 阻塞 Public Beta 发布。只有完成首轮真实用户测试后，才可基于用户证据重新评审并进入后续版本。
