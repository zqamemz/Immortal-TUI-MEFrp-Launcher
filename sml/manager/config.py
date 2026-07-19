"""SML 配置管理模块."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "sml"
CONFIG_FILE = CONFIG_DIR / "config.json"
FRPC_BIN = "/usr/local/bin/mefrpc"
SML_TUNNELS_DIR = Path("/etc/sml/tunnels")
SYSTEMD_SERVICE_PREFIX = "sml-tunnel-"


class Config:
    """管理 SML 本地配置（Token、frpc 路径等）。"""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}

    def _save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ---- Token ----
    @property
    def token(self) -> str:
        return self._data.get("token", "")

    @token.setter
    def token(self, value: str):
        self._data["token"] = value
        self._save()

    def clear_token(self):
        self._data.pop("token", None)
        self._save()

    @property
    def has_token(self) -> bool:
        return bool(self._data.get("token"))

    # ---- 用户信息缓存 ----
    @property
    def username(self) -> str:
        return self._data.get("username", "")

    @username.setter
    def username(self, value: str):
        self._data["username"] = value
        self._save()

    # ---- frpc 路径 ----
    @property
    def frpc_path(self) -> str:
        configured = self._data.get("frpc_path", "")
        if configured and Path(configured).exists():
            return configured
        # 未配置或路径不存在，尝试从 installer 获取
        from sml.installer import get_install_path
        resolved = get_install_path()
        return resolved or configured or FRPC_BIN

    @frpc_path.setter
    def frpc_path(self, value: str):
        self._data["frpc_path"] = value
        self._save()

    # ---- 最近使用的节点 ID ----
    @property
    def last_node_id(self) -> int:
        return self._data.get("last_node_id", 0)

    @last_node_id.setter
    def last_node_id(self, value: int):
        self._data["last_node_id"] = value
        self._save()

    # ---- 获取全部配置 ----
    def get_all(self) -> dict:
        """获取配置快照。"""
        return dict(self._data)

    # ---- Systemd 相关 ----
    @property
    def use_sudo(self) -> bool:
        return self._data.get("use_sudo", True)

    @use_sudo.setter
    def use_sudo(self, value: bool):
        self._data["use_sudo"] = value
        self._save()

    def get_all(self) -> dict:
        return dict(self._data)

    def clear_all(self):
        self._data = {}
        self._save()
