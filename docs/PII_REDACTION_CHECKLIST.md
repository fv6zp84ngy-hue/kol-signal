# Public Fixture PII Redaction Checklist

> 版本：v1
> 适用范围：Fixture、Golden Truth、日志、报告截图和诊断材料

## 1. 接收前

- [ ] 文件由提供者合法取得并允许用于格式兼容验证。
- [ ] 明确是否允许保存、修改、提交仓库或只允许本地查看。
- [ ] 不接收来源不明、爬取或违反第三方条款的数据集。
- [ ] 原始文件不进入 Git 工作区；优先保存在临时、本地隔离目录。

## 2. 必须替换

- [ ] Handle。
- [ ] Profile URL。
- [ ] Email。
- [ ] Platform Creator ID。
- [ ] Display Name。
- [ ] 品牌、项目、客户和经纪公司名称。
- [ ] 内部备注、报价、合同、沟通记录和 Campaign 敏感文本。
- [ ] 文件属性中的作者、公司和绝对路径。

## 3. 应保留的结构

- [ ] Header 名称、顺序和数据类型，仅在许可允许时保留。
- [ ] 空值位置或经过等比例重建的空值分布。
- [ ] 日期、数字、百分比和布尔格式。
- [ ] 工作表数量与名称模式；敏感名称需替换。
- [ ] 重复、冲突、失效值和 Schema Drift 关系。
- [ ] 关键异常都有独立 Ground Truth。

## 4. 公开前自动检查

- [ ] 文本文件中不存在非 `example.com` Email。
- [ ] XLSX 单元格中不存在非 `example.com` Email。
- [ ] URL 使用 `example.com` 或虚构本地域名。
- [ ] 不存在 Token、私钥、API Key 或 Cookie。
- [ ] 不存在 `/Users/...`、公司共享盘或内部目录路径。
- [ ] Fixture Manifest 声明 `data_classification`。
- [ ] `DATA_SOURCE_REGISTER` 中许可与再分发状态完整。
- [ ] 测试、构建和 Demo 后 Git 不出现原始输入或 Run 产物。

## 5. 人工抽检

- [ ] 随机抽检至少十行，确认替换后仍保留关系一致性。
- [ ] 检查共享邮箱、重复达人和 Handle 冲突没有因脱敏被意外改变。
- [ ] 检查备注列没有自然语言残留。
- [ ] 检查工作簿 Document Properties。
- [ ] 复核“真实、脱敏、合成、官方样例”等公开措辞与实际证据一致。

## 6. 失败处理

发现疑似 PII 或授权不明时：

1. 停止提交和分发。
2. 从公开产物中移除文件。
3. 重新生成结构合成版，不在原文件上做零散覆盖。
4. 如果内容已经进入 Git 历史，按 `SECURITY.md` 处理并轮换可能泄露的凭据。
5. 证据不足时将 Adapter 保持为 Not Tested 或 Generic Import。
