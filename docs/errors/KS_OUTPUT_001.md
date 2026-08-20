# KS_OUTPUT_001

## 错误原因

系统无法安全创建输出。常见原因包括目录不可写、文件被锁定、目标已存在，或可用磁盘空间不足。Diagnostics ZIP 永远不会覆盖已有文件。

## 数据风险

原始输入不会被修改。已有 Run 或已有 Diagnostics ZIP 不应被覆盖；如果看到了部分新文件，请保留它们并换一个新输出目录重试。

## 下一步

1. 选择一个可写的新目录或新文件名。
2. 关闭可能锁定 XLSX/ZIP 的程序。
3. 运行 `kol-signal doctor`。
4. 对已有 Run 可执行：

```bash
kol-signal diagnostics --run RUN_ID --output diagnostics-new.zip
```

## 脱敏信息

可提交公开错误码、操作系统、Python 版本、输出阶段和脱敏诊断包。不要公开完整绝对路径、用户名、原始文件名或 Run 内容。

