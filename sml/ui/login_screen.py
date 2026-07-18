"""登录屏幕 - 支持密码登录和 Token 直接登录。"""

from typing import Optional

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from sml.api.client import MEFrpAPI
from sml.utils.captcha import format_captcha_progress
from sml.utils.clipboard import paste_to_input


class LoginScreen(Screen):
    """登录屏幕。"""

    TITLE = "登录 - SML"

    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-box {
        width: 60;
        height: auto;
        padding: 2 3;
        background: #1f2335;
        border: solid #3b4261;
    }

    #login-box > Static, #login-box > Input {
        margin-bottom: 1;
    }

    #login-box > Horizontal {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    #login-box > Horizontal > Input {
        width: 1fr;
        margin-right: 1;
    }

    #title-label {
        text-style: bold;
        color: #7dcfff;
        content-align: center middle;
        height: 3;
    }

    #token-hint {
        color: #565f89;
        text-style: italic;
        height: 2;
    }

    #msg-log {
        height: 3;
        color: #e67e22;
    }

    .paste-btn {
        min-width: 8;
        height: 3;
        margin: 0 0 1 0;
    }

    .login-btn {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="login-box"):
            yield Static("SML - ME Frp TUI Manager", id="title-label")
            yield Label("用户名 / 邮箱:")
            yield Input(placeholder="输入用户名或邮箱", id="username")
            yield Label("密码:")
            with Horizontal():
                yield Input(placeholder="输入密码", password=True, id="password")
                yield Button("粘贴", id="btn-paste-password", classes="paste-btn")
            yield Label("Bearer Token:")
            with Horizontal():
                yield Input(
                    placeholder="输入已有访问 Token",
                    password=True,
                    id="access-token",
                )
                yield Button("粘贴", id="btn-paste-token", classes="paste-btn")
            yield Static("密码登录将自动完成人机验证", id="token-hint")
            yield Static("", id="msg-log")
            with Horizontal():
                yield Button("密码登录", id="btn-login", variant="primary", classes="login-btn")
                yield Button("Token登录", id="btn-token", classes="login-btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn-login":
            self._start_password_login()
        elif btn_id == "btn-token":
            self._start_token_login()
        elif btn_id == "btn-paste-token":
            self._paste_into("access-token")
        elif btn_id == "btn-paste-password":
            self._paste_into("password")

    def _paste_into(self, input_id: str):
        widget = self.query_one(f"#{input_id}")
        if isinstance(widget, Input):
            if paste_to_input(widget):
                self._set_msg("已粘贴", error=False)
            else:
                self._manual_paste_fallback(widget)

    def _manual_paste_fallback(self, target_input: Input):
        def handle_paste(result: Optional[str]):
            if result:
                cursor_pos = target_input.cursor_position
                old_value = target_input.value
                target_input.value = old_value[:cursor_pos] + result + old_value[cursor_pos:]
                target_input.cursor_position = cursor_pos + len(result)
                self._set_msg("已粘贴", error=False)

        self.app.push_screen("manual_paste", handle_paste)

    def _get_input(self, id_: str) -> str:
        widget = self.query_one(f"#{id_}")
        return widget.value.strip() if isinstance(widget, Input) else ""

    def _set_msg(self, msg: str, error: bool = True):
        widget = self.query_one("#msg-log")
        if isinstance(widget, Static):
            widget.update(f"{'⚠' if error else '✓'} {msg}")
            widget.styles.color = "#e74c3c" if error else "#27ae60"

    def _set_busy(self, busy: bool, active: str = ""):
        login_button = self.query_one("#btn-login", Button)
        token_button = self.query_one("#btn-token", Button)
        login_button.disabled = busy
        token_button.disabled = busy
        login_button.label = "验证并登录中..." if busy and active == "password" else "密码登录"
        token_button.label = "验证中..." if busy and active == "token" else "Token登录"

    def _start_password_login(self):
        username = self._get_input("username")
        password = self._get_input("password")
        if not username or not password:
            self._set_msg("请填写用户名和密码")
            return
        self._set_busy(True, "password")
        self._set_msg("正在准备隐式验证...", error=False)
        self._password_login_worker(username, password)

    def _show_captcha_progress(self, progress: int, operation: str):
        self._set_msg(format_captcha_progress(progress, operation), error=False)

    @work(thread=True, exclusive=True)
    def _password_login_worker(self, username: str, password: str):
        try:
            token = self.api.login(
                username,
                password,
                on_captcha_progress=lambda progress: self.app.call_from_thread(
                    self._show_captcha_progress, progress, "登录"
                ),
            )
            self.app.call_from_thread(self._finish_password_login, token)
        except Exception as exc:
            self.app.call_from_thread(self._set_msg, f"登录失败: {exc}")
        finally:
            self.app.call_from_thread(self._set_busy, False)

    def _finish_password_login(self, token: str):
        if token:
            self._set_msg("登录成功！", error=False)
            self.app.push_screen("main")
        else:
            self._set_msg("登录成功，但未获取到 Token，请使用 Token 登录")

    def _start_token_login(self):
        token = self._get_input("access-token")
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        if not token:
            self._set_msg("请输入 Bearer Token")
            return
        self._set_busy(True, "token")
        self._set_msg("正在验证 Token...", error=False)
        self._token_login_worker(token)

    @work(thread=True, exclusive=True)
    def _token_login_worker(self, token: str):
        previous_token = self.api.cfg.token
        try:
            self.api.cfg.token = token
            info = self.api.get_user_info()
            if info:
                username = info.get("username", info.get("email", "用户"))
                self.api.cfg.username = username
                self.app.call_from_thread(self._finish_token_login, username)
            else:
                self.api.cfg.token = previous_token
                self.app.call_from_thread(self._set_msg, "Token 无效或已过期")
        except Exception as exc:
            self.api.cfg.token = previous_token
            self.app.call_from_thread(self._set_msg, f"Token 验证失败: {exc}")
        finally:
            self.app.call_from_thread(self._set_busy, False)

    def _finish_token_login(self, username: str):
        self._set_msg(f"Token 验证成功！欢迎 {username}", error=False)
        self.app.push_screen("main")

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "password":
            self._start_password_login()
        elif event.input.id == "access-token":
            self._start_token_login()
