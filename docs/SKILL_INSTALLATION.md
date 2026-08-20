# Codex Skill Installation and Uninstallation

> Skill：`creator-signal-intelligence`
> 安装方式：从 GitHub Source Archive 手工复制
> CLI 与 Skill：独立安装、独立卸载

## 1. 安装前

先安装并验证 CLI：

```bash
kol-signal --version
kol-signal doctor
```

从 GitHub Release 的 Source Archive 解压仓库，确认以下文件存在：

```text
skills/creator-signal-intelligence/
├── SKILL.md
├── agents/openai.yaml
└── references/cli-workflow.md
```

Skill 安装不会安装 CLI，也不会安装 Gmail、飞书或其他插件。

## 2. macOS

默认目标目录：

```text
~/.codex/skills/creator-signal-intelligence/
```

如果设置了 `CODEX_HOME`，目标目录是：

```text
<CODEX_HOME>/skills/creator-signal-intelligence/
```

安装前先展示并检查目标目录。若同名目录已经存在，停止操作；默认**不覆盖**：

```bash
codex_root="${CODEX_HOME:-$HOME/.codex}"
skill_target="$codex_root/skills/creator-signal-intelligence"
test ! -e "$skill_target"
mkdir -p "$codex_root/skills"
cp -R skills/creator-signal-intelligence "$skill_target"
test -f "$skill_target/SKILL.md"
```

任一检查失败时不要继续复制。

## 3. Linux

默认目录和检查流程与 macOS 相同：

```bash
codex_root="${CODEX_HOME:-$HOME/.codex}"
skill_target="$codex_root/skills/creator-signal-intelligence"
test ! -e "$skill_target"
mkdir -p "$codex_root/skills"
cp -R skills/creator-signal-intelligence "$skill_target"
test -f "$skill_target/SKILL.md"
```

不要使用 `sudo` 将 Skill 写入其他用户或系统级目录。

## 4. Windows PowerShell

```powershell
$profileRoot = [Environment]::GetFolderPath("UserProfile")
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $profileRoot ".codex" }
$skillTarget = Join-Path $codexRoot "skills\creator-signal-intelligence"
$skillTarget
if (Test-Path $skillTarget) { throw "Target already exists; installation stopped." }
New-Item -ItemType Directory -Force -Path (Join-Path $codexRoot "skills")
Copy-Item -Recurse "skills\creator-signal-intelligence" $skillTarget
if (-not (Test-Path (Join-Path $skillTarget "SKILL.md"))) { throw "SKILL.md validation failed." }
```

目标存在时不覆盖，不使用 `-Force` 覆盖 Skill 内容。

## 5. 使 Skill 生效

确认 `SKILL.md` 存在后：

1. 重启 Codex，或开启新任务。
2. 显式调用：

```text
使用 $creator-signal-intelligence 审计我上传的达人名单。
```

当前任务的 Skill 列表通常在启动时加载；复制成功不代表当前任务立即可用。

## 6. 卸载 Skill

先关闭正在使用该 Skill 的 Codex 任务，再确认目标是精确的：

```text
creator-signal-intelligence
```

只删除该 Skill 目录，不删除父级 `skills`、`.codex`、CLI 环境或项目 Run。

### macOS / Linux

```bash
codex_root="${CODEX_HOME:-$HOME/.codex}"
skill_target="$codex_root/skills/creator-signal-intelligence"
test -f "$skill_target/SKILL.md"
rm -r "$skill_target"
```

### Windows PowerShell

```powershell
$profileRoot = [Environment]::GetFolderPath("UserProfile")
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $profileRoot ".codex" }
$skillTarget = Join-Path $codexRoot "skills\creator-signal-intelligence"
if (-not (Test-Path (Join-Path $skillTarget "SKILL.md"))) { throw "Skill target validation failed." }
Remove-Item -Recurse $skillTarget
```

卸载后重启 Codex 或开启新任务。CLI、历史 Run 和 Mapping 配置不会受到影响。

## 7. 安全边界

- 安装动作必须由用户明确执行。
- 不自动写入用户 Codex 目录。
- 不覆盖同名 Skill。
- 不复制真实名单、Run 或 Mapping 配置。
- 不自动连接外部服务。
