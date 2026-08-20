# Campaign Parser — Supported Expressions and Limits

> Parser Version：`1`
> 适用阶段：Open Alpha A1
> 核对日期：2026-07-31

## 1. 设计边界

Campaign Parser 只把用户明确写出的筛选条件转换为可见结构，不生成营销策略、不补充受众假设，也不调用模型。

每次解析返回：

```text
CampaignParseResult
├── parsed_campaign
├── recognized_conditions
├── unrecognized_conditions
├── conflicting_conditions
├── warnings
└── parser_version
```

Topic 标签可以被结构化保存，但当前达人输入没有可靠 Topic 证据字段，因此不会进入评分。报告会明确显示“仅保留，未参与规则”。

## 2. 当前可靠支持

### 市场

| 规范值 | 支持表达 |
|---|---|
| `US` | 美国、US、USA、United States |
| `CA` | 加拿大、Canada |
| `BR` | 巴西、Brazil |
| `JP` | 日本、Japan |
| `DE` | 德国、Germany |

多个市场会被理解为允许集合，不自动视为冲突。

### 语言

| 规范值 | 支持表达 |
|---|---|
| `en` | 英语、English |
| `es` | 西班牙语、Spanish |
| `pt` | 葡萄牙语、Portuguese |
| `ja` | 日语、Japanese |
| `de` | 德语、German |

### 平台

- TikTok / Tik Tok。
- Instagram / IG。
- YouTube / YT。

### 粉丝范围

以下表达解析为同一个范围：

```text
10K–500K
10,000–500,000
1万–50万
```

同一 Brief 中出现不同范围，或最小值大于最大值时，解析结果进入 `conflicting_conditions`，不得运行。

### 最近发帖

支持明确的天数限制，例如：

```text
最近 30 天
last 30 days
within 30 days
```

### 联系路径

支持明确的“需要/不需要商务联系路径”以及对应英文表达。相互矛盾时停止运行。

### Blocklist

首版只支持明确的 Handle：

```text
排除达人：@creator_a、@creator_b
Blocklist: @creator_a, @creator_b
```

匹配使用规范化 Handle，并产生 `EXCLUDED_BLOCKLIST`。

### Topic 标签

当前识别：

- 宠物日常 / `pet_lifestyle`。
- 养狗教程 / `dog_tutorial`。
- 宠物科技 / `pet_tech`。
- 智能硬件体验 / `smart_hardware`。
- 产品测评 / `product_review`。

这些标签只进入最终 Campaign 配置和报告，不增加评分维度。

## 3. 未识别条件

模糊表达不会被强行翻译为分数，例如：

```text
内容不要太商业化
最好有小红书感
内容有质感
适合女性用户
```

- 带“不要、必须、排除”等硬约束信号的未识别条件标记为 `blocking`。
- 带“最好、偏好”等软约束信号的未识别条件标记为 `advisory`。
- 非交互 Run 遇到 `blocking` 条件时停止。
- 用户可以通过 `campaign-preview` 明确确认“该条件不会参与本轮规则”，再传入确认配置。

## 4. 使用流程

先预览：

```bash
kol-signal campaign-preview \
  --brief campaign.txt
```

需要接受未识别条件时，显式生成确认配置：

```bash
kol-signal campaign-preview \
  --brief campaign.txt \
  --confirm \
  --output confirmed_campaign.json
```

再运行：

```bash
kol-signal run \
  --input creators.xlsx \
  --brief campaign.txt \
  --campaign-config confirmed_campaign.json
```

确认配置包含原 Brief Hash。Brief 改变后配置失效，必须重新预览。

## 5. 明确不做

- 开放式 Campaign 策略生成。
- 自动推断市场、受众、性别或排除条件。
- 为理解任意文案持续增加隐藏正则。
- 把 Topic 直接当作已有达人证据。
- 新增评分维度。
- 内容抓取。
- 模型或 Skill Prompt 中的第二套解析规则。
