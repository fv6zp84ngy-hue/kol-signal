# Open Alpha 社交平台发布素材

> 发布前替换 GitHub Release 链接；不要删除合成数据和业务效果限制声明。

## 主发布文案

我做了一个本地优先的 KOL 名单审计工具：KOL List Auditor Open Alpha。

它不是第五个“找达人数据库”，而是把两份或多份找人工具导出的 CSV/XLSX 进行：

- 字段标准化；
- 同平台确定性去重；
- 缺失、过期和冲突检查；
- Campaign 条件确认；
- Priority / Verify / Hold / Excluded 分类；
- Excel 导出和反馈回收。

公开案例使用 280 条完全合成记录：

- 规范化后 214 位达人；
- 46 个重复候选组；
- 18 个高冲突字段；
- 35 个过期关键字段；
- 20 位 Priority；
- 27 位 Verify。

这套案例不能推断实际业务收益，也不代表真实 Campaign 的回复率或转化率会提高。WaveInflu-like 和 Nox-like Adapter 当前仍是 `Not Tested`，发布的目的之一就是收集合法、脱敏的真实格式证据。

主要 CTA：

> 上传两份你从不同找人工具导出的名单，看看有多少重复、冲突和过期数据。

次要 CTA：

> 只提交表头和三行脱敏示例，帮助增加 Adapter 兼容性。

安装和 Demo：

```bash
pipx install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal demo
```

项目链接：`[发布时填写 GitHub Release URL]`

## 短文案

KOL List Auditor Open Alpha：把多份达人名单变成可解释的审计和联系优先级。

280 条完全合成记录的公开案例中，系统识别出 46 个重复组、18 个高冲突字段和 35 个过期关键字段。案例只展示工作流，不能推断实际业务收益；Native Adapter 仍为 `Not Tested`。

> 上传两份你从不同找人工具导出的名单，看看有多少重复、冲突和过期数据。

## Adapter 招募文案

如果你的导出格式无法被 Generic Mapping 正确识别：

> 只提交表头和三行脱敏示例，帮助增加 Adapter 兼容性。

不要发送原始名单、真实邮箱、Handle、主页 URL、品牌备注或 Token。优先使用仓库中的 Adapter Format Request。

