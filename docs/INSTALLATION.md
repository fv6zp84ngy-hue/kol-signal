# CLI Installation and Uninstallation

> 适用版本：`0.5.0a1`
> 分发方式：GitHub Release Wheel
> PyPI：尚未发布

## 1. 下载与校验

从同一个 GitHub Release 下载：

```text
kol_signal-0.5.0a1-py3-none-any.whl
SHA256SUMS
```

### macOS / Linux

```bash
shasum -a 256 -c SHA256SUMS
```

### Windows PowerShell

```powershell
Get-FileHash .\kol_signal-0.5.0a1-py3-none-any.whl -Algorithm SHA256
```

将结果与 `SHA256SUMS` 中的 Wheel Hash 比较。Windows 不要求直接执行 Unix 格式的校验命令。

## 2. 推荐：pipx

以下命令假设设备已经安装并配置好 `pipx`。本项目不会自动修改全局 Python。

### macOS

```bash
pipx install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
kol-signal doctor
```

### Linux

```bash
pipx install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
kol-signal doctor
```

### Windows PowerShell

```powershell
pipx install .\kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
kol-signal doctor
```

如果 `pipx` 不可用，使用下一节的独立虚拟环境，不要把包安装到不明确的全局 Python。

## 3. 独立虚拟环境

### macOS / Linux

```bash
python3 -m venv kol-signal-env
source kol-signal-env/bin/activate
python -m pip install ./kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
```

### Windows PowerShell

```powershell
py -3.11 -m venv kol-signal-env
.\kol-signal-env\Scripts\Activate.ps1
python -m pip install .\kol_signal-0.5.0a1-py3-none-any.whl
kol-signal --version
```

支持矩阵只声明 Python 3.11 及以上、当前发行 Wheel 和 OpenPyXL 3.x。不承诺 `.xls`、加密 Excel、所有 Python 发行版或被全局依赖污染的环境。

## 4. 首次验证

在任意可写目录运行：

```bash
kol-signal doctor
kol-signal demo
```

Demo 默认写入当前目录的：

```text
kol-signal-demo/<run_id>/
```

它不读取用户文件、不访问网络，也不需要源码仓库。

## 5. 卸载 CLI

### pipx

```bash
pipx uninstall kol-signal
```

### 虚拟环境

先退出虚拟环境，再删除你明确创建的 `kol-signal-env` 目录。删除前确认该目录只用于本项目。

卸载只移除 CLI 环境，**不会删除**：

- 当前目录或其他目录中的历史 Run。
- `runs/`。
- `kol-signal-demo/`。
- `.kol-signal/mappings/`。
- 用户单独安装的 Codex Skill。

历史 Run 是否删除由用户决定，本项目没有自动清理命令。

## 6. 升级

下载新 Release 的 Wheel 和 Checksums，先校验，再让 `pipx` 或对应虚拟环境执行升级。不要复用未经确认的旧文件名或第三方镜像。

## 7. 已知分发限制

- 当前不发布 PyPI。
- Wheel 不包含 Codex Skill。
- Wheel 不安装 Gmail、飞书或其他插件。
- GitHub Release URL 尚未写入包元数据。
- Open Alpha 前仍需满足 Adapter 外部格式证据门槛。
