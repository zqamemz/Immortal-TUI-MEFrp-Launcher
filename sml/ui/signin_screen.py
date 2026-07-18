"""签到屏幕。"""

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from sml.api.client import MEFrpAPI
from sml.utils.captcha import format_captcha_progress


class SignInScreen(Screen):
    """每日签到屏幕。"""

    TITLE = "每日签到 - SML"

    CSS = """
    SignInScreen {
        align: center middle;
    }

    #signin-box {
        width: 60;
        height: auto;
        padding: 2 3;
        background: #1f2335;
        border: solid #3b4261;
    }

    #signin-box > Static {
        margin-bottom: 1;
    }

    #signin-box > Horizontal {
        height: auto;
        align: center middle;
    }

    #signin-msg {
        height: 3;
    }

    #signin-result {
        height: auto;
        border: solid #3b4261;
        padding: 1 2;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="signin-box"):
            yield Static("每日签到", classes="title")
            yield Static("签到时将自动完成人机验证，无需粘贴 Token。")
            yield Static("", id="signin-msg")
            with Horizontal():
                yield Button("立即签到", id="btn-signin", variant="primary")
                yield Button("返回", id="btn-back")
            yield Static("", id="signin-result")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-signin":
            self._start_signin()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def _start_signin(self):
        signin_button = self.query_one("#btn-signin", Button)
        back_button = self.query_one("#btn-back", Button)
        signin_button.disabled = True
        signin_button.label = "验证并签到中..."
        back_button.disabled = True
        self._msg("正在准备隐式验证...", error=False)
        self._signin_worker()

    def _show_captcha_progress(self, progress: int):
        self._msg(format_captcha_progress(progress, "签到"), error=False)

    @work(thread=True, exclusive=True)
    def _signin_worker(self):
        try:
            result = self.api.sign_in(
                on_captcha_progress=lambda progress: self.app.call_from_thread(
                    self._show_captcha_progress, progress
                )
            )
            self.app.call_from_thread(self._finish_signin, result)
        except Exception as exc:
            self.app.call_from_thread(self._msg, f"签到失败: {exc}")
        finally:
            self.app.call_from_thread(self._restore_button)

    def _finish_signin(self, result):
        self._msg("签到成功！", error=False)
        result_widget = self.query_one("#signin-result", Static)
        result_widget.update(f"签到结果: {result}")

    def _restore_button(self):
        signin_button = self.query_one("#btn-signin", Button)
        signin_button.disabled = False
        signin_button.label = "立即签到"
        self.query_one("#btn-back", Button).disabled = False

    def _msg(self, text: str, error: bool = True):
        widget = self.query_one("#signin-msg", Static)
        widget.update(f"{'⚠' if error else '✓'} {text}")
        widget.styles.color = "#e74c3c" if error else "#27ae60"
