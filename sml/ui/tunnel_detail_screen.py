"""隧道详情屏幕 - 查看配置、启动/停止 systemd 服务等."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, DataTable, Input, Label
from textual import work

from sml.api.client import MEFrpAPI, APIError
from sml.manager.systemd import (
    get_tunnel_status, start_tunnel, stop_tunnel, restart_tunnel,
    install_tunnel_service, remove_tunnel_service, enable_tunnel_service,
    write_tunnel_config, remove_tunnel_config, check_frpc,
)
from sml.utils.helpers import check_root


class TunnelDetailScreen(Screen):
    """隧道详情 - 查看/修改隧道信息，管理 systemd 服务。"""

    TITLE = "隧道详情 - SML"

    CSS = """
    TunnelDetailScreen {
        align: center top;
    }

    #detail-box {
        width: 70;
        height: auto;
        padding: 1 2;
        margin: 1 0;
        background: #1f2335;
        border: solid #3b4261;
    }

    #detail-box > Static {
        margin-bottom: 1;
    }

    #proxy-config {
        height: auto;
        border: none;
    }

    #service-status {
        height: 3;
        padding: 0 1;
    }

    #service-actions {
        height: auto;
        margin: 1 0;
        align: center middle;
    }

    #service-actions > Button {
        margin: 0 1;
    }

    #detail-msg {
        height: 3;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()
        self.proxy_id: int = 0
        self.proxy_data: dict = {}

    def on_mount(self):
        self.proxy_id = self.app.current_tunnel_id
        if self.proxy_id:
            self.refresh_data()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="detail-box"):
            yield Static("隧道详情", classes="title")
            yield DataTable(id="proxy-config")
            yield Static("", id="service-status")
            yield Static("Systemd 服务管理:", classes="label")
            with Horizontal(id="service-actions"):
                yield Button("安装服务", id="svc-install", variant="primary")
                yield Button("启动", id="svc-start", variant="success")
                yield Button("停止", id="svc-stop", variant="warning")
                yield Button("重启", id="svc-restart", variant="default")
                yield Button("卸载服务", id="svc-remove", variant="error")
            yield Static("", id="detail-msg")
            with Horizontal():
                yield Button("返回列表", id="btn-back")
                yield Button("刷新", id="btn-refresh", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn-back":
            self.app.pop_screen()
        elif btn_id == "btn-refresh":
            self.refresh_data()
        elif btn_id == "svc-install":
            self.do_install_service()
        elif btn_id == "svc-start":
            self.do_service_action("start")
        elif btn_id == "svc-stop":
            self.do_service_action("stop")
        elif btn_id == "svc-restart":
            self.do_service_action("restart")
        elif btn_id == "svc-remove":
            self.do_remove_service()

    @work(exclusive=True)
    async def refresh_data(self):
        if not self.proxy_id:
            self._msg("未指定隧道 ID")
            return

        try:
            # 获取隧道信息和配置
            config = self.api.get_proxy_config(self.proxy_id)
            self.proxy_data = config if isinstance(config, dict) else config.get("data", {})

            # 显示配置
            table = self.query_one("#proxy-config")
            if isinstance(table, DataTable):
                table.clear()
                if not table.columns:
                    table.add_columns("配置项", "值")
                
                # 如果 proxy_data 有 config 字段且是字符串（TOML配置文本），分行展示
                if "config" in self.proxy_data and isinstance(self.proxy_data.get("config"), str):
                    config_text = self.proxy_data["config"]
                    for line in config_text.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # 简单分割 key = value
                            if "=" in line:
                                parts = line.split("=", 1)
                                key = parts[0].strip()
                                val = parts[1].strip().strip("'\"")
                                table.add_row(key, val[:60])
                            else:
                                table.add_row("配置", line[:60])
                    # 显示其他元数据（type等）
                    for k, v in self.proxy_data.items():
                        if k != "config":
                            table.add_row(f"[meta] {k}", str(v)[:60])
                else:
                    # 常规 dict 展开
                    for k, v in self.proxy_data.items():
                        table.add_row(str(k), str(v)[:60])

            # 检查 systemctl 状态
            status = get_tunnel_status(self.proxy_id)
            status_w = self.query_one("#service-status")
            if isinstance(status_w, Static):
                if status == "active":
                    status_w.update("● 服务状态: 运行中")
                    status_w.styles.color = "#27ae60"
                elif status == "inactive":
                    status_w.update("○ 服务状态: 已停止")
                    status_w.styles.color = "#e74c3c"
                elif status == "not-found":
                    status_w.update("○ 服务状态: 未安装 systemd 服务")
                    status_w.styles.color = "#565f89"
                else:
                    status_w.update(f"● 服务状态: {status}")
                    status_w.styles.color = "#e67e22"

            if not check_root():
                self._msg("提示: systemd 管理需要 root 权限", error=True)
            else:
                frpc_ok, frpc_msg = check_frpc()
                if not frpc_ok:
                    self._msg("提示: 未检测到 frpc，请先在设置中配置 frpc 路径", error=True)
                else:
                    self._msg("frpc 可用", error=False)

        except Exception as e:
            self._msg(f"加载失败: {e}")

    @work(exclusive=True)
    async def do_install_service(self):
        if not check_root():
            self._msg("需要 root 权限来安装 systemd 服务")
            return
        btn = None
        try:
            btn = self.query_one("#svc-install")
            if isinstance(btn, Button):
                btn.disabled = True
                btn.label = "安装中..."

            config = self.api.get_proxy_config(self.proxy_id)
            proxy_list = self.api.get_proxy_list()
            proxies = proxy_list if isinstance(proxy_list, list) else proxy_list.get("proxies", [])
            proxy_info = {}
            for p in proxies:
                if isinstance(p, dict) and p.get("proxyId") == self.proxy_id:
                    proxy_info = p
                    break

            if isinstance(config, dict) and "config" in config:
                tunnel_config = config["config"]
            else:
                tunnel_config = str(config)

            write_tunnel_config(self.proxy_id, tunnel_config)
            ok, msg = install_tunnel_service(self.proxy_id)
            if ok:
                self._msg("服务安装成功", error=False)
            else:
                self._msg(msg, error=True)
            self.refresh_data()
        except Exception as e:
            self._msg(f"安装失败: {e}")
        finally:
            if btn is not None:
                btn.disabled = False
                btn.label = "安装服务"

    @work(exclusive=True)
    async def do_service_action(self, action: str):
        if not check_root():
            self._msg("需要 root 权限")
            return
        try:
            if action == "start":
                ok, msg = start_tunnel(self.proxy_id)
            elif action == "stop":
                ok, msg = stop_tunnel(self.proxy_id)
            elif action == "restart":
                ok, msg = restart_tunnel(self.proxy_id)
            else:
                return
            if ok:
                self._msg(f"{action} 成功", error=False)
            else:
                self._msg(f"{action} 失败: {msg}", error=True)
            self.refresh_data()
        except Exception as e:
            self._msg(f"{action} 失败: {e}")

    @work(exclusive=True)
    async def do_remove_service(self):
        if not check_root():
            self._msg("需要 root 权限")
            return
        try:
            remove_tunnel_service(self.proxy_id)
            remove_tunnel_config(self.proxy_id)
            self._msg("服务已卸载", error=False)
            self.refresh_data()
        except Exception as e:
            self._msg(f"卸载失败: {e}")

    def _msg(self, text: str, error: bool = False):
        w = self.query_one("#detail-msg")
        if isinstance(w, Static):
            w.update(text)
            w.styles.color = "#e74c3c" if error else "#27ae60"
