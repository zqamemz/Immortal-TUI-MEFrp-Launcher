# ITML- ME Frp TUI Manager

在 SSH 和真实命令行环境下使用的 **ME Frp** 图形化终端管理程序。

> 基于 [Textual](https://textual.textualize.io/) 框架构建，无需 WebUI，直接在终端中运行。

## 目录

- [功能](#功能)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [mefrpc 说明](#mefrpc-说明)
- [Systemd 服务管理](#systemd-服务管理)
- [配置说明](#配置说明)
- [快捷键](#快捷键)
- [项目结构详解](#项目结构详解)
- [API 参考](#api-参考)
- [依赖](#依赖)
- [常见问题](#常见问题)
- [许可证](#许可证)

## 功能

- 🔐 **登录** — 密码登录、Token 登录，自动完成人机验证
- 📊 **仪表盘** — 实时显示统计信息、用户信息、快捷入口
- 🔌 **隧道管理** — 隧道列表、创建、启用/禁用、删除
- 📍 **节点信息面板** — 创建隧道时右侧展示节点简介、协议、带宽、负载等
- ⚙️ **Systemd 守护** — 将隧道安装为 systemd 服务，实现开机自启/进程守护
- 📅 **每日签到** — 支持人机验证
- 🎁 **权益抽取** — 抽奖功能，查看剩余次数
- � **内置 mefrpc** — 首次启动自动安装，无需单独下载 frpc
- �🚪 **智能退出** — 保持隧道退出 / 关闭所有隧道退出

## 截图

```
┌─────────────────────────────────────────────────────┐
│  SML - ME Frp Manager                      v1.0.0   │
├─────────────────────────────────────────────────────┤
│           欢迎回来, 张三 ！                          │
├──────────┬──────────┬──────────┬──────────┤         │
│  1024    │   12     │    8     │  已登录   │         │
│ 在线用户  │  节点数   │ 我的隧道  │  状态     │         │
├──────────┴──────────┴──────────┴──────────┤         │
│          快捷操作                           │         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │         │
│  │ 隧道列表 │ │新建隧道 │ │每日签到 │       │         │
│  └─────────┘ └─────────┘ └─────────┘       │         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │         │
│  │权益抽取 │ │  设置   │ │  退出   │       │         │
│  └─────────┘ └─────────┘ └─────────┘       │         │
├─────────────────────────────────────────────┤         │
│  Ctrl+Q 退出  Ctrl+R 刷新  Esc 返回        │         │
└─────────────────────────────────────────────┘         │
```

## 快速开始

### 0. 安装 Git（如尚未安装）

本项目通过 Git 克隆源码。若系统中还没有 `git` 命令，请先安装：

**Debian / Ubuntu：**

```bash
sudo apt update
sudo apt install -y git
```

**CentOS / RHEL / Rocky / AlmaLinux：**

```bash
# CentOS 7
sudo yum install -y git

# CentOS 8+ / RHEL 8+ / Rocky / Alma
sudo dnf install -y git
```

**Arch Linux：**

```bash
sudo pacman -S git
```

**验证安装：**

```bash
git --version
# 示例输出: git version 2.x.x
```

### 1. 克隆项目

```bash
git clone https://github.com/zqamemz/Immortal-TUI-MEFrp-Launcher.git
cd Immortal-TUI-MEFrp-Launcher
```

### 2. 创建并激活 Python 虚拟环境

强烈建议使用虚拟环境，避免与系统 Python 包冲突。

```bash
# 创建虚拟环境（目录名 venv 可自定义）
python3 -m venv venv
```

**激活虚拟环境：**

```bash
# Linux / macOS（bash / zsh）
source venv/bin/activate

# 若使用 fish shell
# source venv/bin/activate.fish
```

激活成功后，终端提示符前通常会出现 `(venv)`，例如：

```text
(venv) user@host:~/Immortal-TUI-MEFrp-Launcher$
```

后续的 `pip` / `python` 命令都在该虚拟环境中执行。退出虚拟环境可输入：

```bash
deactivate
```

> **提示：** 每次新开终端后，进入项目目录并重新执行 `source venv/bin/activate` 即可继续使用。

### 3. 安装依赖（使用 requirements.txt）

请先确认虚拟环境已激活（提示符有 `(venv)`），再安装：

```bash
# 升级 pip（可选）
pip install -U pip

# 按依赖文件安装
pip install -r requirements.txt

# 以可编辑模式安装本项目（生成 sml / sml-install 命令）
pip install -e .
```

安装完成后，程序会在首次运行时自动部署内置的 `mefrpc`；也可手动执行：

```bash
sml-install
```

### 4. 运行

```bash
# 直接启动（需已激活虚拟环境且已 pip install -e .）
sml

# 或者使用 Python 模块
python -m sml
```

### 5. 首次使用

1. 启动程序后，使用已有账号密码或访问 Token **登录**
2. 登录后进入主菜单，可通过 **设置** 配置 frpc / mefrpc 路径
3. 在 **隧道列表** 中查看已有隧道，或 **新建隧道**
4. 进入隧道详情可 **安装 Systemd 服务** 实现进程守护

---

## 使用说明

### 界面导览

| 界面 | 入口 | 作用 |
|------|------|------|
| 登录页 | 首次启动 / 无 Token | 密码登录或 Token 登录 |
| 主菜单 | 登录成功后 | 统计卡片、快捷按钮、账户信息 |
| 隧道列表 | 主菜单 → 隧道列表 | 查看、刷新、启动/停止、删除隧道 |
| 新建隧道 | 主菜单 / 隧道列表 → 新建 | 填写表单；右侧滚动查看节点卡片 |
| 隧道详情 | 隧道列表 → 查看详情 | 配置查看、Systemd 安装/启停 |
| 每日签到 | 主菜单 → 每日签到 | 自动完成验证并签到 |
| 权益抽取 | 主菜单 → 权益抽取 | 查看剩余次数并发起抽奖 |
| 设置 | 主菜单 → 设置 | frpc 路径、默认节点、清除 Token |
| 退出确认 | `Ctrl+Q` 或主菜单退出 | 选择保持/关闭隧道后退出 |

### 登录

1. **密码登录**：填写用户名与密码，程序自动完成隐式人机验证后提交。
2. **Token 登录**：若已有 API Token，可在设置或配置文件中写入；下次启动若本地已有 Token 将直接进入主菜单。
3. 登录成功后 Token 保存在 `~/.config/sml/config.json`，请勿泄露。

### 主菜单仪表盘

- **欢迎栏**：显示当前用户名。
- **统计卡片**：在线用户、节点数、我的隧道、登录状态（数据来自公开统计接口 + 个人隧道列表）。
- **快捷操作**：跳转到各功能页。
- **账户信息表**：用户名、邮箱、注册时间、VIP、流量、状态等。

### 隧道列表

1. 进入后自动拉取隧道列表。
2. 用方向键移动光标选中一行。
3. **查看详情**：进入该隧道的详情与 Systemd 管理页。
4. **启动 / 停止**：调用 API 启用或禁用隧道（`isDisabled`）。
5. **删除**：删除远端隧道记录（请谨慎操作）。
6. **刷新列表**：重新请求 API。

### 创建隧道

左侧为表单，右侧为**节点信息面板**（可滚动）：

| 表单项 | 说明 |
|--------|------|
| 隧道名称 | 必填，便于识别 |
| 隧道类型 | tcp / udp / http / https / stcp / xtcp |
| 选择节点 | 从下拉选择；选中后右侧对应节点卡片高亮 |
| 本地地址 | 默认 `127.0.0.1` |
| 本地端口 | 必填，本机服务端口 |
| 远程端口 | TCP/UDP 可选，留空由服务端分配 |
| 域名 | HTTP/HTTPS 时填写 |

右侧节点卡片通常包含：节点 ID/名称、VIP/过载标记、支持协议、带宽、简介、负载进度条。切换「选择节点」时会高亮并滚动到对应卡片。

### 隧道详情与 Systemd

1. 展示该隧道配置键值表。
2. 显示本机 systemd 服务状态：运行中 / 已停止 / 未安装。
3. **安装服务**：将配置写入本机，并创建 `sml-tunnel-{id}.service`。
4. **启动 / 停止 / 重启 / 卸载**：通过 systemctl 管理进程。
5. 非 root 时会提示需要权限；未找到 frpc/mefrpc 时请先 `sml-install` 或在设置中配置路径。

### 每日签到与权益抽取

- **签到**：进入页面后按提示操作，自动处理人机验证。
- **权益抽取**：可查看剩余次数，发起抽奖并查看结果。

### 设置

| 项 | 说明 |
|----|------|
| frpc 路径 | mefrpc/frpc 可执行文件路径；留空则自动探测安装路径或内置路径 |
| 默认节点 ID | 可选，记住常用节点 |
| 用户名 | 本地缓存显示用 |
| 清除 Token | 清除登录态，下次启动回到登录页 |

### 隐式人机验证

密码登录、每日签到和重置访问密钥时，程序会自动获取验证挑战、在本地计算 PoW 解答并提交验证，无需打开浏览器或手工粘贴 Token。

---

## mefrpc 说明

项目内置 ME Frp 客户端二进制 `sml/mefrpc`。

| 方式 | 说明 |
|------|------|
| 自动安装 | 运行 `sml` 时若系统路径尚无 mefrpc，会尝试安装 |
| 手动安装 | `sml-install` |
| 强制重装 | `sml-install --force` |
| 卸载 | `sml-install uninstall` |

**默认安装位置：**

- Linux：`/usr/local/bin/mefrpc`
- Windows（开发环境）：`%LOCALAPPDATA%\SML\bin\mefrpc`

路径优先级：设置里手动配置 → 已安装路径 → 包内内置路径 → 默认 `frpc` 路径。

---

## Systemd 服务管理

SML 支持将隧道注册为 systemd 服务，实现进程守护和开机自启。

### 前提

- Linux 系统（支持 systemd）
- root 权限（或 sudo）
- 已安装 frpc / mefrpc（见上一节）

### 操作

在程序 **隧道详情** 页面中，通过按钮可以：

| 操作 | 说明 |
|------|------|
| 安装服务 | 写入隧道配置并创建 systemd unit 文件 |
| 启动 | `systemctl start sml-tunnel-{id}` |
| 停止 | `systemctl stop sml-tunnel-{id}` |
| 重启 | `systemctl restart sml-tunnel-{id}` |
| 卸载服务 | 停止并删除 systemd unit 文件 |

### 手动管理

```bash
# 查看所有 SML 隧道服务
systemctl list-units --type=service | grep sml-tunnel

# 查看单个隧道状态
systemctl status sml-tunnel-10086

# 查看隧道日志
journalctl -u sml-tunnel-10086 -f
```

隧道配置文件默认目录：`/etc/sml/tunnels/`（如 `tunnel-{id}.toml`）。

---

## 配置说明

配置文件位于 `~/.config/sml/config.json`：

```json
{
  "token": "your_api_token",
  "username": "your_username",
  "frpc_path": "/usr/local/bin/mefrpc",
  "last_node_id": 1,
  "use_sudo": true
}
```

| 字段 | 含义 |
|------|------|
| `token` | API 访问令牌（登录后自动写入） |
| `username` | 用户名缓存 |
| `frpc_path` | frpc/mefrpc 可执行文件路径 |
| `last_node_id` | 最近使用的节点 ID |
| `use_sudo` | 调用 systemctl 时是否使用 sudo（默认 true） |

---

## 快捷键

| 快捷键 | 行为 |
|--------|------|
| `Ctrl+Q` | 弹出退出确认菜单 |
| `Ctrl+R` | 刷新当前页（若该页支持 `refresh_data`） |
| `Ctrl+V` | 向当前输入框粘贴；SSH 无剪贴板时进入手动粘贴页 |
| `Esc` | 返回上一屏 |
| 保持隧道退出 | 所有隧道继续运行，仅关闭 UI |
| 关闭隧道退出 | 停止所有 systemd 隧道服务后退出 |

---

## 项目结构详解

```text
Immortal-TUI-MEFrp-Launcher/
├── README.md                 # 本说明文档
├── docs.md                   # 补充文档（若有）
├── pyproject.toml            # 现代打包元数据、依赖、入口脚本、package-data
├── setup.py                  # 兼容 setuptools 的安装脚本（含 mefrpc 打包）
├── requirements.txt          # 运行时依赖列表（供 pip install -r 使用）
├── .gitignore                # Git 忽略规则
├── tests/                    # 单元/接口相关测试
│   ├── test_api_captcha.py   # API 与验证码相关测试
│   └── test_captcha.py       # 本地 PoW/验证码逻辑测试
└── sml/                      # 主 Python 包（安装后 import sml）
    ├── __init__.py           # 包初始化与版本号
    ├── __main__.py           # 入口：自动安装 mefrpc + 启动 TUI；sml-install CLI
    ├── app.py                # Textual 应用：全局 CSS、屏幕注册、快捷键
    ├── installer.py          # 内置 mefrpc 的安装/卸载/路径探测
    ├── mefrpc                # 内置 ME Frp 客户端二进制（随包分发）
    ├── api/                  # 与 ME Frp 云端 API 通信
    │   ├── __init__.py
    │   └── client.py         # MEFrpAPI：登录、隧道、节点、签到、抽奖等
    ├── manager/              # 本机状态与进程管理
    │   ├── __init__.py
    │   ├── config.py         # 读写 ~/.config/sml/config.json
    │   └── systemd.py        # 写隧道配置、systemctl 启停、check_frpc
    ├── ui/                   # 各功能屏幕（Textual Screen）
    │   ├── __init__.py
    │   ├── login_screen.py          # 登录
    │   ├── main_screen.py           # 主菜单仪表盘 + 退出确认
    │   ├── tunnel_list_screen.py    # 隧道列表与批量操作按钮
    │   ├── tunnel_create_screen.py  # 创建隧道表单 + 右侧节点卡片
    │   ├── tunnel_detail_screen.py  # 隧道详情 + Systemd 管理
    │   ├── signin_screen.py         # 每日签到
    │   ├── lottery_screen.py        # 权益抽取
    │   ├── settings_screen.py       # 设置
    │   └── paste_screen.py          # SSH 环境下手动粘贴
    └── utils/                # 通用工具
        ├── __init__.py
        ├── captcha.py        # 隐式验证码 / PoW 求解
        ├── clipboard.py      # 剪贴板与 SSH 环境检测
        └── helpers.py        # 格式化、root 检测、which 等
```

### 根目录文件

| 路径 | 作用 |
|------|------|
| `README.md` | 安装、使用与结构说明 |
| `docs.md` | 额外文档（设计/接口等，以仓库内容为准） |
| `pyproject.toml` | 定义包名 `sml`、依赖、`sml`/`sml-install` 入口，以及将 `mefrpc` 打入 package-data |
| `setup.py` | 传统安装入口；`package_data` 包含 `sml/mefrpc` |
| `requirements.txt` | 列出 `textual`、`requests`、`pyyaml`，便于 `pip install -r` |
| `.gitignore` | 忽略虚拟环境、缓存、构建产物等 |

### 包 `sml/` 核心模块

| 路径 | 作用 |
|------|------|
| `__main__.py` | `python -m sml` / 命令 `sml` 的入口；启动前静默尝试安装 mefrpc；`sml-install` 对应 `install_cli` |
| `app.py` | `SMLApp`：注册各 Screen、全局主题 CSS、Ctrl 快捷键、粘贴与返回逻辑 |
| `installer.py` | 将内置 `mefrpc` 复制到系统路径、赋权、卸载；`get_install_path()` 供配置探测 |
| `mefrpc` | 随包分发的客户端二进制，安装后供 systemd 服务 `ExecStart` 使用 |

### `sml/api/`

| 路径 | 作用 |
|------|------|
| `client.py` | 统一 `BASE_URL` 请求封装；`login`、`get_proxy_list`、`create_proxy`、`get_create_proxy_data`、签到/抽奖/节点/系统接口等 |

### `sml/manager/`

| 路径 | 作用 |
|------|------|
| `config.py` | Token、用户名、`frpc_path`（含自动探测）、`last_node_id`、`use_sudo` 的读写 |
| `systemd.py` | 隧道 toml 路径、`install/start/stop/restart/remove` 服务、`get_tunnel_status`、`stop_all_tunnels`、`check_frpc` |

### `sml/ui/`

| 路径 | 作用 |
|------|------|
| `login_screen.py` | 登录表单与验证流程 |
| `main_screen.py` | 仪表盘布局、统计卡片、菜单按钮、用户信息表；含 `QuitConfirmScreen` |
| `tunnel_list_screen.py` | DataTable 展示隧道；刷新/新建/详情/启停/删除 |
| `tunnel_create_screen.py` | 左表单右节点列表；按地区分组卡片、负载条、选择联动高亮 |
| `tunnel_detail_screen.py` | 配置表 + 服务状态 + Systemd 按钮 |
| `signin_screen.py` / `lottery_screen.py` | 签到与抽奖 UI |
| `settings_screen.py` | 路径与 Token 等本地设置 |
| `paste_screen.py` | 无法使用系统剪贴板时的手动粘贴界面 |

### `sml/utils/`

| 路径 | 作用 |
|------|------|
| `captcha.py` | 获取挑战、本地计算并提交隐式验证 |
| `clipboard.py` | 读取剪贴板、判断 SSH 环境、粘贴到 Input |
| `helpers.py` | 字节/时间格式化、`check_root`、`check_command` 等 |

### `tests/`

| 路径 | 作用 |
|------|------|
| `test_captcha.py` | 验证码/PoW 相关单测 |
| `test_api_captcha.py` | 与 API 验证流程相关的测试 |

### 数据流简图

```text
用户操作 (ui/*)
    → MEFrpAPI (api/client.py)  ↔  https://api.mefrp.com
    → Config (manager/config.py)  ↔  ~/.config/sml/config.json
    → systemd.py + mefrpc         ↔  systemctl / 本地隧道配置
```

---

## API 参考

所有 API 调用均通过 `sml/api/client.py` 中的 `MEFrpAPI` 类封装，覆盖 ME Frp 公开接口，主要包括：

| 类别 | 示例能力 |
|------|----------|
| 公共信息 | 统计、商城商品 |
| 用户认证 | 密码登录、找回密码、Token |
| 隧道管理 | 列表、创建、删除、启用/禁用、下线、配置导出 |
| 账户管理 | 用户信息、签到、抽奖、改密、操作日志 |
| 节点信息 | 列表、状态、节点 Token |
| 系统信息 | 系统状态、公告 |

响应统一解析 `code == 200` 后返回 `data` 字段；失败抛出 `APIError`。

---

## 依赖

- Python >= 3.8
- [Textual](https://textual.textualize.io/) >= 1.0.0 — TUI 框架
- [Requests](https://requests.readthedocs.io/) >= 2.25.0 — HTTP 客户端
- [PyYAML](https://pyyaml.org/) >= 5.1 — YAML 配置解析

安装方式见 [快速开始](#3-安装依赖使用-requirementstxt)。

---

## 常见问题

**Q: 提示找不到 frpc / mefrpc？**  
A: 先激活虚拟环境，执行 `sml-install`，或在 **设置** 中填写正确的可执行文件路径。

**Q: Systemd 按钮无效？**  
A: 需要 Linux + systemd，并以 root 运行，或配置好 sudo；先在隧道详情中「安装服务」。

**Q: SSH 里 Ctrl+V 粘贴不了？**  
A: 程序会打开手动粘贴页，在输入框中粘贴后确认即可。

**Q: 每次打开终端都要重新装依赖吗？**  
A: 不需要。只要再次 `cd` 到项目目录并 `source venv/bin/activate` 后执行 `sml` 即可。

**Q: 统计卡片只有数字没有标签？**  
A: 请使用最新代码中的 `main_screen` 样式；标签颜色与 Grid 列宽已修复。

---

## 许可证

MIT License
