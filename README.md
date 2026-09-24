# 【苏丹的游戏】事件分支查看器

一个使用 Python Tkinter 编写的本地事件数据查看工具，用于检索和阅读《苏丹的游戏》的事件说明、触发条件、结算条件与原始脚本。

《苏丹的游戏》结局查看器见：[Sultan_s_Game_Ending_Viewer](https://github.com/AC-HUB-AC/Sultan_s_Game_Ending_Viewer)。

## 主要功能

- 启动后自动加载应用内置数据，无需先选择游戏目录。
- 可切换到游戏当前安装目录中的事件数据，并可随时重置为内置数据。
- 支持按角色 ID、名称、别称或关键词检索角色。
- 支持按事件 ID、标题或关键词检索事件，并根据所选角色过滤事件。
- 查看事件说明、触发条件（Slot）、结算条件（Settlement）和事件原始脚本。
- 鼠标悬停条件行时高亮；点击条件可在下方查看完整内容。
- 可设置玩家名称，用于替换事件文本中的 `[player.name]`；替换后的名字会突出显示。
- 提供加载状态、空状态与错误提示，并自动跟随 Windows 明暗主题。

## 使用方法

### 下载并运行 exe

前往 [GitHub Releases](https://github.com/AC-HUB-AC/Sultan_s_Game_Event_Viewer/releases)，
从最新版本的 Assets 中下载 `苏丹的游戏事件查看器(GitHub：AC-HUB-AC).exe`，然后双击运行。

程序启动后会自动加载内置数据：

1. 在“角色”中输入角色 ID、名称、别称或关键词，也可以选择“所有人”。
2. 在“事件”中输入事件 ID、标题或关键词，然后选择目标事件。
3. 事件说明、触发条件、结算条件和原始脚本会自动刷新。
4. 在“玩家名称”中输入名字，可以查看 `[player.name]` 被替换后的实际效果。

### 使用游戏当前数据

如果游戏更新后需要读取最新事件，点击“选择游戏目录并重新加载数据”。程序支持选择以下任一目录：

- 游戏根目录 `Sultan's Game`
- `Sultan's Game_Data/StreamingAssets/config`
- `Sultan's Game_Data/StreamingAssets/config/rite`

Steam 中可通过“管理 → 浏览本地文件”找到游戏目录。选择完成后会自动重新加载，数据来源显示为“自定义目录”。点击“重置为内置数据”即可恢复随程序提供的数据。

> 内置数据对应 2022.3.58 版本，即 2025-04-01 前正式版的 1153 个事件。

## 界面说明

- **数据来源**：显示当前使用内置数据还是自定义目录。
- **玩家名称**：仅用于替换事件文本中的 `[player.name]`，不会参与筛选。
- **角色**：按角色相关信息过滤事件；选择“所有人”时显示全部事件。
- **事件**：按事件 ID、标题或关键词查找事件。
- **触发条件（Slot）**：事件卡槽及触发要求。
- **结算条件（Settlement）**：不同结果分支及其判定条件。
- 条件中的 `!` 表示否定，也就是“没有”或“不满足”。

## 从源码运行

项目只依赖 Python 标准库中的 Tkinter。建议在 Windows PowerShell 中使用 [uv](https://docs.astral.sh/uv/)：

```powershell
cd C:\path\to\Sultan_s_Game_Event_Viewer
uv run --python 3.11 python ".\event_viewer.py"
```

如果系统没有 Tkinter，请安装包含 Tcl/Tk 的完整 Python 3.11。

## 构建 Windows exe

在项目根目录执行：

```powershell
uv run --python 3.11 --with pyinstaller python -m PyInstaller --clean --noconfirm --distpath "." --workpath ".\.build" ".\conf\event_viewer.spec"
```

构建完成后，exe 会输出到项目根目录；中间文件位于 `.build/`。

如果项目根目录已经存在同名 exe，构建脚本会先将旧文件复制到
`releases/backup/`，并在文件名末尾添加构建时间，例如：

```text
苏丹的游戏事件查看器(GitHub：AC-HUB-AC)_20260925-120000-123.exe
```

备份成功后才会继续生成新版 exe；同一毫秒内重复构建时还会自动添加数字后缀，
不会覆盖已有备份。

构建产物不会提交到 Git 仓库。确认程序运行正常后，应创建对应版本的 Git 标签和
GitHub Release，并将新 exe 作为 Release Asset 上传。

## 常见问题

### Windows 阻止运行 exe

本项目提供的 exe 未进行商业代码签名，Windows 可能显示来源未知或阻止运行。可以先在文件“属性”中检查是否有“解除锁定”选项。若设备启用了不允许单独放行应用的安全策略，建议不要降低系统安全设置，直接按上面的步骤使用 Windows Python 源码运行。

### 加载自定义目录失败

请确认所选目录中能够找到：

```text
Sultan's Game_Data/StreamingAssets/config/rite/*.json
```

错误原因会同时显示在窗口状态栏和错误提示框中。

## 反馈

如遇到事件解析错误、角色关联不准确或有功能建议，欢迎提交 Issue，并尽量附上事件 ID、游戏版本和问题截图。
