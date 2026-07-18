"""创建隧道屏幕."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Header, Footer, Static, Select
from textual import work
from rich.text import Text

from sml.api.client import MEFrpAPI, APIError


class TunnelCreateScreen(Screen):
    """创建隧道表单 + 节点信息面板。"""

    TITLE = "创建隧道 - SML"

    CSS = """
    TunnelCreateScreen {
        layout: horizontal;
    }

    #create-form {
        width: 48;
        min-width: 48;
        height: 100%;
        padding: 1 2;
        background: #1f2335;
        border: solid #3b4261;
        margin: 1 0 1 1;
    }

    #create-form > Label {
        margin-top: 1;
    }

    #create-form > Input, #create-form > Select {
        margin-bottom: 0;
    }

    #create-actions {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    #create-actions > Button {
        margin: 0 1;
    }

    #create-msg {
        height: 3;
    }

    #node-panel {
        width: 1fr;
        height: 100%;
        margin: 0 1 0 0;
        padding: 0 1;
    }

    #node-panel-title {
        height: 3;
        color: #ff9e64;
        text-style: bold;
        padding: 0 1;
    }

    #node-list {
        height: 1fr;
        padding: 0;
    }

    .node-card {
        background: #24283b;
        border: solid #3b4261;
        padding: 1 2;
        margin: 0 0 1 0;
        height: auto;
    }

    .node-card-selected {
        background: #24283b;
        border: solid #2680eb;
        padding: 1 2;
        margin: 0 0 1 0;
        height: auto;
    }

    .node-header {
        color: #c0d0e0;
        text-style: bold;
        height: 1;
    }

    .node-tags {
        height: 1;
    }

    .node-desc {
        color: #565f89;
        height: auto;
        max-height: 3;
    }

    .node-load {
        height: 1;
        padding: 0 0;
    }

    .node-sep {
        color: #3b4261;
        height: 1;
    }

    .tag-tcp {
        color: #ffffff;
        background: #27ae60;
    }

    .tag-udp {
        color: #ffffff;
        background: #2680eb;
    }

    .tag-http {
        color: #ffffff;
        background: #e67e22;
    }

    .tag-https {
        color: #ffffff;
        background: #e74c3c;
    }

    .tag-stcp {
        color: #ffffff;
        background: #8e44ad;
    }

    .tag-bandwidth {
        color: #7dcfff;
        background: #2d3a4f;
    }

    .tag-vip {
        color: #ffffff;
        background: #e67e22;
    }

    .tag-overload {
        color: #ffffff;
        background: #c0392b;
    }

    .load-bar {
        color: #27ae60;
    }

    .load-bar-warn {
        color: #e67e22;
    }

    .load-bar-danger {
        color: #e74c3c;
    }

    .load-bar-full {
        color: #c0392b;
    }

    .node-load-text {
        color: #565f89;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = MEFrpAPI()
        self.nodes: list = []
        self.proxy_types = ["tcp", "udp", "http", "https", "stcp", "xtcp"]
        self.node_map: dict = {}  # nodeId -> node dict

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="create-form"):
            yield Static("创建新隧道", classes="title")
            yield Label("隧道名称:")
            yield Input(placeholder="例如: 我的MC服务器", id="t-name")
            yield Label("隧道类型:")
            yield Select(
                [(t, t) for t in self.proxy_types],
                id="t-type", value="tcp",
            )
            yield Label("选择节点:")
            yield Select([], id="t-node")
            yield Label("本地地址:")
            yield Input(placeholder="例如: 127.0.0.1", id="t-local-addr", value="127.0.0.1")
            yield Label("本地端口:")
            yield Input(placeholder="例如: 25565", id="t-local-port")
            yield Label("远程端口 (TCP/UDP):")
            yield Input(placeholder="留空自动分配", id="t-remote-port")
            yield Label("域名 (HTTP/HTTPS):")
            yield Input(placeholder="例如: example.com", id="t-domain")
            yield Static("", id="create-msg")
            with Horizontal(id="create-actions"):
                yield Button("创建隧道", id="btn-create", variant="primary")
                yield Button("返回", id="btn-back")
        with Vertical(id="node-panel"):
            yield Static("节点信息", id="node-panel-title")
            yield ScrollableContainer(id="node-list")
        yield Footer()

    def on_mount(self):
        self._load_nodes()

    # ------------------------------------------------------------------ #
    # 节点加载
    # ------------------------------------------------------------------ #

    @work(exclusive=True)
    async def _load_nodes(self):
        msg = self.query_one("#create-msg")
        if isinstance(msg, Static):
            msg.update("正在加载节点列表...")
        try:
            data = self.api.get_create_proxy_data()
            nodes = data if isinstance(data, list) else data.get("nodes", data.get("nodeList", []))
            self.nodes = nodes

            # 构建 nodeId -> node 映射
            self.node_map = {}
            for n in self.nodes:
                if isinstance(n, dict):
                    nid = n.get("nodeId", n.get("id", 0))
                    self.node_map[str(nid)] = n

            # 填充下拉选项
            select = self.query_one("#t-node")
            if isinstance(select, Select):
                options = []
                for n in nodes:
                    if isinstance(n, dict):
                        nid = n.get("nodeId", n.get("id", 0))
                        nname = n.get("nodeName", n.get("name", f"节点{nid}"))
                        options.append((f"{nname} (ID:{nid})", str(nid)))
                select.set_options(options)

            # 渲染右侧节点卡片
            self._render_node_cards()

            if isinstance(msg, Static):
                msg.update(f"已加载 {len(nodes)} 个节点")
                msg.styles.color = "#27ae60"
        except Exception as e:
            if isinstance(msg, Static):
                msg.update(f"加载节点失败: {e}")

    # ------------------------------------------------------------------ #
    # 节点卡片渲染
    # ------------------------------------------------------------------ #

    def _render_node_cards(self, highlight_id: str = ""):
        """渲染所有节点卡片到右侧面板。"""
        node_list = self.query_one("#node-list")
        if not isinstance(node_list, ScrollableContainer):
            return
        node_list.remove_children()

        # 按地区分组
        groups: dict[str, list] = {}
        for n in self.nodes:
            if not isinstance(n, dict):
                continue
            nid = str(n.get("nodeId", n.get("id", "?")))
            region = self._get_region(n)
            groups.setdefault(region, []).append((nid, n))

        for region, items in groups.items():
            # 区域标题
            count = len(items)
            region_title = Static(
                Text(f"  {region} ({count})", style="#ff9e64"),
                classes="node-sep",
            )
            node_list.mount(region_title)

            for nid, n in items:
                card = self._build_node_card(n, nid, nid == highlight_id)
                node_list.mount(card)

    def _get_region(self, node: dict) -> str:
        """从节点名称中提取区域。"""
        name = node.get("nodeName", node.get("name", ""))
        # 常见格式: "北京 ①" "四川/成都 ②" "广东/肇庆 ①"
        for sep in ["/", " "]:
            if sep in name:
                return name.split(sep)[0].strip()
        return name[:4] if len(name) > 4 else name or "其他"

    def _build_node_card(self, node: dict, nid: str, selected: bool = False) -> Vertical:
        """构建单个节点卡片。"""
        name = node.get("nodeName", node.get("name", f"节点 {nid}"))
        desc = node.get("description", node.get("desc", node.get("remark", "")))
        bandwidth = node.get("bandwidth", node.get("rate", node.get("maxBandwidth", "")))
        is_vip = node.get("isVip", node.get("vip", False))
        is_overload = node.get("isOverload", node.get("overload", False))
        load = node.get("load", node.get("usage", 0))

        # 支持的协议
        protocols = []
        if node.get("supportTcp", node.get("tcp", True)):
            protocols.append(("TCP", "#27ae60"))
        if node.get("supportUdp", node.get("udp", True)):
            protocols.append(("UDP", "#2680eb"))
        if node.get("supportHttp", node.get("http", False)):
            protocols.append(("HTTP", "#e67e22"))
        if node.get("supportHttps", node.get("https", False)):
            protocols.append(("HTTPS", "#e74c3c"))
        if node.get("supportStcp", node.get("stcp", False)):
            protocols.append(("STCP", "#8e44ad"))

        card_class = "node-card-selected" if selected else "node-card"

        children = []

        # 标题行: # ID 名称 VIP 过载
        header = Text()
        header.append(f"# {nid} {name}", style="bold #c0d0e0")
        if is_vip:
            header.append("  VIP", style="bold #e67e22")
        if is_overload:
            header.append("  过载", style="bold #c0392b")
        children.append(Static(header, classes="node-header"))

        # 标签行: TCP UDP 200Mbps
        tags = Text()
        first = True
        for proto, color in protocols:
            if not first:
                tags.append("  ")
            tags.append(proto, style=color)
            first = False
        if bandwidth:
            if not first:
                tags.append("  ")
            tags.append(f" {bandwidth} ", style="#7dcfff on #2d3a4f")
        if len(tags) > 0:
            children.append(Static(tags, classes="node-tags"))

        # 描述
        if desc:
            desc_text = str(desc)[:80]
            children.append(Static(Text(desc_text, style="#565f89"), classes="node-desc"))

        # 负载条
        load_pct = self._parse_load(load)
        children.append(self._make_load_bar(load_pct))

        # 分隔线
        children.append(Static(Text("─" * 30, style="#3b4261"), classes="node-sep"))

        return Vertical(*children, classes=card_class, id=f"node-card-{nid}")

    def _parse_load(self, load) -> int:
        """解析负载值为 0-100 的整数。"""
        if isinstance(load, (int, float)):
            v = int(load)
            return max(0, min(100, v))
        if isinstance(load, str):
            load = load.strip().replace("%", "")
            try:
                return max(0, min(100, int(float(load))))
            except ValueError:
                pass
        return 0

    def _make_load_bar(self, pct: int) -> Static:
        """生成负载进度条文本。"""
        bar_width = 20
        filled = int(bar_width * pct / 100)
        empty = bar_width - filled

        if pct >= 100:
            color = "#c0392b"
        elif pct >= 80:
            color = "#e74c3c"
        elif pct >= 50:
            color = "#e67e22"
        else:
            color = "#27ae60"

        bar = Text()
        bar.append("█" * filled, style=color)
        bar.append("░" * empty, style="#3b4261")
        bar.append(f"  {pct}% 负载", style="#565f89")
        return Static(bar, classes="node-load")

    # ------------------------------------------------------------------ #
    # 事件处理
    # ------------------------------------------------------------------ #

    def on_select_changed(self, event: Select.Changed):
        """节点下拉选择变化时，高亮对应的节点卡片。"""
        if event.select.id == "t-node":
            val = str(event.value) if event.value is not Select.BLANK else ""
            # 先清除所有高亮
            for child in self.query_one("#node-list").query(".node-card-selected"):
                child.set_class(False, "node-card-selected")
                child.set_class(True, "node-card")
            # 高亮选中卡片
            if val:
                card = self.query_one(f"#node-card-{val}")
                if card:
                    card.set_class(False, "node-card")
                    card.set_class(True, "node-card-selected")
                    card.scroll_visible()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-create":
            self.do_create()
        elif event.button.id == "btn-back":
            self.app.pop_screen()

    def _get(self, id_: str) -> str:
        w = self.query_one(f"#{id_}")
        if isinstance(w, Input):
            return w.value.strip()
        return ""

    def _msg(self, text: str, error: bool = True):
        w = self.query_one("#create-msg")
        if isinstance(w, Static):
            w.update(f"{'⚠' if error else '✓'} {text}")
            w.styles.color = "#e74c3c" if error else "#27ae60"

    @work(exclusive=True)
    async def do_create(self):
        name = self._get("t-name")
        local_addr = self._get("t-local-addr")
        local_port = self._get("t-local-port")
        remote_port = self._get("t-remote-port")
        domain = self._get("t-domain")

        type_select = self.query_one("#t-type")
        node_select = self.query_one("#t-node")

        ptype = type_select.value if isinstance(type_select, Select) else "tcp"
        node_val = node_select.value if isinstance(node_select, Select) else ""

        if not name or not local_port:
            self._msg("请填写隧道名称和本地端口")
            return

        params = {
            "proxyName": name,
            "proxyType": ptype,
            "localAddr": local_addr,
            "localPort": int(local_port),
        }

        if node_val and node_val is not Select.BLANK:
            params["nodeId"] = int(node_val) if str(node_val).isdigit() else node_val
        if remote_port:
            params["remotePort"] = int(remote_port)
        if domain and ptype in ("http", "https"):
            params["domain"] = domain

        btn = self.query_one("#btn-create")
        if isinstance(btn, Button):
            btn.disabled = True
            btn.label = "创建中..."

        try:
            result = self.api.create_proxy(**params)
            self._msg(f"隧道 [{name}] 创建成功！", error=False)
        except Exception as e:
            self._msg(f"创建失败: {e}")
        finally:
            if isinstance(btn, Button):
                btn.disabled = False
                btn.label = "创建隧道"
