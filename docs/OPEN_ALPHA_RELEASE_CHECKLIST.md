# Open Alpha Release Checklist

```text
package_version: 0.5.0a1
expected_tag: v0.5.0-alpha.1
release_channel: Open Alpha
github_remote: missing
external_install_smoke_test: pending
owner_clean_env_smoke_test: passed
release_status: blocked_by_remote_ci_and_independent_smoke
```

## 本地候选已完成

- [x] README 首屏命令与 CLI 一致。
- [x] 完全合成 Demo。
- [x] 280 条完全合成公开案例及机器可读 Ground Truth。
- [x] Known Limitations。
- [x] Adapter Compatibility Matrix。
- [x] Release Notes、发布文案和反馈入口。
- [x] PII/Secret 扫描。
- [x] Wheel、Source Archive 和 Checksums 构建路径。

## 正式发布前阻断项

- [ ] 配置维护者确认的 GitHub Remote。
- [ ] 在 GitHub CI 实际通过 Ubuntu 3.11/3.12 和 Windows 3.12。
- [ ] 至少一名未参与开发者仅凭 README 下载 Artifact、校验、安装并运行 Demo。
- [x] 提交全部发布范围并建立干净、精确的 `v0.5.0-alpha.1` Tag。
- [x] Release Manifest 显示 `release_ready=true`。
- [x] 从 Tag 构建最终 Artifact 并再次校验 SHA-256。
- [ ] 创建 GitHub Open Alpha Release。

README-only 隔离安装 Smoke Test 已由维护者在源码目录外完成；由于执行者仍参与项目开发，不能替代未参与开发者的独立安装验证。

缺少 GitHub Remote、GitHub CI 实际通过或独立安装验证时，不得把本地候选描述成已经公开发布。
