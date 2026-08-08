import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sml.utils import clipboard


class DetectEnvironmentTests(unittest.TestCase):
    """验证 detect_environment 对多种 SSH 工具/终端的识别。"""

    def _detect(self, env, platform="linux"):
        with patch.dict("os.environ", env, clear=True), \
             patch.object(clipboard.sys, "platform", platform):
            return clipboard.detect_environment()

    def test_local_desktop(self):
        self.assertEqual(
            self._detect({"DISPLAY": ":0", "TERM": "xterm-256color"}),
            "local",
        )

    def test_openssh(self):
        self.assertEqual(
            self._detect({"SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}),
            "ssh",
        )
        self.assertEqual(self._detect({"SSH_CLIENT": "1.2.3.4 5000 22"}), "ssh")
        self.assertEqual(self._detect({"SSH_TTY": "/dev/pts/0"}), "ssh")

    def test_mobaxterm_bridges_clipboard(self):
        # MobaXterm 同时会设置 SSH 连接变量，但应优先识别为 mobaxterm
        self.assertEqual(
            self._detect({"MOBAXTERM": "1", "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}),
            "mobaxterm",
        )

    def test_vscode_remote_bridges_clipboard(self):
        self.assertEqual(
            self._detect({"VSCODE_REMOTE": "1", "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}),
            "vscode-remote",
        )
        self.assertEqual(
            self._detect({"TERM_PROGRAM": "vscode", "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}),
            "vscode-remote",
        )

    def test_wsl_bridges_clipboard(self):
        self.assertEqual(self._detect({"WSL_DISTRO_NAME": "Ubuntu"}), "wsl")
        self.assertEqual(self._detect({"WSL_INTEROP": "/run/WSL/1_interop"}), "wsl")

    def test_termux(self):
        self.assertEqual(self._detect({"TERMUX_VERSION": "0.118.0"}), "termux")
        self.assertEqual(
            self._detect({"PREFIX": "/data/data/com.termux/files/usr"}),
            "termux",
        )
        # Termux 内 SSH 到本机时剪贴板工具仍可用，优先识别为 termux
        self.assertEqual(
            self._detect({
                "TERMUX_VERSION": "0.118.0",
                "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22",
            }),
            "termux",
        )

    def test_windows_local_terminals(self):
        self.assertEqual(
            self._detect({"WT_SESSION": "abc123"}, platform="win32"),
            "local",
        )
        self.assertEqual(
            self._detect({"MSYSTEM": "MINGW64"}, platform="win32"),
            "local",
        )

    def test_local_terminal_markers(self):
        self.assertEqual(self._detect({"TERM_PROGRAM": "iTerm.app"}), "local")
        self.assertEqual(self._detect({"TERM_PROGRAM": "WezTerm"}), "local")
        self.assertEqual(self._detect({"KITTY_WINDOW_ID": "1"}), "local")
        self.assertEqual(
            self._detect({"ALACRITTY_LOG": "/tmp/alacritty.log"}),
            "local",
        )

    def test_ssh_wins_over_local_terminal_markers(self):
        # 远程会话即使 TERM_PROGRAM 被转发也按 SSH 处理（无剪贴板桥接）
        self.assertEqual(
            self._detect({
                "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22",
                "TERM_PROGRAM": "WezTerm",
            }),
            "ssh",
        )

    def test_tmux_and_screen(self):
        self.assertEqual(self._detect({"TMUX": "/tmp/tmux-1000/default,123,0"}), "tmux")
        self.assertEqual(self._detect({"STY": "12345.pts-0.host"}), "screen")

    def test_rdp_windows(self):
        self.assertEqual(
            self._detect({"SESSIONNAME": "RDP-Tcp#5"}, platform="win32"),
            "rdp",
        )
        self.assertEqual(
            self._detect({"REMOTE_SESSION": "1"}, platform="win32"),
            "rdp",
        )
        # Windows 本地控制台会话
        self.assertEqual(
            self._detect({"SESSIONNAME": "Console"}, platform="win32"),
            "local",
        )

    def test_headless_linux(self):
        self.assertEqual(self._detect({}), "headless")
        # 有显示则不是无头
        self.assertEqual(self._detect({"WAYLAND_DISPLAY": "wayland-0"}), "local")


class IsSshEnvironmentTests(unittest.TestCase):
    """验证 is_ssh_environment 的剪贴板可用性判断。"""

    def _is_ssh(self, env, platform="linux"):
        with patch.dict("os.environ", env, clear=True), \
             patch.object(clipboard.sys, "platform", platform):
            return clipboard.is_ssh_environment()

    def test_ssh_and_headless_are_true(self):
        self.assertTrue(self._is_ssh({"SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}))
        self.assertTrue(self._is_ssh({}))

    def test_bridging_tools_are_false(self):
        self.assertFalse(self._is_ssh({"MOBAXTERM": "1", "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}))
        self.assertFalse(self._is_ssh({"VSCODE_REMOTE": "1", "SSH_CONNECTION": "1.2.3.4 5000 5.6.7.8 22"}))
        self.assertFalse(self._is_ssh({"WSL_DISTRO_NAME": "Ubuntu"}))
        self.assertFalse(self._is_ssh({"TERMUX_VERSION": "0.118.0"}))

    def test_local_desktop_is_false(self):
        self.assertFalse(self._is_ssh({"DISPLAY": ":0"}))
        self.assertFalse(self._is_ssh({"WT_SESSION": "abc"}, platform="win32"))
        self.assertFalse(self._is_ssh({"MSYSTEM": "MINGW64"}, platform="win32"))


class TermuxClipboardTests(unittest.TestCase):
    """验证 Termux 环境下的 termux-clipboard-get 读取回退。"""

    def test_get_clipboard_text_falls_back_to_termux_clipboard_get(self):
        def fake_run(cmd, **kwargs):
            if cmd == ["termux-clipboard-get"]:
                return SimpleNamespace(returncode=0, stdout="hello\n")
            return SimpleNamespace(returncode=1, stdout="")

        def fake_which(name):
            return "/usr/bin/" + name if name == "termux-clipboard-get" else None

        with patch.object(clipboard, "_try_pyperclip", return_value=None), \
             patch.object(clipboard.sys, "platform", "linux"), \
             patch.object(clipboard.shutil, "which", side_effect=fake_which), \
             patch("subprocess.run", side_effect=fake_run):
            self.assertEqual(clipboard.get_clipboard_text(), "hello")


if __name__ == "__main__":
    unittest.main()
