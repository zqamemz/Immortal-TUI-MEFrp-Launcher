"""SML 主 TUI 应用程序."""

from textual.app import App
from textual.binding import Binding
from textual.screen import Screen

from sml.manager.config import Config
from sml.ui.login_screen import LoginScreen
from sml.ui.main_screen import MainScreen, QuitConfirmScreen
from sml.ui.tunnel_list_screen import TunnelListScreen
from sml.ui.tunnel_create_screen import TunnelCreateScreen
from sml.ui.tunnel_detail_screen import TunnelDetailScreen
from sml.ui.signin_screen import SignInScreen
from sml.ui.lottery_screen import LotteryScreen
from sml.ui.settings_screen import SettingsScreen
from sml.ui.paste_screen import ManualPasteScreen
from sml.utils.clipboard import paste_to_input, get_clipboard_text, is_ssh_environment


class SMLApp(App):
    """SML 主应用程序 - ME Frp 终端图形化管理工具。"""

    TITLE = "SML - ME Frp Manager"
    SUB_TITLE = "v1.0.0"

    CSS = """
    Screen {
        background: #1a1b26;
    }

    /* 通用按钮样式 */
    Button {
        background: #2d3a4f;
        color: #c0d0e0;
        border: none;
        padding: 0 2;
        min-width: 16;
        height: 3;
    }
    Button:hover {
        background: #3d5a7f;
    }
    Button:focus {
        background: #4a6a9f;
    }

    Button.primary {
        background: #2680eb;
        color: #ffffff;
    }
    Button.primary:hover {
        background: #3a9aff;
    }

    Button.success {
        background: #27ae60;
        color: #ffffff;
    }
    Button.success:hover {
        background: #2ecc71;
    }

    Button.warning {
        background: #e67e22;
        color: #ffffff;
    }
    Button.warning:hover {
        background: #f39c12;
    }

    Button.error {
        background: #c0392b;
        color: #ffffff;
    }
    Button.error:hover {
        background: #e74c3c;
    }

    /* Input 样式 */
    Input {
        background: #24283b;
        color: #c0d0e0;
        border: tall #3b4261;
        padding: 0 2;
    }
    Input:focus {
        border: tall #2680eb;
    }

    /* Header / Footer */
    Header {
        background: #1f2335;
        color: #a9b1d6;
    }
    Footer {
        background: #1f2335;
        color: #565f89;
    }

    /* 静态文本 */
    Static {
        color: #c0d0e0;
    }

    /* DataTable */
    DataTable {
        background: #1a1b26;
        color: #c0d0e0;
        border: solid #3b4261;
    }
    DataTable > .datatable--header {
        background: #24283b;
        color: #7dcfff;
    }
    DataTable > .datatable--cursor {
        background: #2d3a4f;
    }

    /* 选项卡 */
    TabbedContent {
        border: solid #3b4261;
    }
    TabbedContent > .tabbed-content--tab-bar {
        background: #1f2335;
    }
    TabbedContent > .tabbed-content--tab {
        background: #24283b;
        color: #565f89;
    }
    TabbedContent > .tabbed-content--tab-active {
        background: #2680eb;
        color: #ffffff;
    }

    /* 列表视图 */
    ListView {
        background: #1a1b26;
        border: solid #3b4261;
    }
    ListView > .list-view--item {
        background: #24283b;
        color: #c0d0e0;
        padding: 1 2;
    }
    ListView > .list-view--item:hover {
        background: #2d3a4f;
    }
    ListView > .list-view--item-highlighted {
        background: #3d5a7f;
    }

    /* 分组框 */
    StaticGroup {
        border: solid #3b4261;
        background: #1f2335;
        padding: 1 2;
    }

    /* 网格容器 */
    Grid {
        grid-gutter: 1 2;
    }

    /* 消息 */
    Toast {
        background: #24283b;
        color: #c0d0e0;
        padding: 1 3;
    }

    .hidden {
        display: none;
    }

    .label {
        color: #565f89;
    }

    .value {
        color: #7dcfff;
    }

    .title {
        color: #ff9e64;
        text-style: bold;
    }

    .status-online {
        color: #27ae60;
    }

    .status-offline {
        color: #e74c3c;
    }

    .status-warning {
        color: #e67e22;
    }
    """

    SCREENS = {
        "login": LoginScreen,
        "main": MainScreen,
        "quit_confirm": QuitConfirmScreen,
        "tunnel_list": TunnelListScreen,
        "tunnel_create": TunnelCreateScreen,
        "tunnel_detail": TunnelDetailScreen,
        "signin": SignInScreen,
        "lottery": LotteryScreen,
        "settings": SettingsScreen,
        "manual_paste": ManualPasteScreen,
    }

    BINDINGS = [
        Binding("ctrl+q", "quit_app", "退出", priority=True),
        Binding("ctrl+r", "refresh", "刷新", priority=False),
        Binding("ctrl+v", "paste_clipboard", "粘贴", priority=False),
        Binding("escape", "back", "返回", priority=False),
    ]

    def __init__(self):
        super().__init__()
        self.cfg = Config()
        self.current_tunnel_id: int = 0  # 用于隧道详情页传递

    def on_mount(self):
        """应用启动时判断是否已有 token，决定进入哪个页面。"""
        if self.cfg.has_token:
            self.push_screen("main")
        else:
            self.push_screen("login")

    def action_quit_app(self):
        """退出应用时关闭所有隧道或保持运行。"""
        self.push_screen("quit_confirm")

    def action_refresh(self):
        """刷新当前屏幕。"""
        screen = self.screen
        if hasattr(screen, "refresh_data"):
            screen.refresh_data()

    def action_back(self):
        """返回上一个屏幕。"""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_paste_clipboard(self):
        """全局粘贴：将剪贴板内容粘贴到当前聚焦的 Input 组件。

        在 SSH 等无系统剪贴板的环境下，自动回退到手动粘贴屏幕。
        """
        focused = self.focused
        if focused is not None and hasattr(focused, "value") and hasattr(focused, "cursor_position"):
            # 先尝试系统剪贴板
            if paste_to_input(focused):
                self.notify("已粘贴", severity="information", timeout=2)
            else:
                # 系统剪贴板不可用（SSH 环境），回退到手动粘贴
                self._do_manual_paste(focused)

    def _do_manual_paste(self, target_input):
        """打开手动粘贴屏幕，将用户粘贴的内容插入到目标 Input。"""
        input_id = getattr(target_input, "id", "") or ""

        def handle_paste(result: str | None):
            if result:
                # 将结果插入到目标 Input 组件
                cursor_pos = target_input.cursor_position
                old_value = target_input.value
                new_value = old_value[:cursor_pos] + result + old_value[cursor_pos:]
                target_input.value = new_value
                target_input.cursor_position = cursor_pos + len(result)
                self.notify("已粘贴", severity="information", timeout=2)

        self.push_screen("manual_paste", handle_paste)
