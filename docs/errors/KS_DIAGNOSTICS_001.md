# KS_DIAGNOSTICS_001

## 错误原因

Diagnostics 无法找到指定 Run、Run ID 不安全、`manifest.json` 缺失/损坏，或 Manifest Schema 不受支持。Diagnostics 不会为了恢复信息去读取原始达人名单。

## 数据风险

该错误不会修改 Run，也不会上传任何数据。它只表示当前无法生成可公开提交的脱敏诊断包。

## 下一步

1. 确认 `RUN_ID` 是目标 Run 目录名称。
2. 如果 Run 不在默认 `runs/` 下，显式提供 `--runs-dir`。
3. 使用新 ZIP 文件名：

```bash
kol-signal diagnostics --run RUN_ID --output diagnostics.zip
```

自定义 Run 根目录时：

```bash
kol-signal diagnostics \
  --run RUN_ID \
  --runs-dir PATH_TO_RUNS \
  --output diagnostics.zip
```

## 脱敏信息

如果仍然失败，只提交 `kol-signal --version`、`kol-signal doctor` 的非敏感结果、公开错误码和“Manifest 是否存在”。不要提交 Manifest 原文、原始 Run、绝对路径或输入文件。

