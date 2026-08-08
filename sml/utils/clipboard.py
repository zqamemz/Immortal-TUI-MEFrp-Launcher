"""跨平台剪贴板读取工具.

优先使用 pyperclip（若已安装），否则用平台命令回退：
- Linux: xclip / xsel / wl-paste
- Windows: powershell Get-Clipboard
- macOS: pbpaste
- Termux: termux-clipboard-get

在 SSH 等无系统剪贴板的环境下，自动回退到手动粘贴模式。
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Optional

logger = logging.getLogger("sml.clipboard")


def _try_pyperclip() -> Optional[str]:
    """尝试使用 pyperclip 库读取剪贴板。"""
    try:
        import pyperclip
        text = pyperclip.paste()
        return text.strip() if text and text.strip() else None
    except Exception:
        return None


def _try_powershell() -> Optional[str]:
    """Windows: 通过 PowerShell Get-Clipboard 读取。"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def _try_xclip() -> Optional[str]:
    """Linux X11: 通过 xclip 读取。"""
    if not shutil.which("xclip"):
        return None
    try:
        result = subprocess.run(
            ["xclip", "-o", "-selection", "clipboard"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def _try_xsel() -> Optional[str]:
    """Linux X11: 通过 xsel 读取。"""
    if not shutil.which("xsel"):
        return None
    try:
        result = subprocess.run(
            ["xsel", "-ob"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def _try_wl_paste() -> Optional[str]:
    """Linux Wayland: 通过 wl-paste 读取。"""
    if not shutil.which("wl-paste"):
        return None
    try:
        result = subprocess.run(
            ["wl-paste"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def _try_pbpaste() -> Optional[str]:
    """macOS: 通过 pbpaste 读取。"""
    if not shutil.which("pbpaste"):
        return None
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def _try_termux_clipboard() -> Optional[str]:
    """Termux (Android): 通过 termux-clipboard-get 读取。"""
    if not shutil.which("termux-clipboard-get"):
        return None
    try:
        result = subprocess.run(
            ["termux-clipboard-get"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            text = result.stdout.strip()
            return text if text else None
    except Exception:
        pass
    return None


def detect_environment() -> str:
    """检测当前运行环境，返回环境标识。

    返回值：
    - "local"         本地桌面环境（剪贴板可用）
    - "termux"        Termux (Android，剪贴板可用)
    - "mobaxterm"     MobaXterm（剪贴板被桥接，可用）
    - "vscode-remote" VS Code Remote（剪贴板被桥接，可用）
    - "wsl"           WSL（剪贴板被桥接，可用）
    - "ssh"           OpenSSH 远程会话（剪贴板通常不可用）
    - "tmux"          tmux 会话
    - "screen"        GNU screen 会话
    - "rdp"           Windows 远程桌面
    - "headless"      Linux 无图形显示（剪贴板不可用）

    注意：会桥接剪贴板的工具（Termux / MobaXterm / VS Code Remote / WSL）
    优先于通用 SSH 标记判断，避免误判为无剪贴板环境。
    Xshell / SecureCRT / Termius / PuTTY / Tabby 等客户端不设置可识别的
    环境变量，会被归入通用 "ssh"，回退到手动粘贴（这些工具默认不桥接
    远程剪贴板）。
    """
    env = os.environ

    # 工具特定标记优先（这些工具会桥接系统剪贴板）
    if "TERMUX_VERSION" in env or env.get("PREFIX", "").startswith(
        "/data/data/com.termux"
    ):
        return "termux"
    if "MOBAXTERM" in env:
        return "mobaxterm"
    if "VSCODE_REMOTE" in env or env.get("TERM_PROGRAM") == "vscode":
        return "vscode-remote"
    if "WSL_DISTRO_NAME" in env or "WSL_INTEROP" in env:
        return "wsl"

    # OpenSSH 服务端设置的连接变量
    if "SSH_CONNECTION" in env or "SSH_CLIENT" in env or "SSH_TTY" in env:
        return "ssh"

    # tmux / GNU screen 会话
    if "TMUX" in env:
        return "tmux"
    if "STY" in env:
        return "screen"

    # Windows 本地终端（Windows Terminal / Git Bash / MSYS2 / Cygwin）
    if sys.platform == "win32":
        if "WT_SESSION" in env or env.get("MSYSTEM"):
            return "local"

    # macOS / Linux 本地终端模拟器标记
    if env.get("TERM_PROGRAM") in ("iTerm.app", "WezTerm", "Hyper", "Tabby"):
        return "local"
    if any(
        k in env
        for k in (
            "KITTY_WINDOW_ID",
            "ALACRITTY_LOG",
            "VTE_VERSION",
            "KONSOLE_VERSION",
            "XTERM_VERSION",
        )
    ):
        return "local"

    # Windows 远程桌面
    if sys.platform == "win32":
        session = env.get("SESSIONNAME", "")
        if session.startswith("RDP-Tcp") or env.get("REMOTE_SESSION") == "1":
            return "rdp"

    # Linux 无图形显示 → 无头 / SSH 环境
    if sys.platform.startswith("linux") and not (
        "DISPLAY" in env or "WAYLAND_DISPLAY" in env
    ):
        return "headless"

    return "local"


def is_ssh_environment() -> bool:
    """检测当前是否运行在 SSH 等无系统剪贴板的环境中。

    返回 True 表示系统剪贴板大概率不可用，应回退到手动粘贴。
    识别多种 SSH 工具/终端环境（OpenSSH、无头 Linux 等）。
    """
    return detect_environment() in ("ssh", "headless")


def get_clipboard_text() -> Optional[str]:
    """从系统剪贴板读取文本（跨平台）。

    探测顺序: pyperclip > powershell (Win) > pbpaste (macOS) >
    xclip > xsel > wl-paste > termux-clipboard-get (Linux/Termux)
    """
    # 1. pyperclip 库（需安装 python -m pip install pyperclip）
    text = _try_pyperclip()
    if text:
        return text

    # 2. 平台特定命令
    if sys.platform == "win32":
        text = _try_powershell()
        if text:
            return text
    elif sys.platform == "darwin":
        text = _try_pbpaste()
        if text:
            return text
    else:
        # Linux — 依次尝试 xclip / xsel / wl-paste / termux-clipboard-get
        text = _try_xclip()
        if text:
            return text
        text = _try_xsel()
        if text:
            return text
        text = _try_wl_paste()
        if text:
            return text
        text = _try_termux_clipboard()
        if text:
            return text

    return None


def paste_to_input(input_widget) -> bool:
    """将剪贴板内容粘贴到 Textual Input 组件中。

    返回是否粘贴成功。
    """
    text = get_clipboard_text()
    if text is None:
        return False

    # 在光标位置插入文本
    cursor_pos = input_widget.cursor_position
    old_value = input_widget.value
    new_value = old_value[:cursor_pos] + text + old_value[cursor_pos:]
    input_widget.value = new_value
    # 将光标移到粘贴内容之后
    input_widget.cursor_position = cursor_pos + len(text)
    return True
