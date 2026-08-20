# 内测用户反馈数据

本报告是基于 fixed virtual Persona cohort 的 simulated-user artifact-level A/B internal evaluation。它不是真人客户研究、Agency 从业者访谈或生产环境业务效果数据。

## 1. Summary

在固定 Campaign、固定 virtual Persona cohort、固定任务和一致条件下，内部配对测试比较了直接查看多源名单与使用产品审计产物后的 shortlist 决策。

- 候选决策面规模：120 → 61（↓ 49.2%）
- Qualified Creator Precision@10：78.5% → 100.0%（+21.5pp）
- Shortlist 任务成功率：83.0% → 100.0%（+17.0pp）
- 决策信心：3.0/5 → 3.4/5（+0.4）
- 样本：N=100 个有效配对测试

“候选决策面规模”是由 benchmark pipeline 定义的、需要继续判断的候选数量，不等同于人工审核工时、人工效率或成本节省；该比例也不应解释为人工工时减少比例。

## 2. Current Product Version

- Product version: `0.5.0a1`
- Benchmark version: `1.0`
- Task version: `shortlist-v1`

## 3. Sample Size

- Planned pairs: 100
- Valid pairs: 100
- Pair coverage: 100.0%

## 4. Test Scenario

本次为 `single-scenario internal evaluation`，数据分类为 `fully_synthetic`，使用仓库批准的 Fixture 与预先冻结的 Campaign Ground Truth。

## 5. Baseline Definition

Baseline persona 直接面对 Campaign Brief 与原始多来源名单，不可见产品 score、audit label、shortlist label、Ground Truth 或 Treatment 输出。

## 6. Treatment Definition

Treatment 使用同一 Campaign 和同一份数据，由当前产品 pipeline 实际生成的审计与 shortlist artifact；没有手工修改产品输出。

## 7. Results

候选决策面规模、Precision 和任务成功率属于确定性或 pipeline-derived 证据；Decision Confidence 是 simulated-user self-report，不能与确定性指标混为一谈。

## 8. Confidence Intervals

- Precision paired delta 95% bootstrap CI: [+19.8pp, +23.4pp]
- Success paired delta 95% bootstrap CI: [+10.0pp, +25.0pp]
- Confidence paired delta 95% bootstrap CI: [+0.3, +0.5]

Bootstrap 以 persona pair 为重采样单位，并使用 experiment seed `20260813`；区间不代表模拟用户可以替代真人总体推断。

## 9. Cohort Summary

Persona model: `deepseek-v4-flash`; model version: `DeepSeek-V4-Flash`。完整 persona IDs 仅保存在本地 machine-readable summary。

## 10. Valid / Failed Trial Accounting

- Imported trials: 200
- Valid pairs: 100
- Invalid/incomplete pairs: 0
- Orphan trials: 0

失败、缺失和 schema-invalid trial 保留在本地证据中，没有替换 persona 或只保留成功结果。

## 11. Methodology

实验固定 persona cohort、case、task、K，以及 Baseline/Treatment 的 provider/model 配置，仅改变 condition。`experiment_seed` 用于 cohort、bootstrap 和实验工作流的固定；当前 `provider_seed_supported=false`，因此不声称模型生成具有 seed-level deterministic reproducibility，也不将两次调用视为 bit-for-bit 可复现。确定性 verifier 检查 ID、重复选择、Campaign 硬条件和冻结 Ground Truth；模型只产生选择与五点信心自评。

## 12. Limitations

这是 fixed virtual Persona cohort 的 simulated-user artifact-level 内部评估，不是真人客户研究、Agency 从业者访谈或生产环境业务效果。Fixture 为 synthetic/redacted approved data；当前只有 single-scenario internal evaluation，没有多 Campaign 外部验证。当前没有内容主题 Ground Truth，因此 Qualified 只表示通过冻结硬条件，不代表完整 Brand Fit、真实合作意愿或实际回复率。候选决策面规模是 pipeline-derived 数量，不代表人工工时、人工效率或成本变化。Decision Confidence 是模型条件下的 self-report，不能替代真人量表或用户访谈。Provider inference 不承诺 seed-level deterministic reproducibility；结果可能受模型版本、服务端行为和运行时差异影响。重要结论仍需真人测试、不同 persona-model robustness run，以及真实工作流中的独立校准；本报告不构成因果业务收益承诺。

## 13. Reproduction Metadata

- Run ID: `p5_deepseek_20260813`
- Git commit: `c0221eb5c0ce5bd28d47100f8d14b8159c6db435`
- Git dirty at prepare: `true`
- Persona sampling seed: `20260813`
- Bootstrap iterations: `10000`
- Bootstrap seed: `20260813`
- Experiment seed 用于 cohort、bootstrap 和实验工作流；`provider_seed_supported=false`，不代表 provider inference 可按 seed 完全重现。

聚合数字由 `summary.json` 自动生成，完整 pair、trial、verifier 与 Fixture hash 证据保存在对应本地 benchmark run 中。
