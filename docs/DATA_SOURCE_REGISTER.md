# Data Source Register

> 登记表版本：v1
> 核对日期：2026-07-31
> 机器可读版本：[`../fixtures/data_source_register.json`](../fixtures/data_source_register.json)

## 1. 登记原则

没有登记来源、获取方式、许可、PII 和再分发状态的数据，不进入公开 Fixture、测试或兼容声明。

`verified_at` 表示最后核对该证据的日期，不代表 Adapter 已达到 Verified。Adapter 等级以 `adapter_status` 为准。

## 2. 当前证据

| source_name | source_type | acquisition_method | license | contains_pii | redistributable | verified_at | adapter_status | intended_use |
|---|---|---|---|---:|---:|---|---|---|
| Creator Signal Intelligence synthetic fixture suite | fully_synthetic_fixture | 按产品测试场景本地确定性生成，不复制第三方导出 | MIT repository fixture | false | true | 2026-07-31 | Not Tested | 标准化、去重、冲突、评分、输出与 Schema 变异测试 |
| WaveInflu public Chrome Web Store product metadata | official_public_product_metadata | 查看公开产品页；只确认 Excel 导出及字段类别 | 第三方页面，仅保留 URL 引用 | false | false | 2026-07-31 | Not Tested | 产品能力背景，不证明精确 Header 兼容 |
| NoxInfluencer public Help Center product metadata | official_public_product_metadata | 查看公开官方帮助页；只确认数据类别 | 第三方页面，仅保留 URL 引用 | false | false | 2026-07-31 | Not Tested | 产品能力背景，不证明精确 CSV Schema |
| Generic CSV/XLSX mapping contract | product_test_contract | 仓库自建 Canonical Field 与 Mapping 测试 | MIT repository test contract | false | true | 2026-07-31 | Generic Import | 未知合法表格的 Mapping Preview 与确认流程 |

## 3. 外部证据链接

- WaveInflu 产品页：<https://chromewebstore.google.com/detail/waveinflu-influencer-find/memenfegdnhmjipjnfndoncinlcpfenf>
- NoxInfluencer 官方帮助页：<https://www.noxinfluencer.com/help/knowledgebase/influencer-data-service/>

仓库不复制上述页面、截图或第三方数据，只登记 URL 和本项目对证据范围的判断。

## 4. 合成 Fixture 登记

结构说明见 [`../fixtures/structure_faithful_manifest.json`](../fixtures/structure_faithful_manifest.json)。

当前 Fixture：

- 总计 120 条来源记录。
- 三个来源各 40 条。
- 去重后 Ground Truth 为 85 位达人。
- Handle、URL、Email、Platform ID、Display Name、品牌和内部备注全部为虚构或保留域数据。
- Email 使用 `example.com` 及其子域。
- Profile URL 使用 `*.example.com`。
- Null Rate 和异常分布用于覆盖测试，不代表第三方真实总体分布。

Ground Truth 索引见 [`../fixtures/ground_truth_manifest.json`](../fixtures/ground_truth_manifest.json)。

## 5. 新证据登记模板

```text
source_name
source_type
acquisition_method
license
contains_pii
redistributable
verified_at
adapter_status
intended_use
```

可选字段：

```text
evidence_id
source_url
schema_hash
owner_confirmation
redaction_method
```

无法确认许可或再分发权时，只能保存本地证据摘要和 Schema Hash，不得提交原文件。
