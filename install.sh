#!/usr/bin/env bash
# SML 一键安装脚本
# 用法: bash install.sh [安装目录]
# 默认安装到 /opt/sml，可自定义：bash install.sh /usr/local/sml

set -e

# ── 配置 ────────────────────────────────────────────────────────────────────────
DEFAULT_INSTALL_DIR="/opt/sml"
INSTALL_DIR="${1:-$DEFAULT_INSTALL_DIR}"
VENV_DIR="$INSTALL_DIR/venv"
BIN_SML="/usr/local/bin/sml"

# ── 颜色输出 ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { printf "${CYAN}[INFO]${NC} %s\n" "$*"; }
ok()    { printf "${GREEN}[OK]${NC}   %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$*"; }
fail()  { printf "${RED}[FAIL]${NC} %s\n" "$*"; exit 1; }

# ── sudo 处理 ───────────────────────────────────────────────────────────────────
# 若安装目录需要 root 权限写入（/opt、/usr/local），自动加 sudo
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if ! [ -w "$(dirname "$INSTALL_DIR")" ] || ! [ -w "$(dirname "$BIN_SML")" ] 2>/dev/null; then
        if command -v sudo &>/dev/null; then
            SUDO="sudo"
        else
            warn "当前用户无写入权限且未找到 sudo，安装可能失败"
        fi
    fi
fi

# ── 检测 Python ─────────────────────────────────────────────────────────────────
info "检测 Python 版本..."
PYTHON=""
for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

[ -z "$PYTHON" ] && fail "未找到 Python 3.8+，请先安装 Python。"

MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo 0)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]; }; then
    fail "Python 版本需要 >= 3.8，当前是 $MAJOR.$MINOR"
fi
info "使用 Python: $PYTHON ($($PYTHON --version 2>&1))"

# ── 克隆/更新项目 ──────────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    info "项目已存在于 $INSTALL_DIR，执行 git pull 更新..."
    cd "$INSTALL_DIR"
    git pull || warn "git pull 失败，继续安装..."
else
    info "克隆项目到 $INSTALL_DIR..."
    $SUDO mkdir -p "$(dirname "$INSTALL_DIR")"
    $SUDO git clone https://github.com/zqamemz/Immortal-TUI-MEFrp-Launcher.git "$INSTALL_DIR" \
        || fail "克隆失败，请检查网络连接"
    cd "$INSTALL_DIR"
fi

# 非 root 运行时下放目录权限，避免后续 pip 写入失败
if [ "$(id -u)" -ne 0 ] && [ -d "$INSTALL_DIR" ]; then
    $SUDO chown -R "$(id -u):$(id -g)" "$INSTALL_DIR" 2>/dev/null || true
fi

# ── 创建虚拟环境 ────────────────────────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
    info "虚拟环境已存在: $VENV_DIR"
else
    info "创建虚拟环境: $VENV_DIR"
    $PYTHON -m venv "$VENV_DIR" || fail "创建虚拟环境失败（可能缺少 python3-venv，请先安装）"
fi

# ── 安装依赖 ────────────────────────────────────────────────────────────────────
info "安装依赖..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -U pip setuptools wheel -q 2>/dev/null || true
pip install -r requirements.txt -q || fail "安装 requirements.txt 失败"
pip install -e . -q || fail "pip install -e . 失败"
ok "依赖安装完成"

# ── 生成 /usr/local/bin/sml 包装脚本 ──────────────────────────────────────────
info "生成 sml 命令..."

$SUDO $PYTHON - "$VENV_DIR" "$BIN_SML" << 'PYEOF'
import sys, os, stat

venv_dir   = sys.argv[1]
bin_sml    = sys.argv[2]
venv_python = os.path.join(venv_dir, "bin", "python")

content = (
    "#!/usr/bin/env bash\n"
    f"# SML 启动脚本 - 由 install.sh 自动生成\n"
    f"exec \"{venv_python}\" -m sml \"$@\"\n"
)

with open(bin_sml, "w") as f:
    f.write(content)
os.chmod(bin_sml, os.stat(bin_sml).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print(f"已生成: {bin_sml}")
PYEOF

ok "已安装: $BIN_SML"

# ── 安装内置 mefrpc ─────────────────────────────────────────────────────────────
info "安装内置 mefrpc..."
"$VENV_DIR/bin/python" -c "from sml.installer import install; print(install())" 2>/dev/null || ok "mefrpc 安装跳过（首次启动时会自动安装）"

# ── 完成 ────────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}\n"
printf "${GREEN}║  SML 安装完成！                                          ║${NC}\n"
printf "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}\n"
printf "${GREEN}║  启动:  ${NC}sml                                           ║\n"
printf "${GREEN}║  安装 mefrpc:  ${NC}sml install                             ║\n"
printf "${GREEN}║  安装目录:  ${NC}$INSTALL_DIR                 ║\n"
printf "${GREEN}║  更新:  ${NC}cd $INSTALL_DIR && git pull && bash install.sh║\n"
printf "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
