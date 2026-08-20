# Open Alpha 完全合成案例

> 数据分类：完全合成（Fully Synthetic）  
> 行业场景：宠物智能硬件出海  
> 参考时间：2026-07-31  
> 用途：只展示工作流和输出

这套案例由 [`tools/generate_open_alpha_case.py`](../../tools/generate_open_alpha_case.py) 确定性生成，不包含真实达人、邮箱、主页、平台 ID、品牌数据或客户备注。所有联系地址均使用 `example.com` 保留域。

## 案例结果

- 原始记录：280
- 规范化记录：214
- 重复候选：46
- 高冲突字段：18
- 过期关键字段：35
- Priority：20
- Verify：27

其中 46 个重复组由 20 个三记录组和 26 个双记录组组成，因此 280 条来源记录最终归并为 214 位规范化达人。

这些数字经过 [`tests/test_a5_open_alpha_release.py`](../../tests/test_a5_open_alpha_release.py) 直接运行当前去重、冲突、新鲜度和评分规则验证，不是手工填写的宣传数字。

## 如何复现

```bash
kol-signal run \
  --input examples/open_alpha_case/waveinflu_case.csv \
  --input examples/open_alpha_case/nox_case.csv \
  --brief examples/open_alpha_case/campaign.txt \
  --output open-alpha-case-runs \
  --non-interactive
```

输入：

- `waveinflu_case.csv`：140 条 WaveInflu-like 合成记录。
- `nox_case.csv`：140 条 Nox-like 合成记录。
- `campaign.txt`：美国、英语、TikTok、10K–500K、30 天活跃和必须有联系路径。
- `expected_metrics.json`：机器可读 Ground Truth。

输出与普通用户 Run 相同，包含 Audit、Shortlist、Merge Review、Feedback Template、Report、Campaign 配置和 Manifest。

## 正确理解

该案例不能推断实际业务收益，也不能证明真实 Campaign 的回复率、正向回复率或合作转化会提高。

它只展示工作流和输出：

```text
多份名单
→ 标准化与确定性去重
→ 缺失/过期/冲突审计
→ Campaign 硬过滤与参考评分
→ Priority / Verify / Excluded
→ Excel 导出
```

WaveInflu-like 和 Nox-like 只描述合成表头结构，不代表两个第三方 Adapter 已经通过真实导出验证。当前验证等级见 [`docs/ADAPTER_COMPATIBILITY.md`](../../docs/ADAPTER_COMPATIBILITY.md)。

