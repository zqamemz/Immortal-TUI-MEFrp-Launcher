"""frpc 隧道进程管理模块 (Systemd)."""

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from sml.manager.config import (
    SML_TUNNELS_DIR,
    SYSTEMD_SERVICE_PREFIX,
    Config,
)


def _run_cmd(cmd: list[str], use_sudo: bool = True) -> tuple[int, str, str]:
    """运行系统命令，可选 sudo。"""
    if use_sudo and os.geteuid() != 0:
        cmd = ["sudo"] + cmd
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "命令未找到，请确认系统已安装所需工具"
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"


def _systemctl(args: list[str]) -> tuple[int, str, str]:
    """调用 systemctl。"""
    cfg = Config()
    return _run_cmd(["systemctl"] + args, use_sudo=cfg.use_sudo)


# ---------------------------------------------------------------------------
# 隧道配置目录管理
# ---------------------------------------------------------------------------

def ensure_tunnel_dirs():
    """确保隧道配置目录存在。"""
    SML_TUNNELS_DIR.mkdir(parents=True, exist_ok=True)


def get_tunnel_config_path(proxy_id: int) -> Path:
    """获取隧道配置文件的完整路径。"""
    ensure_tunnel_dirs()
    return SML_TUNNELS_DIR / f"tunnel-{proxy_id}.toml"


def write_tunnel_config(proxy_id: int, config_content: str) -> Path:
    """将隧道配置写入本地文件。"""
    path = get_tunnel_config_path(proxy_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(config_content)
    return path


def remove_tunnel_config(proxy_id: int):
    """删除本地的隧道配置文件。"""
    path = get_tunnel_config_path(proxy_id)
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Systemd 服务管理
# ---------------------------------------------------------------------------

def _service_name(proxy_id: int) -> str:
    return f"{SYSTEMD_SERVICE_PREFIX}{proxy_id}"


def _service_file_path(proxy_id: int) -> str:
    return f"/etc/systemd/system/{_service_name(proxy_id)}.service"


def get_tunnel_status(proxy_id: int) -> str:
    """获取隧道 systemd 服务状态。返回: active / inactive / failed / not-found"""
    code, out, _ = _systemctl(["is-active", _service_name(proxy_id)])
    if code == 0:
        return out.strip()
    # 如果服务文件不存在
    if not os.path.exists(_service_file_path(proxy_id)):
        return "not-found"
    return "inactive"


def get_all_tunnel_status(proxy_ids: list[int]) -> dict[int, str]:
    """批量查询多个隧道的 systemd 服务状态（一次 systemctl 调用）。

    返回 {proxy_id: "active"/"inactive"/"not-found"/"failed"} 字典。
    """
    if not proxy_ids:
        return {}

    # 使用 systemctl is-active 批量查询
    svcs = [_service_name(pid) for pid in proxy_ids]
    code, out, err = _systemctl(["is-active"] + svcs)

    lines = (out or "").strip().splitlines()
    result = {}
    for i, pid in enumerate(proxy_ids):
        if i < len(lines):
            status = lines[i].strip()
            if status in ("active", "inactive", "failed"):
                result[pid] = status
            else:
                result[pid] = "inactive"
        else:
            result[pid] = "inactive"

        # 如果服务文件不存在，覆盖为 not-found
        if result[pid] == "inactive" and not os.path.exists(_service_file_path(pid)):
            result[pid] = "not-found"
    return result


def install_tunnel_service(proxy_id: int) -> tuple[bool, str]:
    """创建并启用 systemd 服务。"""
    cfg = Config()
    frpc = cfg.frpc_path
    config_path = get_tunnel_config_path(proxy_id)

    if not os.path.exists(frpc):
        return False, f"frpc 未找到: {frpc}"

    if not config_path.exists():
        return False, f"隧道配置文件不存在: {config_path}"

    service_content = f"""[Unit]
Description=SML Tunnel #{proxy_id} - ME Frp Proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={shlex.quote(frpc)} -c {shlex.quote(str(config_path))}
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
"""
    # 写入服务文件
    tmp_path = f"/tmp/sml-tunnel-{proxy_id}.service"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(service_content)
    except IOError as e:
        return False, f"无法写入临时服务文件: {e}"

    code, _, err = _run_cmd(
        ["cp", tmp_path, _service_file_path(proxy_id)],
        use_sudo=cfg.use_sudo,
    )
    os.unlink(tmp_path)
    if code != 0:
        return False, f"复制服务文件失败: {err}"

    # 重新加载 systemd
    code, _, err = _systemctl(["daemon-reload"])
    if code != 0:
        return False, f"daemon-reload 失败: {err}"

    return True, "服务安装成功"


def start_tunnel(proxy_id: int) -> tuple[bool, str]:
    """启动隧道 systemd 服务。"""
    code, _, err = _systemctl(["start", _service_name(proxy_id)])
    if code != 0:
        return False, f"启动失败: {err}"
    # 等待片刻确认状态
    time.sleep(1)
    status = get_tunnel_status(proxy_id)
    if status == "active":
        return True, "隧道已启动"
    return False, f"启动后状态异常: {status}"


def stop_tunnel(proxy_id: int) -> tuple[bool, str]:
    """停止隧道 systemd 服务。"""
    code, _, err = _systemctl(["stop", _service_name(proxy_id)])
    if code != 0:
        return False, f"停止失败: {err}"
    return True, "隧道已停止"


def restart_tunnel(proxy_id: int) -> tuple[bool, str]:
    """重启隧道 systemd 服务。"""
    code, _, err = _systemctl(["restart", _service_name(proxy_id)])
    if code != 0:
        return False, f"重启失败: {err}"
    return True, "隧道已重启"


def enable_tunnel_service(proxy_id: int) -> tuple[bool, str]:
    """设置隧道开机自启。"""
    code, _, err = _systemctl(["enable", _service_name(proxy_id)])
    if code != 0:
        return False, f"启用自启失败: {err}"
    return True, "已启用开机自启"


def disable_tunnel_service(proxy_id: int) -> tuple[bool, str]:
    """取消隧道开机自启。"""
    code, _, err = _systemctl(["disable", _service_name(proxy_id)])
    if code != 0:
        return False, f"禁用自启失败: {err}"
    return True, "已禁用开机自启"


def remove_tunnel_service(proxy_id: int) -> tuple[bool, str]:
    """删除隧道 systemd 服务。"""
    cfg = Config()
    svc = _service_file_path(proxy_id)
    if not os.path.exists(svc):
        return True, "服务文件不存在，无需删除"

    # 先停止
    _systemctl(["stop", _service_name(proxy_id)])
    _systemctl(["disable", _service_name(proxy_id)])

    code, _, err = _run_cmd(["rm", "-f", svc], use_sudo=cfg.use_sudo)
    if code != 0:
        return False, f"删除服务文件失败: {err}"

    _systemctl(["daemon-reload"])
    remove_tunnel_config(proxy_id)
    return True, "已删除隧道服务"


# ---------------------------------------------------------------------------
# 批量操作
# ---------------------------------------------------------------------------

def get_all_tunnel_services() -> list[int]:
    """列出所有已安装的 SML 隧道服务的 proxy_id。"""
    code, out, _ = _systemctl(
        ["list-units", "--type=service", "--all", "--no-legend", f"{SYSTEMD_SERVICE_PREFIX}*"]
    )
    ids = []
    if code == 0:
        for line in out.splitlines():
            parts = line.split()
            if parts:
                name = parts[0]
                if name.startswith(SYSTEMD_SERVICE_PREFIX):
                    try:
                        pid = int(name.replace(SYSTEMD_SERVICE_PREFIX, "").split(".")[0])
                        ids.append(pid)
                    except ValueError:
                        pass
    return ids


def remove_all_tunnel_services() -> list[str]:
    """卸载所有 SML 隧道 systemd 服务（用于 mefrpc 卸载前清理）。

    Returns:
        清理过程中的消息列表。
    """
    ids = get_all_tunnel_services()
    msgs = []
    for pid in ids:
        ok, msg = remove_tunnel_service(pid)
        msgs.append(f"  [{'✓' if ok else '✗'}] 隧道 #{pid}: {msg}")
    return msgs


def stop_all_tunnels() -> tuple[int, list[str]]:
    """停止所有 SML 隧道。返回 (数量, 消息列表)。"""
    ids = get_all_tunnel_services()
    msgs = []
    for pid in ids:
        ok, msg = stop_tunnel(pid)
        msgs.append(f"  [{ '✓' if ok else '✗' }] 隧道 #{pid}: {msg}")
    return len(ids), msgs


def check_frpc() -> tuple[bool, str]:
    """检查 frpc/mefrpc 是否可用。"""
    cfg = Config()
    frpc = cfg.frpc_path
    if not os.path.exists(frpc):
        # 尝试在 PATH 中查找 frpc 或 mefrpc
        found = shutil.which("frpc") or shutil.which("mefrpc")
        if found:
            cfg.frpc_path = found
            return True, f"frpc 已找到: {found}"
        return False, "frpc 未找到，请运行 sml-install 安装内置 mefrpc"
    return True, f"frpc 已找到: {frpc}"
