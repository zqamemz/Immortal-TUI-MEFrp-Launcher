"""主仪表盘屏幕 - 用户信息和导航."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, DataTable, Label
from textual import work
from textual.reactive import reactive
from textual.message import Message

from sml.api.client import MEFrpAPI, APIError
from sml.manager.config import Config


class MainScreen(Screen):
    """主仪表盘 - 登录后首页。"""

    TITLE = "主菜单 - SML"

    CSS = """
    MainScreen {
        align: center top;
    }

    #welcome-bar {
        height: 3;
        background: #1f2335;
        padding: 0 2;
        content-align: center middle;
        border: solid #3b4261;
        margin: 1 2;
    }

    #stat-grid {
        grid-size: 4;
        grid-columns: 1fr;
        margin: 0 2;
        height: 5;
    }

    .stat-card {
        background: #24283b;
        border: solid #3b4261;
        padding: 0 1;
        content-align: center middle;
        height: 5;
    }

    .stat-value {
        color: #7dcfff;
        text-style: bold;
        text-align: center;
    }

    .stat-label {
        color: #565f89;
        text-align: center;
    }

    #menu-grid {
        grid-size: 3;
        grid-columns: 1fr 1fr 1fr;
        grid-rows: auto;
        margin: 1 2;
    }

    .menu-btn {
        min-width: 20;
        height: 5;
        margin: 0 1;
    }

    #info-panel {
        margin: 1 2;
        border: solid #3b4261;
        background: #1f2335;
        height: auto;
        padding: 0 1;
    }

    #user-info-table {
        height: auto;
        border: none;
    }

    #action-area {
        margin: 0 2;
    }

    .section-title {
        color: #ff9e64;
        text-style: bold;
        height: 3;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()
        self.cfg = Config()
        self.user_info: dict = {}
        self.stats: dict = {}
        self.tunnel_count = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("正在加载...", id="welcome-bar")
        yield Grid(id="stat-grid")
        yield Static("快捷操作", classes="section-title")
        yield Grid(id="menu-grid")
        yield Static("账户信息", classes="section-title")
        yield Vertical(id="info-panel")
        yield Footer()

    def on_mount(self):
        self.refresh_data()

    @work(exclusive=True)
    async def refresh_data(self):
        """加载用户信息和统计数据。"""
        try:
            # 加载用户信息
            try:
                self.user_info = self.api.get_user_info()
            except Exception as e:
                self.user_info = {"username": self.cfg.username or "未知"}
                self._set_welcome(f"用户信息加载失败: {e}")

            username = self.user_info.get("username") or self.cfg.username or "用户"
            self._set_welcome(f"欢迎回来, {username} ！")

            # 加载隧道列表获取计数
            try:
                proxy_data = self.api.get_proxy_list()
                proxies = proxy_data if isinstance(proxy_data, list) else proxy_data.get("proxies", proxy_data.get("data", []))
                self.tunnel_count = len(proxies) if isinstance(proxies, list) else 0
            except Exception:
                self.tunnel_count = 0

            # 加载系统统计
            try:
                self.stats = self.api.get_statistics()
            except Exception:
                self.stats = {}

            self._update_stats()
            self._build_menu()
            self._build_user_info()

        except Exception as e:
            self._set_welcome(f"数据加载出错: {e}")

    def _set_welcome(self, text: str):
        w = self.query_one("#welcome-bar")
        if isinstance(w, Static):
            w.update(text)

    def _update_stats(self):
        grid = self.query_one("#stat-grid")
        if not isinstance(grid, Grid):
            return

        users = self.stats.get("users", self.stats.get("userCount", "?"))
        nodes = self.stats.get("nodes", self.stats.get("nodeCount", "?"))
        proxies = self.stats.get("proxies", self.stats.get("proxyCount", self.tunnel_count))

        grid.remove_children()
        for label, value in [
            ("在线用户", str(users)),
            ("节点数", str(nodes)),
            ("我的隧道", str(proxies)),
            ("状态", "已登录"),
        ]:
            grid.mount(
                Vertical(
                    Static(value, classes="stat-value"),
                    Static(label, classes="stat-label"),
                    classes="stat-card",
                )
            )

    def _build_menu(self):
        grid = self.query_one("#menu-grid")
        if not isinstance(grid, Grid):
            return

        grid.remove_children()
        menus = [
            ("🔌 隧道列表", "tunnel_list", "primary"),
            ("➕ 新建隧道", "tunnel_create", "success"),
            ("📅 每日签到", "signin", "warning"),
            ("🎁 权益抽取", "lottery", "warning"),
            ("⚙️ 设置", "settings", "default"),
            ("🚪 退出", "quit_confirm", "error"),
        ]
        for label, screen, variant in menus:
            btn = Button(label, id=f"nav-{screen}", variant=variant, classes="menu-btn")
            grid.mount(btn)

    def _build_user_info(self):
        panel = self.query_one("#info-panel")
        if not isinstance(panel, Vertical):
            return

        panel.remove_children()
        rows = [
            ("用户名", self.user_info.get("username", "未知")),
            ("邮箱", self.user_info.get("email", "未知")),
            ("注册时间", str(self.user_info.get("registerTime", self.user_info.get("createdAt", "未知")))),
            ("VIP 等级", str(self.user_info.get("level", self.user_info.get("vip", "普通")))),
            ("流量", str(self.user_info.get("traffic", self.user_info.get("flow", "未知")))),
            ("状态", self.user_info.get("status", "正常")),
        ]

        table = DataTable(id="user-info-table")
        table.add_columns("项目", "内容")
        table.add_rows(rows)
        panel.mount(table)

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id or ""
        if btn_id.startswith("nav-"):
            target = btn_id[4:]
            self.app.push_screen(target)


class QuitConfirmScreen(Screen):
    """退出确认屏幕 - 两种退出模式。"""

    TITLE = "退出确认"

    CSS = """
    QuitConfirmScreen {
        align: center middle;
    }

    #quit-box {
        width: 50;
        height: auto;
        padding: 2 3;
        background: #1f2335;
        border: solid #3b4261;
    }

    #quit-box > Static {
        margin-bottom: 1;
    }

    #quit-box > Horizontal {
        height: auto;
        align: center middle;
    }

    #quit-box > Horizontal > Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="quit-box"):
            yield Static("退出程序", classes="title")
            yield Static("请选择退出模式：")
            with Horizontal():
                yield Button("保持隧道并退出", id="quit-keep", variant="primary")
                yield Button("关闭隧道并退出", id="quit-stop", variant="error")
                yield Button("取消", id="quit-cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "quit-keep":
            self.app.exit()
        elif btn_id == "quit-stop":
            self.stop_all_and_exit()
        elif btn_id == "quit-cancel":
            self.app.pop_screen()

    @work(exclusive=True)
    async def stop_all_and_exit(self):
        from sml.manager.systemd import stop_all_tunnels
        btn = self.query_one("#quit-stop")
        if isinstance(btn, Button):
            btn.disabled = True
            btn.label = "关闭中..."
        try:
            stop_all_tunnels()
        except Exception as e:
            pass
        self.app.exit()
