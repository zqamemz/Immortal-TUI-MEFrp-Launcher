"""权益抽取（抽奖）屏幕."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Grid
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, Label
from textual import work

from sml.api.client import MEFrpAPI, APIError
from sml.utils.helpers import format_timestamp


class LotteryScreen(Screen):
    """抽奖屏幕 - 查看剩余次数并抽取权益。"""

    TITLE = "权益抽取 - SML"

    CSS = """
    LotteryScreen {
        align: center middle;
    }

    #lottery-box {
        width: 50;
        height: auto;
        padding: 2 3;
        background: #1f2335;
        border: solid #3b4261;
    }

    #lottery-box > Static {
        margin-bottom: 1;
    }

    #lottery-stats {
        height: auto;
        margin-bottom: 1;
    }

    .lottery-stat {
        height: 3;
        padding: 0 1;
    }

    .lottery-stat > .value {
        color: #7dcfff;
    }

    #lottery-actions {
        height: auto;
        align: center middle;
        margin: 1 0;
    }

    #lottery-msg {
        height: 3;
    }

    #lottery-result {
        height: auto;
        border: solid #27ae60;
        padding: 1 2;
        margin-top: 1;
        background: #1a2b1f;
    }

    #lottery-result > Static {
        color: #27ae60;
        text-align: center;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="lottery-box"):
            yield Static("权益抽取 (抽奖)", classes="title")
            yield Grid(id="lottery-stats")
            yield Static("", id="lottery-msg")
            with Horizontal(id="lottery-actions"):
                yield Button("🎰 抽取一次", id="btn-draw", variant="primary")
                yield Button("返回", id="btn-back")
            yield Static("", id="lottery-result")
        yield Footer()

    def on_mount(self):
        self.refresh_data()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-draw":
            self.do_draw()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    @work(exclusive=True)
    async def refresh_data(self):
        try:
            remaining = self.api.get_lottery_remaining()
            grid = self.query_one("#lottery-stats")
            if isinstance(grid, Grid):
                grid.remove_children()

                if isinstance(remaining, dict):
                    count = remaining.get("remaining", remaining.get("count", remaining.get("total", 0)))
                    last_draw = remaining.get("lastDrawTime", remaining.get("lastTime", 0))
                else:
                    count = remaining
                    last_draw = 0

                grid.mount(
                    Vertical(
                        Static("剩余次数", classes="label"),
                        Static(str(count), classes="value"),
                        classes="lottery-stat",
                    ),
                    Vertical(
                        Static("上次抽取", classes="label"),
                        Static(
                            format_timestamp(last_draw)
                            if isinstance(last_draw, int)
                            else str(last_draw),
                            classes="value",
                        ),
                        classes="lottery-stat",
                    ),
                )

        except Exception as e:
            self._msg(f"加载信息失败: {e}")

    @work(exclusive=True)
    async def do_draw(self):
        btn = self.query_one("#btn-draw")
        if isinstance(btn, Button):
            btn.disabled = True
            btn.label = "抽取中..."

        try:
            result = self.api.lottery_draw()
            result_w = self.query_one("#lottery-result")
            if isinstance(result_w, Static):
                if isinstance(result, dict):
                    prize = result.get("prize", result.get("name", result.get("reward", "")))
                    level = result.get("level", result.get("vip", "普通"))
                    lines = [
                        f"🎉 恭喜获得: {prize}",
                        f"等级: {level}",
                    ]
                    result_w.update("\n".join(lines))
                else:
                    result_w.update(f"🎉 结果: {result}")
                result_w.styles.border = "#27ae60"
            self._msg("抽取成功！", error=False)
            self.refresh_data()
        except Exception as e:
            self._msg(f"抽取失败: {e}")
        finally:
            if isinstance(btn, Button):
                btn.disabled = False
                btn.label = "🎰 抽取一次"

    def _msg(self, text: str, error: bool = True):
        w = self.query_one("#lottery-msg")
        if isinstance(w, Static):
            w.update(f"{'⚠' if error else '✓'} {text}")
            w.styles.color = "#e74c3c" if error else "#27ae60"
