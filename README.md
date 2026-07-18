# SML - ME Frp TUI Manager

在 SSH 和真实命令行环境下使用的 **ME Frp** 图形化终端管理程序。

> 基于 [Textual](https://textual.textualize.io/) 框架构建，无需 WebUI，直接在终端中运行。

## 功能

- 🔐 **登录** — 密码登录、Token 登录，自动完成人机验证
- 📊 **仪表盘** — 实时显示统计信息、用户信息、快捷入口
- 🔌 **隧道管理** — 隧道列表、创建、启用/禁用、删除
- ⚙️ **Systemd 守护** — 将隧道安装为 systemd 服务，实现开机自启/进程守护
- 📅 **每日签到** — 支持人机验证
- 🎁 **权益抽取** — 抽奖功能，查看剩余次数
- 🚪 **智能退出** — 保持隧道退出 / 关闭所有隧道退出

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

### 1. 安装

```bash
# 克隆或下载项目
git clone <your-repo-url> /opt/sml
cd /opt/sml

# 安装依赖
pip install textual requests pyyaml

# 安装 SML
pip install -e .
```

或者使用 pip 直接安装：

```bash
pip install sml  # 发布后
```

### 2. 运行

```bash
# 直接启动
sml

# 或者使用 Python 模块
python -m sml
```

### 3. 首次使用

1. 启动程序后，使用已有账号密码或访问 Token **登录**
2. 登录后进入主菜单，可通过 **设置** 配置 frpc 路径
3. 在 **隧道列表** 中查看已有隧道，或 **新建隧道**
4. 进入隧道详情可 **安装 Systemd 服务** 实现进程守护

## 隐式人机验证

密码登录、每日签到和重置访问密钥时，程序会自动获取验证挑战、在本地计算 PoW 解答并提交验证，无需打开浏览器或手工粘贴 Token。

## Systemd 服务管理

SML 支持将隧道注册为 systemd 服务，实现进程守护和开机自启。

### 前提

- Linux 系统（支持 systemd）
- root 权限（或 sudo）
- 已安装 frpc

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

## 配置

配置文件位于 `~/.config/sml/config.json`：

```json
{
  "token": "your_api_token",
  "username": "your_username",
  "frpc_path": "/usr/local/bin/frpc",
  "last_node_id": 1
}
```

## 退出模式

| 快捷键 | 行为 |
|--------|------|
| `Ctrl+Q` | 弹出退出确认菜单 |
| 保持隧道退出 | 所有隧道继续运行，仅关闭 UI |
| 关闭隧道退出 | 停止所有 systemd 隧道服务后退出 |

## 项目结构

```
SML/
├── pyproject.toml        # 项目元数据和依赖
├── setup.py              # 安装配置
├── requirements.txt      # 依赖列表
└── sml/
    ├── __init__.py        # 包版本
    ├── __main__.py        # 入口点
    ├── app.py             # Textual 主应用
    ├── api/
    │   ├── __init__.py
    │   └── client.py      # ME Frp API 完整封装
    ├── manager/
    │   ├── __init__.py
    │   ├── config.py      # 配置管理 (JSON)
    │   └── systemd.py     # Systemd 隧道服务管理
    ├── ui/
    │   ├── __init__.py
    │   ├── login_screen.py       # 登录页
    │   ├── main_screen.py        # 主仪表盘
    │   ├── tunnel_list_screen.py # 隧道列表
    │   ├── tunnel_create_screen.py # 新建隧道
    │   ├── tunnel_detail_screen.py # 隧道详情 + systemd
    │   ├── signin_screen.py      # 每日签到
    │   ├── lottery_screen.py     # 权益抽取
    │   └── settings_screen.py    # 设置
    └── utils/
        ├── __init__.py
        └── helpers.py     # 工具函数
```

## API 参考

所有 API 调用均通过 `sml/api/client.py` 中的 `MEFrpAPI` 类封装，覆盖 ME Frp 5.0 所有公开接口：

- 公共信息 (统计、商城)
- 用户认证（密码登录、Token 登录、找回密码）
- 隧道管理 (CRUD、启用/禁用、配置导出)
- 账户管理 (信息、签到、抽奖、修改密码)
- 节点信息 (列表、状态、Token)
- 系统信息 (状态、公告)

## 依赖

- Python >= 3.8
- [Textual](https://textual.textualize.io/) >= 1.0.0 — TUI 框架
- [Requests](https://requests.readthedocs.io/) >= 2.25.0 — HTTP 客户端
- [PyYAML](https://pyyaml.org/) >= 5.1 — YAML 配置解析

## 许可证

MIT License
