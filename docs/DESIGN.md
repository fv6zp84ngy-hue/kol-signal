# Creator Signal Intelligence — Public Beta Design

> 版本：v0.2  
> 范围状态：Scope Frozen  
> 设计目标：以最低基础设施成本，支持真实用户上传名单、获得可信结果并回传反馈  
> 架构原则：本地优先、确定性优先、模型可选、外部写入最少

## 0. 范围冻结

在首轮真实用户测试前，架构只服务以下 P0 链路：

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

不得为了 Backlog 功能预建服务器、连接器协议、复杂事件模型或前端基础设施。冻结期间只接受核心链路 Bug、数据安全问题和阻断验收的必要修正。

## 1. 设计结论

Public Beta 使用四层结构：

1. Skill 交互层
2. 本地 Python 应用层
3. SQLite 数据与运行产物层
4. 可选模型增强层

不建设服务器端 SaaS，不保存用户数据到公共云，不依赖第三方实时 API 才能完成核心流程。

核心流程：

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

## 2. 技术选择

- Python 3.11+
- SQLite
- Pandas 或 Polars
- Pydantic
- Typer 或 Click
- OpenPyXL
- Jinja2
- 可选模型 Provider
- Pytest

不要求：

- Web Server
- 用户登录
- 云数据库
- 消息队列
- Redis
- 容器编排
- 实时任务系统

## 3. 产品入口

### 3.1 Codex Skill

Skill 负责：

- 引导用户上传文件。
- 从自然语言提取 Campaign Brief。
- 展示字段映射预览。
- 解释运行结果。
- 帮助用户处理 Review Queue。
- 返回输出文件。

Skill 不负责：

- 保存隐藏业务规则。
- 直接决定身份合并。
- 无来源生成事实。
- 自动发送邮件。

### 3.2 CLI

CLI 是稳定执行入口，主要供开发、调试和高级用户使用。

推荐主命令：

```text
kol-signal run
kol-signal review
kol-signal feedback
kol-signal demo
```

普通用户不需要理解完整命令。

## 4. 核心模块

### 4.1 Import and Mapping

职责：

- 读取 CSV/XLSX。
- 自动检测编码和工作表。
- 识别常见字段。
- 提供字段映射预览。
- 保存原始行和来源信息。
- 允许用户修正映射。

采用两类 Adapter：

#### Native Adapter

首发仅维护两个真实常用来源。

#### Generic Mapping Adapter

通过列名、样例值和模型辅助推测字段。

模型只负责建议映射，最终映射必须通过结构校验，存在歧义时由用户确认。

### 4.2 Normalization

负责：

- Platform 枚举统一。
- Handle 规范化。
- Profile URL 规范化。
- Followers、Views 和 Engagement Rate 解析。
- Country 和 Language 标准化。
- Email 格式基础校验。
- 日期统一为带时区格式。

无效数据不得静默转为 0。

### 4.3 Identity Resolution

Public Beta 只执行同平台确定性合并。

自动合并条件：

1. Platform ID 相同。
2. 规范化 Profile URL 相同。
3. 同平台 Handle 相同，且不存在不同 Platform ID 或 URL 的反证。

以下情况进入人工审核：

- 同名不同账号。
- Handle 相同但 URL 冲突。
- 跨平台疑似同一人。
- 共享经纪邮箱。
- 只有邮箱或 Display Name 相同。

系统不在第一版实现复杂跨平台身份图谱。

### 4.4 Data Quality Engine

每个关键字段保存多个来源观测，并选出当前采用值。

简化优先级：

```text
已验证结果
> 达人主页公开信息
> 更新时间更近的数据库值
> 较旧或明确标记为估算的数据
```

实际实现使用配置化字段来源优先级，不在代码中写死全局“最佳平台”。

质量状态：

- Fresh
- Stale
- Conflict
- Missing
- Estimated
- Review Required

冲突检测：

- 数值字段使用相对差异。
- 分类字段比较规范值。
- Email 分别处理个人邮箱和经纪公司邮箱。
- 身份相关冲突一律进入 Review Queue。

### 4.5 Campaign Decision Engine

输入：

- 品牌与产品。
- 目标市场。
- 语言。
- 内容主题。
- 产品场景。
- 达人规模。
- 必要联系路径。
- 排除条件。

输出四类：

- Priority
- Verify
- Hold
- Excluded

内部保留参考评分，但用户界面首先显示行动等级和理由。

评分维度：

#### Brand Fit

- 地区和语言匹配。
- 内容主题匹配。
- 产品场景匹配。
- 内容形式匹配。

#### Commercial Readiness

- 最近是否活跃。
- 是否存在商业合作信号。
- 是否公开合作入口。
- 广告密度是否过高或证据不足。

#### Contactability

- 是否存在可用联系路径。
- 邮箱来源。
- 邮箱新鲜度。
- 历史退信或送达结果。

#### Data Confidence

- 关键字段覆盖。
- 数据是否新鲜。
- 来源是否一致。
- 是否存在身份或联系方式冲突。

P0 的主题、内容形式和商业合作信号只使用导入名单中已有的结构化字段或用户在 Campaign Brief 中明确提供的信息。系统不抓取、不读取也不分析达人近期内容；证据不足时降低 Data Confidence 或进入 Verify。

### 4.6 Reporting and Export

每次运行生成：

```text
runs/<run_id>/
├── manifest.json
├── data_audit.xlsx
├── creator_shortlist.xlsx
├── merge_review.xlsx
├── feedback_template.xlsx
├── report.md
└── warnings.json
```

首发不直接写入 Gmail 或飞书。

用户可以：

- 下载 Excel。
- 导入飞书。
- 导入 Airtable。
- 导入 Google Sheets。

### 4.7 Feedback Import

用户完成审核或建联后，将 Feedback Template 重新导入。

系统记录：

- Merge Correct
- Shortlist Accepted
- Contact Correct
- Actually Contacted
- Delivered
- Bounced
- Replied
- Positive Reply
- Feedback Note

系统只输出描述统计和规则改进建议，不自动调整生产评分。

## 5. 简化数据模型

Public Beta 只需要以下核心表：

### import_batches

记录一次文件导入。

### source_records

保存原始行、来源和行定位。

### creators

保存规范化后的达人身份。

### observations

保存字段值、来源、时间和状态。

### runs

保存本次 Campaign、配置和输出路径。

### decisions

保存候选等级、参考分数、理由和警告。

### feedback

保存人工审核与建联结果。

不在首发阶段实现：

- 完整 merge decision 事件链。
- 独立成本账本。
- 复杂项目状态事件。
- 完整邮件事件图。
- 多层模型缓存实体。
- 外部连接器统一执行协议。

必要的审计信息可暂时保存在 JSON 字段和运行产物中。

## 6. 运行确定性

相同的：

- 输入文件内容。
- 字段映射。
- Campaign Brief。
- 规则版本。
- 模型缓存结果。

应产生相同的：

- 合并结果。
- 数据状态。
- 候选等级。
- 排名。
- 输出文件。

每次运行保存：

- 输入文件 Hash。
- Campaign 配置。
- 规则版本。
- 模型名称和 Prompt 版本。
- 输出文件 Hash。

不需要首发实现复杂中断恢复。

## 7. 隐私与安全

必须：

- 默认本地运行。
- 原始文件、数据库和运行产物加入 `.gitignore`。
- 报告默认遮蔽邮箱。
- 示例使用虚构身份和 `example.com`。
- 不保存 API Token。
- 首版不连接 Gmail，也不请求 Gmail 权限。
- 不自动发送任何邮件。
- 不把用户名单上传到公开服务，除非用户明确启用模型能力并了解数据边界。

Public Beta 用户须明确知道：

- 哪些数据在本地处理。
- 哪些文本可能被发送给模型。
- 如何关闭模型增强。
- 如何删除工作目录。

## 8. 风险控制

### 字段格式变化

通过 Mapping Preview 和 Generic Adapter 降低维护压力。

### 错误身份合并

只自动执行确定性同平台合并，其他情况进入人工审核。

### 模型幻觉

模型结果不得成为无证据事实，也不得直接决定合并和最终评分。

### 用户输入缺失

缺失数据降低 Data Confidence，不自动视为负面事实。

### API 或插件不可用

核心流程只依赖本地文件。

### 结果伪精确

对外优先展示 Priority、Verify、Hold 和 Excluded；参考分数只作为辅助。

## 9. 冻结后的开发阶段

### M0：离线核心

- 通用文件导入。
- 两个 Native Adapter。
- 字段映射预览。
- 标准化。
- 确定性去重。
- 数据质量审计。
- Campaign Shortlist。
- Excel 和 Markdown 输出。

### M1：可试用产品

- Skill 引导流程。
- Review Queue。
- Feedback Template。
- Feedback Import。
- 安装文档。
- 模拟数据 Demo。
- 首批真实格式适配。

M0 和 M1 共同构成冻结后的 Public Beta P0。两者完成前不得并行建设 Backlog 功能。

## 10. Backlog

以下能力不属于 Public Beta P0，不得阻塞首版：

- Gmail 草稿。
- 飞书真实连接器。
- Live API。
- 竞品分析。
- 自动发邮件。
- 复杂内容分析、合作角度和个性化开头。
- A/B/C 实验。
- 自动调整评分权重。
- SaaS 前端。

只有首轮真实用户测试完成后，才可依据用户证据重新排序 Backlog。

## 11. 设计成功标准

该架构成功，不以代码量衡量，而以以下结果衡量：

- 新用户能在一次引导中完成名单导入。
- 常见表格无需手工写 Mapping YAML。
- 去重结果可信。
- 用户能够理解为什么某人进入 Priority。
- 输出可以直接进入现有工作流。
- 用户能方便地指出系统哪里判断错误。
- 第三方服务不可用时，核心产品仍能运行。
