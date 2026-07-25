#!/usr/bin/env bash
# ITML 一键无人值守安装脚本
# 用法: bash onekeyinstall.sh
# 从 http://scm.closefrp.com/itml/onekeyinstall.sh 下载后自动执行
# 支持: Debian/Ubuntu/CentOS/RHEL/Rocky/AlmaLinux/Arch

set -e

# ── 配置 ────────────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/zqamemz/Immortal-TUI-MEFrp-Launcher.git"
INSTALL_DIR="/opt/sml"
VENV_DIR="$INSTALL_DIR/venv"
BIN_SML="/usr/local/bin/sml"
BIN_SML_INSTALL="/usr/local/bin/sml-install"

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

# ── 检测包管理器 ────────────────────────────────────────────────────────────────
info "检测系统环境..."
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt";    SUDO="sudo"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf";    SUDO="sudo"
elif command -v yum &>/dev/null; then
    PKG_MGR="yum";    SUDO="sudo"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"; SUDO="sudo"
elif command -v apk &>/dev/null; then
    PKG_MGR="apk";    SUDO="sudo"
else
    PKG_MGR="unknown"; SUDO=""
fi
info "系统包管理器: $PKG_MGR"

# ── 系统级依赖安装 ──────────────────────────────────────────────────────────────
# 包含: 基础工具 + Python + venv + pip + 编译/运行时系统库（解决环境库缺失）
install_system_deps() {
    case "$PKG_MGR" in
        apt)
            $SUDO apt-get update -qq
            $SUDO apt-get install -y \
                git curl \
                python3 python3-venv python3-pip python3-dev \
                python3-full \
                gcc build-essential \
                libncursesw5-dev libffi-dev libssl-dev \
                pkg-config
            ;;
        dnf)
            $SUDO dnf install -y \
                git curl \
                python3 python3-pip python3-devel \
                gcc gcc-c++ make \
                ncurses-devel libffi-devel openssl-devel \
                pkgconfig
            ;;
        yum)
            $SUDO yum install -y \
                git curl \
                python3 python3-pip python3-devel \
                gcc gcc-c++ make \
                ncurses-devel libffi-devel openssl-devel \
                pkgconfig
            ;;
        pacman)
            $SUDO pacman -Sy --noconfirm \
                git curl \
                python python-pip \
                gcc make \
                ncurses libffi openssl
            ;;
        apk)
            $SUDO apk add --no-cache \
                git curl \
                python3 py3-pip \
                gcc g++ make musl-dev \
                ncurses-dev libffi-dev openssl-dev \
                linux-headers
            ;;
        *)
            warn "未知包管理器，跳过系统依赖自动安装。请手动确认 python3 / venv / pip 可用。"
            ;;
    esac
}

# ── 确保基础工具可用 ────────────────────────────────────────────────────────────
ensure_tool() {
    local tool="$1"; local pkg="$2"
    if ! command -v "$tool" &>/dev/null; then
        info "缺少 $tool，尝试安装..."
        install_system_deps
    fi
}

# 先确保 git 和 python3 存在
if ! command -v git &>/dev/null || ! command -v python3 &>/dev/null; then
    info "缺少核心依赖 (git/python3)，执行系统依赖安装..."
    install_system_deps
fi

# 再次确认
command -v git &>/dev/null     || fail "git 未安装，请手动安装后重试。"
command -v python3 &>/dev/null || fail "python3 未安装，请手动安装后重试。"

PYTHON="python3"
PYTHON_VERSION=$($PYTHON --version 2>&1)
info "Python: $PYTHON_VERSION"

MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]; }; then
    fail "Python 版本需要 >= 3.8，当前是 $MAJOR.$MINOR"
fi

# 确保 pip 模块可用（部分精简镜像没有 pip）
if ! $PYTHON -m pip --version &>/dev/null; then
    info "pip 不可用，尝试修复..."
    case "$PKG_MGR" in
        apt)    $SUDO apt-get update -qq && $SUDO apt-get install -y python3-pip ;;
        dnf|yum) $SUDO $PKG_MGR install -y python3-pip ;;
        pacman) $SUDO pacman -Sy --noconfirm python-pip ;;
        apk)    $SUDO apk add --no-cache py3-pip ;;
        *)
            # 最后手段: get-pip.py
            curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
                && $SUDO $PYTHON /tmp/get-pip.py --user || warn "pip 修复失败"
            ;;
    esac
fi

# ── 克隆/更新项目 ──────────────────────────────────────────────────────────────
info "准备安装目录: $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
    info "项目已存在，执行 git pull 更新..."
    cd "$INSTALL_DIR"
    git pull --ff-only || warn "git pull 失败，继续安装..."
else
    info "克隆项目..."
    $SUDO mkdir -p "$(dirname "$INSTALL_DIR")"
    $SUDO git clone "$REPO_URL" "$INSTALL_DIR" \
        || fail "克隆失败，请检查网络连接。"
    cd "$INSTALL_DIR"
fi

# 确保当前用户对安装目录有写权限（如果不是 root 运行）
if [ ! -w "$INSTALL_DIR" ] && [ "$(id -u)" -ne 0 ]; then
    info "当前用户无写权限，修改目录权限..."
    $SUDO chown -R "$(id -u):$(id -g)" "$INSTALL_DIR"
fi

# ── 创建虚拟环境（带多重回退）─────────────────────────────────────────────────
create_venv() {
    if [ -d "$VENV_DIR" ]; then
        info "虚拟环境已存在: $VENV_DIR"
        return 0
    fi

    info "创建虚拟环境: $VENV_DIR"

    # 方法 1: 标准 venv
    if $PYTHON -m venv "$VENV_DIR" 2>/dev/null; then
        ok "venv 创建成功"
        return 0
    fi
    warn "venv 创建失败（可能缺少 python3-venv），尝试修复..."

    # 修复: 安装 venv 包
    case "$PKG_MGR" in
        apt)    $SUDO apt-get update -qq && $SUDO apt-get install -y python3-venv python3-full ;;
        dnf|yum) $SUDO $PKG_MGR install -y python3-virtualenv ;;
        pacman) $SUDO pacman -Sy --noconfirm python-virtualenv ;;
        apk)    $SUDO apk add --no-cache py3-virtualenv ;;
    esac

    # 方法 2: 重试 venv
    if $PYTHON -m venv "$VENV_DIR" 2>/dev/null; then
        ok "venv 创建成功 (重试)"
        return 0
    fi

    # 方法 3: 使用 virtualenv (pip)
    info "尝试使用 virtualenv..."
    $PYTHON -m pip install --user -q virtualenv 2>/dev/null || $SUDO $PYTHON -m pip install -q virtualenv
    if command -v virtualenv &>/dev/null && virtualenv "$VENV_DIR" 2>/dev/null; then
        ok "virtualenv 创建成功"
        return 0
    fi

    # 方法 4: 让 pip 安装 virtualenv 后重试
    if $PYTHON -m pip install -q virtualenv 2>/dev/null && "$VENV_DIR/../bin/virtualenv" "$VENV_DIR" 2>/dev/null; then
        ok "virtualenv 创建成功 (pip)"
        return 0
    fi

    return 1
}

create_venv || fail "无法创建虚拟环境，请手动检查系统依赖（python3-venv / gcc / make）"

# ── 安装 Python 依赖 ────────────────────────────────────────────────────────────
info "安装 Python 依赖..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 升级 pip / setuptools（避免构建工具过旧导致编译失败）
pip install -U pip setuptools wheel -q 2>/dev/null || true

# 安装项目依赖
pip install -r requirements.txt -q || fail "安装 requirements.txt 失败"
pip install -e . -q || fail "pip install -e . 失败"

ok "依赖安装完成"

# ── 生成 /usr/local/bin/sml 包装脚本 ──────────────────────────────────────────
info "生成 sml 命令..."

$PYTHON - "$VENV_DIR" "$BIN_SML" << 'PYEOF'
import sys, os, stat

venv_dir   = sys.argv[1]
bin_sml    = sys.argv[2]
venv_python = os.path.join(venv_dir, "bin", "python")

content = (
    "#!/usr/bin/env bash\n"
    f"# ITML 启动脚本 - 由 onekeyinstall.sh 自动生成\n"
    f"exec \"{venv_python}\" -m sml \"$@\"\n"
)

with open(bin_sml, "w") as f:
    f.write(content)
os.chmod(bin_sml, os.stat(bin_sml).st_mode | stat.S_IEXEC)
print(f"已生成: {bin_sml}")
PYEOF

ok "已安装: $BIN_SML"

# ── 安装 mefrpc ─────────────────────────────────────────────────────────────────
info "安装内置 mefrpc..."
"$VENV_DIR/bin/python" -c "from sml.installer import install; print(install())" 2>/dev/null || ok "mefrpc 安装跳过（首次启动时会自动安装）"

# ── 完成 ────────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}\n"
printf "${GREEN}║  ITML 安装完成！                                          ║${NC}\n"
printf "${GREEN}╠══════════════════════════════════════════════════════════════════╣${NC}\n"
printf "${GREEN}║  启动:  ${NC}sml                                           ║\n"
printf "${GREEN}║  安装目录:  ${NC}$INSTALL_DIR                 ║\n"
printf "${GREEN}║  更新:  ${NC}cd $INSTALL_DIR && git pull && bash onekeyinstall.sh║\n"
printf "${GREEN}║  卸载:  ${NC}rm -rf $INSTALL_DIR $BIN_SML       ║\n"
printf "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"
echo ""

# ── 启动引导 ────────────────────────────────────────────────────────────────────
printf "${CYAN}是否现在启动 ITML？[Y/n] ${NC}"
if [ -t 0 ]; then
    read -r START_NOW
else
    START_NOW="y"
fi
if [[ "$START_NOW" =~ ^[Nn]$ ]]; then
    info "跳过启动。下次运行 sml 即可启动。"
    exit 0
fi

info "启动 ITML..."
exec "$BIN_SML"
