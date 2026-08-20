# Adapter Compatibility

> 兼容矩阵版本：v1
> 核对日期：2026-07-31
> 适用版本：`0.5.0a1`

## 1. 如何理解状态

| 等级 | 证据要求 | 可以公开表达 |
|---|---|---|
| Verified | 至少两份合法、真实或脱敏的实际导出结构，并通过 Schema Drift 和端到端测试 | 已验证指定格式版本 |
| Experimental | 一份合法实际导出、官方样例或精确官方字段结构 | 实验性支持，可能需要确认 Mapping |
| Generic Import | 没有专用 Adapter，通过字段映射导入 | 可尝试导入，必须检查 Mapping Preview |
| Not Tested | 没有实际导出或精确官方 Schema 证据 | 尚未验证真实格式 |

命中 Native Adapter 只表示当前 Header 符合仓库中的确定性签名，不等于该第三方来源已经 Verified。

## 2. 当前 Compatibility Matrix

| 来源/路径 | 实现 | 验证等级 | 当前证据 | 安全行为 |
|---|---|---|---|---|
| WaveInflu Native v1 | 已实现 | **Not Tested** | 纯合成 Fixture；公开产品页只确认 Excel 导出及字段类别，没有确认精确 Header | 签名不匹配时降级 Generic Mapping |
| Nox Native v1 | 已实现 | **Not Tested** | 纯合成 Fixture；官方帮助页只确认数据类别，没有确认精确 CSV Header | 签名不匹配时降级 Generic Mapping |
| Generic CSV | 已实现 | **Generic Import** | UTF-8/UTF-8-SIG、Header 校验、Mapping Preview 和变异测试 | 歧义列必须确认 |
| Generic XLSX | 已实现 | **Generic Import** | 未加密 `.xlsx`、显式工作表选择、Mapping Preview | 多个非空工作表不会静默选择 |
| EasyKOL 导出 | 无 Native Adapter | **Generic Import；vendor format Not Tested** | 没有合法格式样本 | 进入 Generic Mapping |
| CreatiVault 导出 | 无 Native Adapter | **Generic Import；vendor format Not Tested** | 没有合法格式样本 | 进入 Generic Mapping |
| 其他未知名单 | 无 Native Adapter | **Generic Import** | 取决于用户文件的列名和样例值 | 未映射列保留在 Raw Payload |

## 3. 已验证的工程行为

以下结论只验证导入机制，不验证第三方当前导出格式：

- 列顺序变化不影响 Native 签名。
- 增加无关列不影响 Native 签名，额外列保留在 Raw Payload。
- 删除非签名可选列不影响 Native 签名。
- Native 签名发生大小写、空格或字段名漂移时，不会误报 Native，而是降级 Generic Mapping。
- `128000`、`128K`、`1.2M` 可以标准化。
- `N/A`、`-` 和空值不会被虚构为 0。
- UTF-8-SIG 可以读取。
- 单行无效值不会阻断其他有效记录。
- XLSX 工作表名称变化可以通过 `--sheet` 显式选择。

完整变异定义见 [`../tools/format_variants.py`](../tools/format_variants.py)，Golden Tests 见 [`../tests/test_a2_adapter_evidence.py`](../tests/test_a2_adapter_evidence.py)。

本地生成 CSV 变异包：

```bash
python -m tools.format_variants \
  --input fixtures/nox_creators.csv \
  --output /tmp/kol-format-variants
```

命令生成 12 个 CSV 变异和 `manifest.json`。工作表名称变化复用仓库内合成 XLSX 的 `Creators` 工作表，通过 `--sheet` 路径测试，不复制第三方工作簿。

## 4. Open Alpha 证据门槛

Open Alpha 发布前要求：

- 至少一个来源达到 Verified；或
- 至少两个来源达到 Experimental。

**当前结果：未满足。**

WaveInflu 与 Nox 的公开页面能证明产品存在相关数据和导出能力，但不能证明仓库中的精确 Header 签名。因此二者继续标记为 Not Tested。

这不是导入功能故障，而是公开兼容声明的证据不足。获得合法脱敏格式前，不得将状态上调。

## 5. 状态升级流程

新证据必须：

1. 来源合法且用途明确。
2. 删除或替换 Handle、URL、Email、Platform ID、Display Name、品牌和内部备注。
3. 在 [`DATA_SOURCE_REGISTER.md`](DATA_SOURCE_REGISTER.md) 登记许可和再分发边界。
4. 与现有签名做 Schema Diff。
5. 通过 Native 检测、标准化、Raw Payload、端到端和 Schema Drift 测试。
6. 更新机器可读证据登记与 Adapter `evidence_ids`。

一位用户的新格式默认先走 Generic Mapping。只有重复需求、合法样本和维护成本均合理时，才考虑增加或修改 Native Adapter。

Open Alpha Adapter 请求登记、升级门槛和私有格式转化流程见：

- [`alpha/ADAPTER_REQUESTS.md`](alpha/ADAPTER_REQUESTS.md)
- [`alpha/PRIVATE_FORMAT_INTAKE.md`](alpha/PRIVATE_FORMAT_INTAKE.md)

当前真实 Adapter 请求数为 0，任何 Native 等级均未因 A6 而升级。

## 6. 公开声明边界

允许：

> Open Alpha 提供 WaveInflu-like 与 Nox-like 实验代码路径，但尚未验证真实导出格式；未知 CSV/XLSX 可通过 Mapping Preview 导入。

不允许：

> 已全面支持 Nox、WaveInflu、EasyKOL 和 CreatiVault。

> Native Adapter 命中代表第三方官方兼容。

> 当前 Fixture 是真实或脱敏第三方导出。
