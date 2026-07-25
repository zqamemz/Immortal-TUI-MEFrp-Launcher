"""mefrpc 自动安装模块 - 将内置的 mefrpc 二进制部署到系统路径。"""

import os
import shutil
import stat
import sys
from pathlib import Path

# mefrpc 在包内的位置（根据平台决定文件名）
_BUNDLED_MEFRPC = Path(__file__).parent / ("mefrpc.exe" if sys.platform == "win32" else "mefrpc")

# 平台相关安装目标（优先用户目录，无需 sudo）
if sys.platform == "win32":
    INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SML" / "bin"
else:
    # 优先尝试用户级目录，不需要 root 权限
    _user_bin = Path.home() / ".local" / "bin"
    _system_bin = Path("/usr/local/bin")
    # 检测用户级目录是否可写，或是否在 PATH 中
    if _user_bin.exists() or os.access(str(Path.home() / ".local"), os.W_OK):
        INSTALL_DIR = _user_bin
    else:
        # 若 /usr/local/bin 可写（如某些容器环境）则用系统目录，否则仍用用户目录
        if os.access(str(_system_bin), os.W_OK):
            INSTALL_DIR = _system_bin
        else:
            INSTALL_DIR = _user_bin

INSTALL_NAME = "mefrpc"
INSTALL_PATH = INSTALL_DIR / INSTALL_NAME


def is_installed() -> bool:
    """检查 mefrpc 是否已正确安装到系统路径。"""
    return INSTALL_PATH.exists() and os.access(INSTALL_PATH, os.X_OK)


def install(force: bool = False) -> tuple[bool, str]:
    """将内置的 mefrpc 安装到系统路径。

    Args:
        force: 强制覆盖已存在的安装。

    Returns:
        (成功与否, 消息文本)
    """
    # 检查内置二进制是否存在
    if not _BUNDLED_MEFRPC.exists():
        return False, f"内置 mefrpc 未找到: {_BUNDLED_MEFRPC}"

    # 如果已安装且不需要强制覆盖
    if is_installed() and not force:
        return True, f"meFrpc 已安装: {INSTALL_PATH}"

    # 确保目标目录存在
    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # 目录创建失败，回退到使用内置路径
        if _BUNDLED_MEFRPC.exists():
            os.chmod(str(_BUNDLED_MEFRPC), os.stat(str(_BUNDLED_MEFRPC)).st_mode | stat.S_IEXEC)
            return True, f"无法创建安装目录，使用内置版本: {_BUNDLED_MEFRPC}"
        return False, f"无法创建安装目录: {INSTALL_DIR}"

    # 复制二进制文件
    try:
        shutil.copy2(str(_BUNDLED_MEFRPC), str(INSTALL_PATH))
    except PermissionError:
        # TUI 环境中无法交互输入 sudo 密码，直接提示用户手动操作
        return False, (
            f"权限不足，无法写入 {INSTALL_DIR}。"
            f"请手动执行: cp {_BUNDLED_MEFRPC} {INSTALL_PATH} && chmod +x {INSTALL_PATH}"
        )
    except Exception as e:
        return False, f"复制失败: {e}"

    # 设置可执行权限 (Unix)
    if sys.platform != "win32":
        try:
            st = os.stat(str(INSTALL_PATH))
            os.chmod(str(INSTALL_PATH), st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

    # 验证安装
    if is_installed():
        return True, f"meFrpc 已安装到: {INSTALL_PATH}"
    else:
        # Windows 下 os.access 可能不准确，检查文件是否存在即可
        if INSTALL_PATH.exists():
            return True, f"meFrpc 已安装到: {INSTALL_PATH}"
        return False, f"安装后验证失败，请手动检查: {INSTALL_PATH}"


def uninstall() -> tuple[bool, str]:
    """卸载已安装的 mefrpc。"""
    if not INSTALL_PATH.exists():
        return True, "meFrpc 未安装，无需卸载"

    # 先清理可能残留的 systemd 服务，避免指向已删除的二进制
    try:
        from sml.manager.systemd import remove_all_tunnel_services
        remove_all_tunnel_services()
    except Exception:
        pass

    try:
        INSTALL_PATH.unlink()
    except PermissionError:
        return False, (
            f"权限不足，无法删除 {INSTALL_PATH}。"
            f"请手动执行: rm -f {INSTALL_PATH}"
        )
    except Exception as e:
        return False, f"卸载失败: {e}"

    if not INSTALL_PATH.exists():
        return True, "meFrpc 已卸载"
    return False, "卸载失败，请手动删除"


def get_install_path() -> str:
    """获取 mefrpc 的实际可用路径（已安装路径 > 内置路径）。"""
    if is_installed():
        return str(INSTALL_PATH)
    if _BUNDLED_MEFRPC.exists():
        return str(_BUNDLED_MEFRPC)
    return ""
