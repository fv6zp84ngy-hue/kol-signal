# Open Alpha Known Limitations

> 适用版本：`0.5.0a1`  
> 状态：Open Alpha

## 产品验证边界

- 尚未经过目标用户业务效果验证。
- 不承诺提高回复率、正向回复率或合作转化率。
- 合成 Demo 和公开案例只验证工作流，不代表真实名单表现。
- 评分权重是可解释的初始假设，没有经过大样本校准。

## Adapter 边界

- WaveInflu-like Native Adapter：`Not Tested`。
- Nox-like Native Adapter：`Not Tested`。
- EasyKOL、CreatiVault 和其他来源：Generic Mapping；vendor format `Not Tested`。
- Native 签名命中不等于官方支持或未来格式兼容。
- 新 Adapter 必须满足真实需求、合法脱敏格式和维护成本门槛。

## 输入与平台边界

- 只支持 UTF-8/UTF-8-SIG CSV。
- 只支持未加密 `.xlsx`；不支持 `.xls`、加密文件和宏/VBA 检查。
- 不调用 Live API，不抓取 TikTok、Instagram 或 YouTube。
- 不做全平台实时监控、全量竞品数据库或邮箱查找服务。

## 决策与建联边界

- 只自动执行同平台确定性身份合并。
- 跨平台弱匹配和有反证的相同 Handle 不自动合并。
- 模糊 Campaign 表达可能进入未识别条件，不会被强行解释。
- 不自动发送邮件，不安装 Gmail/飞书连接器，不自动谈判。
- 不预测报价、排他关系或合同状态。
- Feedback 只提供描述统计，不自动调权。

## 分发与支持边界

- Open Alpha 不等于 Stable、Production Ready 或 Public Beta。
- 当前声明的 CI 目标是 Ubuntu Python 3.11/3.12 和 Windows Python 3.12；只有 GitHub Workflow 实际通过后才视为已验证。
- macOS 目前通过本地手动验证，不代表所有 Python 发行版或系统环境。
- 不支持所有旧版 Office、全局 Python 污染环境或极小众系统。

## 隐私与诊断边界

- 核心流程在本地运行，但 Run 目录包含完整联系信息，用户必须自行保护。
- `kol-signal diagnostics` 使用固定白名单且不读取原始输入；分享前仍需人工检查 ZIP。
- 项目不提供遥测服务器，不默认收集或上传使用数据。

