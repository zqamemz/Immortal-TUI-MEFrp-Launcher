"""设置屏幕."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Header, Footer, Static, Checkbox
from textual import work

from sml.manager.config import Config
from sml.manager.systemd import check_frpc
from sml.utils.helpers import check_root


class SettingsScreen(Screen):
    """应用设置屏幕。"""

    TITLE = "设置 - SML"

    CSS = """
    SettingsScreen {
        align: center top;
    }

    #settings-box {
        width: 55;
        height: auto;
        padding: 2 3;
        background: #1f2335;
        border: solid #3b4261;
        margin: 1 0;
    }

    #settings-box > Static {
        margin-bottom: 1;
    }

    #settings-box > Input, #settings-box > Label {
        margin-bottom: 1;
    }

    #settings-actions {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    #settings-actions > Button {
        margin: 0 1;
    }

    #settings-msg {
        height: 3;
    }
    """

    def __init__(self):
        super().__init__()
        self.cfg = Config()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings-box"):
            yield Static("应用设置", classes="title")
            yield Label("frpc 路径:")
            yield Input(placeholder="自动检测或手动设置路径", id="frpc-path")
            yield Label("默认节点 ID:")
            yield Input(placeholder="留空自动选择", id="node-id")
            yield Label("用户名:")
            yield Input(placeholder="当前登录用户名", id="s-username")
            if check_root():
                yield Static("✓ 当前为 root 用户，systemd 管理可用", classes="status-online")
            else:
                yield Static("⚠ 非 root 用户，systemd 功能需 sudo", classes="status-warning")
            yield Static("", id="settings-msg")
            with Horizontal(id="settings-actions"):
                yield Button("保存设置", id="btn-save", variant="primary")
                yield Button("清除 Token", id="btn-clear", variant="error")
                yield Button("返回", id="btn-back")
        yield Footer()

    def on_mount(self):
        settings = self.cfg.get_all()
        self._set_input("frpc-path", settings.get("frpc_path", ""))
        self._set_input("node-id", str(settings.get("last_node_id", "")))
        self._set_input("s-username", settings.get("username", ""))

        # 检测 frpc
        frpc_ok, frpc_msg = check_frpc()
        msg = self.query_one("#settings-msg")
        if isinstance(msg, Static):
            if frpc_ok:
                msg.update(f"✓ {frpc_msg}")
                msg.styles.color = "#27ae60"
            else:
                msg.update("⚠ 未检测到 frpc，请设置正确路径")
                msg.styles.color = "#e67e22"

    def _set_input(self, id_: str, value: str):
        w = self.query_one(f"#{id_}")
        if isinstance(w, Input):
            w.value = value

    def _get(self, id_: str) -> str:
        w = self.query_one(f"#{id_}")
        if isinstance(w, Input):
            return w.value.strip()
        return ""

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn-save":
            self.save_settings()
        elif btn_id == "btn-clear":
            self.clear_token()
        elif btn_id == "btn-back":
            self.app.pop_screen()

    def save_settings(self):
        self.cfg.frpc_path = self._get("frpc-path")
        node_id = self._get("node-id")
        if node_id.isdigit():
            self.cfg.last_node_id = int(node_id)
        self.cfg.username = self._get("s-username")
        msg = self.query_one("#settings-msg")
        if isinstance(msg, Static):
            msg.update("✓ 设置已保存")
            msg.styles.color = "#27ae60"

    def clear_token(self):
        self.cfg.token = ""
        msg = self.query_one("#settings-msg")
        if isinstance(msg, Static):
            msg.update("Token 已清除，下次启动将回到登录页")
            msg.styles.color = "#e67e22"
