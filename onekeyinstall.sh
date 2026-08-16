#!/usr/bin/env bash
# ============================================================================
# ITML 一键无人值守安装脚本
#
# 用法:
#   bash onekeyinstall.sh                              # 交互式安装
#   bash onekeyinstall.sh -y                           # 全自动无人值守安装
#   bash onekeyinstall.sh -y -d /usr/local/sml         # 自定义安装目录
#   curl -fsSL <URL> | bash                            # 管道方式无人值守安装
#
# 支持系统（自动检测，从全新系统到 SML 部署完成全程无人值守）:
#   Debian/Ubuntu 系 (apt)    Debian / Ubuntu / Linux Mint / Kali / ...
#   RHEL/CentOS 系 (yum/dnf)  CentOS 7/8/9 / RHEL / Rocky / AlmaLinux / Fedora / ...
#     - CentOS 7/8 已 EOL: 自动修复为 vault.centos.org 归档源
#     - CentOS 7 / RHEL 8 默认 Python < 3.8: 自动编译 Python 3.11（含 OpenSSL 1.1.1）
#     - CentOS 9 / Rocky 9 / AlmaLinux 9: 系统自带 Python 3.9，开箱即用
#   Arch 系 (pacman)          Arch / Manjaro / EndeavourOS / ...
#   Alpine (apk)
#
# 环境变量（可选）:
#   REPO_URL          项目仓库地址
#   BRANCH            克隆分支
#   LOG_FILE          日志文件路径 (默认 /tmp/onekeyinstall.log)
#   PY_MIRROR         Python 源码下载镜像 (默认华为云; 官方: https://www.python.org/ftp/python)
#   PYTHON_BUILD_VER  需要编译时使用的 Python 版本 (默认 3.11.9)
#   OPENSSL_BUILD_VER 需要编译时使用的 OpenSSL 版本 (默认 1.1.1w)
#   NO_COLOR          设为任意值禁用彩色输出
# ============================================================================

set -euo pipefail

# ── 默认配置 ────────────────────────────────────────────────────────────────
REPO_URL="${REPO_URL:-https://github.com/zqamemz/Immortal-TUI-MEFrp-Launcher.git}"
BRANCH="${BRANCH:-main}"
DEFAULT_INSTALL_DIR="/opt/sml"
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
BIN_SML="/usr/local/bin/sml"
LOG_FILE="${LOG_FILE:-/tmp/onekeyinstall.log}"
PY_MIRROR="${PY_MIRROR:-https://mirrors.huaweicloud.com/python}"
PYTHON_BUILD_VER="${PYTHON_BUILD_VER:-3.11.9}"
OPENSSL_BUILD_VER="${OPENSSL_BUILD_VER:-1.1.1w}"

START_MODE="ask"          # ask | yes | no
PYTHON=""
BUILT_PYTHON=""
CORES="$(nproc 2>/dev/null || echo 2)"
export PYTHONUTF8=1

# ── 颜色输出（非终端自动禁用）───────────────────────────────────────────────
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; NC=''
fi

info()  { printf "${CYAN}[INFO]${NC} %s\n" "$*";  printf '[INFO] %s\n' "$*" >> "$LOG_FILE"; }
ok()    { printf "${GREEN}[OK]${NC}   %s\n" "$*"; printf '[OK]   %s\n' "$*" >> "$LOG_FILE"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$*"; printf '[WARN] %s\n' "$*" >> "$LOG_FILE"; }
fail()  { printf "${RED}[FAIL]${NC} %s\n" "$*"; printf '[FAIL] %s\n' "$*" >> "$LOG_FILE"; exit 1; }

# ── 帮助 ─────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
ITML 一键无人值守安装脚本
从全新系统开始，自动检测发行版并安装依赖，最终部署 SML。

用法:
    bash onekeyinstall.sh [选项] [安装目录]

选项:
    -d, --install-dir DIR   安装目录 (默认 $DEFAULT_INSTALL_DIR)
    -r, --repo URL          项目仓库地址 (默认 $REPO_URL)
    -b, --branch BRANCH     克隆分支 (默认 $BRANCH)
    -y, --yes               全自动模式: 不询问任何问题, 安装后不启动
        --start             安装完成后自动启动 SML
        --no-start          安装完成后不启动 SML (覆盖 --start)
    -h, --help              显示本帮助

示例:
    bash onekeyinstall.sh                    # 交互安装, 默认 /opt/sml
    bash onekeyinstall.sh /usr/local/sml     # 自定义安装目录
    bash onekeyinstall.sh -y                 # 无人值守全自动安装
    curl -fsSL <URL> | bash                  # 管道无人值守安装
EOF
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            -d|--install-dir)
                [ $# -ge 2 ] || { warn "选项 $1 需要一个参数"; usage; exit 1; }
                INSTALL_DIR="$2"; shift 2 ;;
            -r|--repo)
                [ $# -ge 2 ] || { warn "选项 $1 需要一个参数"; usage; exit 1; }
                REPO_URL="$2"; shift 2 ;;
            -b|--branch)
                [ $# -ge 2 ] || { warn "选项 $1 需要一个参数"; usage; exit 1; }
                BRANCH="$2"; shift 2 ;;
            -y|--yes)         START_MODE="no"; shift ;;
            --start)          START_MODE="yes"; shift ;;
            --no-start)       START_MODE="no"; shift ;;
            -h|--help)        usage; exit 0 ;;
            -*)
                warn "未知选项: $1"
                usage
                exit 1
                ;;
            *)
                INSTALL_DIR="$1"; shift ;;
        esac
    done
}

# ── 工具函数 ─────────────────────────────────────────────────────────────────
detect_sudo() {
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=""
    elif command -v sudo &>/dev/null; then
        SUDO="sudo"
    else
        warn "当前用户无 root 权限且未找到 sudo，系统依赖安装可能失败"
        SUDO=""
    fi
}

retry() {
    local n=3 i
    for i in 1 2 3; do
        if "$@"; then
            return 0
        fi
        warn "命令失败: $* （第 $i 次重试）"
        sleep 3
    done
    return 1
}

# ── 系统检测 ─────────────────────────────────────────────────────────────────
detect_os() {
    OS_ID="unknown"; OS_ID_LIKE=""; OS_FAMILY="unknown"; OS_VERSION_ID=""
    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        OS_ID="${ID:-unknown}"
        OS_ID_LIKE="${ID_LIKE:-}"
        OS_VERSION_ID="${VERSION_ID:-}"
    fi

    case "$OS_ID $OS_ID_LIKE" in
        *debian*|*ubuntu*|*raspbian*|*linuxmint*|*kali*|*pop*|*elementary*|*deepin*|*uos*)
            OS_FAMILY="debian" ;;
        *centos*|*rhel*|*rocky*|*almalinux*|*fedora*|*ol*|*amzn*|*anolis*|*opencloudos*|*tencentos*|*alibaba*|*openeuler*|*euleros*|*sangfor*)
            OS_FAMILY="rhel" ;;
        *arch*|*manjaro*|*endeavouros*|*cachyos*|*artix*|*garuda*)
            OS_FAMILY="arch" ;;
        *alpine*)
            OS_FAMILY="alpine" ;;
        *)
            # 兜底: 按可用的包管理器判断
            if command -v apt-get &>/dev/null; then OS_FAMILY="debian"
            elif command -v dnf &>/dev/null; then OS_FAMILY="rhel"
            elif command -v yum &>/dev/null; then OS_FAMILY="rhel"
            elif command -v pacman &>/dev/null; then OS_FAMILY="arch"
            elif command -v apk &>/dev/null; then OS_FAMILY="alpine"
            fi
            ;;
    esac

    # RHEL 系主版本（7=CentOS7 8=RHEL8系 9+=RHEL9系/Fedora）
    RHEL_MAJOR=0
    if [ "$OS_FAMILY" = "rhel" ]; then
        RHEL_MAJOR=$(printf '%s' "$OS_VERSION_ID" | cut -d. -f1 | tr -dc '0-9' || true)
        [ -n "$RHEL_MAJOR" ] || RHEL_MAJOR=0
    fi

    info "检测到系统: ${OS_ID:-未知} ${OS_VERSION_ID:-} (发行版家族: $OS_FAMILY)"
    [ "$OS_FAMILY" != "unknown" ] || warn "未能识别发行版，将跳过系统依赖自动安装，请手动确保 git/python3/venv/pip 可用"
}

# ── Python 3.8+ 检查与选择 ───────────────────────────────────────────────────
python_ok() {
    local cmd="$1"
    [ -n "$cmd" ] || return 1
    command -v "$cmd" &>/dev/null || return 1
    local v major minor
    v=$("$cmd" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null) || return 1
    major=${v%%.*}
    minor=${v#*.}; minor=${minor%%.*}
    if [ "$major" -gt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; }; then
        return 0
    fi
    return 1
}

find_python() {
    local cmd
    for cmd in python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
        if command -v "$cmd" &>/dev/null; then
            if python_ok "$cmd"; then
                PYTHON="$cmd"
                return 0
            fi
            warn "检测到 $cmd 但版本低于 3.8，跳过"
        fi
    done
    return 1
}

# ── 编译 OpenSSL 1.1.1（CentOS 7 自带的 1.0.2 无法编译 Python 3.11）─────────
build_openssl() {
    if [ -x /usr/local/openssl/bin/openssl ]; then
        info "OpenSSL 已编译安装于 /usr/local/openssl，跳过"
        return 0
    fi
    info "编译 OpenSSL $OPENSSL_BUILD_VER（CentOS 7 自带的 1.0.2 过旧，Python 3.11 需要 1.1.1+）..."
    local tgz="/tmp/openssl-$OPENSSL_BUILD_VER.tar.gz"
    local url="https://www.openssl.org/source/old/1.1.1/openssl-$OPENSSL_BUILD_VER.tar.gz"
    retry curl -fsSL "$url" -o "$tgz" || fail "下载 OpenSSL 失败: $url"
    rm -rf "/tmp/openssl-$OPENSSL_BUILD_VER"
    tar xzf "$tgz" -C /tmp || fail "解压 OpenSSL 源码失败"
    cd "/tmp/openssl-$OPENSSL_BUILD_VER"
    ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl shared zlib \
        || fail "OpenSSL 配置失败"
    make -j"$CORES" || fail "OpenSSL 编译失败"
    $SUDO make install || fail "OpenSSL 安装失败"
    $SUDO sh -c 'echo /usr/local/openssl/lib > /etc/ld.so.conf.d/openssl-1.1.conf && ldconfig' \
        || warn "ldconfig 配置失败（Python 编译将使用 --with-openssl 显式指定）"
    ok "OpenSSL $OPENSSL_BUILD_VER 编译完成"
}

# ── 编译 Python（系统没有 3.8+ 时的回退方案）────────────────────────────────
build_python() {
    local ver="$PYTHON_BUILD_VER"
    local prefix="/usr/local/python-$ver"
    local openssl_arg=""

    # 已编译过则直接复用
    BUILT_PYTHON=$(ls "$prefix"/bin/python3.* 2>/dev/null | head -1 || true)
    if [ -n "$BUILT_PYTHON" ]; then
        info "Python 已编译安装于 $prefix，跳过编译"
        return 0
    fi

    if [ -x /usr/local/openssl/bin/openssl ]; then
        openssl_arg="--with-openssl=/usr/local/openssl"
    fi

    info "编译 Python $ver（源码: $PY_MIRROR/$ver/）..."
    local tgz="/tmp/Python-$ver.tgz"
    retry curl -fsSL "$PY_MIRROR/$ver/Python-$ver.tgz" -o "$tgz" \
        || fail "下载 Python 源码失败: $PY_MIRROR/$ver/Python-$ver.tgz"
    rm -rf "/tmp/Python-$ver"
    tar xzf "$tgz" -C /tmp || fail "解压 Python 源码失败"
    cd "/tmp/Python-$ver"
    # shellcheck disable=SC2086
    ./configure \
        --prefix="$prefix" \
        --with-ensurepip=install \
        --with-system-ffi \
        $openssl_arg \
        || fail "Python 配置失败（缺少编译依赖? 请检查 gcc/make/openssl-devel/libffi-devel）"
    make -j"$CORES" || fail "Python 编译失败（内存不足可尝试: CORES=1 bash onekeyinstall.sh）"
    $SUDO make altinstall || fail "Python 安装失败"
    $SUDO ldconfig 2>/dev/null || true

    BUILT_PYTHON=$(ls "$prefix"/bin/python3.* 2>/dev/null | head -1 || true)
    [ -n "$BUILT_PYTHON" ] || fail "Python 编译产物未找到: $prefix"
    ok "Python $ver 编译安装完成: $BUILT_PYTHON"
}

# 确保获得可用的 Python 3.8+（系统自带 → 系统模块 → 源码编译）
ensure_python() {
    if find_python; then
        return 0
    fi
    info "未找到 Python 3.8+，尝试安装/编译..."

    # RHEL 8 系: 系统默认 python3 为 3.6，优先启用 python39 模块
    if [ "$OS_FAMILY" = "rhel" ] && [ "$RHEL_MAJOR" -ge 8 ]; then
        info "尝试通过 dnf 模块启用 python39..."
        $SUDO dnf module enable -y python39 2>/dev/null || warn "dnf 启用 python39 模块失败（将回退源码编译）"
        $SUDO dnf install -y python39 python39-pip python39-devel 2>/dev/null || warn "python39 安装失败（将回退源码编译）"
        if find_python; then
            return 0
        fi
    fi

    # 源码编译（CentOS 7 需先编译 OpenSSL 1.1.1）
    if [ "$OS_FAMILY" = "rhel" ] && [ "$RHEL_MAJOR" -le 7 ]; then
        build_openssl
    fi
    build_python

    if python_ok "$BUILT_PYTHON"; then
        PYTHON="$BUILT_PYTHON"
        return 0
    fi
    return 1
}

# ── 修复已 EOL 的 CentOS 7 / CentOS 8 官方源 ────────────────────────────────
fix_eol_repos() {
    case "$OS_ID" in
        centos)
            if [ "$RHEL_MAJOR" -eq 7 ]; then
                if grep -rl "mirrorlist.centos.org" /etc/yum.repos.d/*.repo 2>/dev/null | grep -q .; then
                    info "CentOS 7 已停止维护，将 yum 源切换为 vault.centos.org (7.9.2009)..."
                    cat > /tmp/CentOS-Base.repo << 'EOF'
[base]
name=CentOS-$releasever - Base
baseurl=https://vault.centos.org/7.9.2009/os/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1

[updates]
name=CentOS-$releasever - Updates
baseurl=https://vault.centos.org/7.9.2009/updates/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1

[extras]
name=CentOS-$releasever - Extras
baseurl=https://vault.centos.org/7.9.2009/extras/$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
enabled=1
EOF
                    $SUDO cp /tmp/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo
                    ok "yum 源已切换为 vault.centos.org"
                fi
            elif [ "$RHEL_MAJOR" -eq 8 ]; then
                if grep -rl "mirrorlist.centos.org\|mirror.stream.centos.org\|^baseurl=http://mirror.centos.org" /etc/yum.repos.d/*.repo 2>/dev/null | grep -q .; then
                    info "CentOS 8 已停止维护，将 dnf 源切换为 vault.centos.org (8.5.2111)..."
                    cat > /tmp/CentOS-Base.repo << 'EOF'
[baseos]
name=CentOS-$releasever - BaseOS
baseurl=https://vault.centos.org/8.5.2111/BaseOS/$basearch/os/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-8
enabled=1

[appstream]
name=CentOS-$releasever - AppStream
baseurl=https://vault.centos.org/8.5.2111/AppStream/$basearch/os/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-8
enabled=1

[extras]
name=CentOS-$releasever - Extras
baseurl=https://vault.centos.org/8.5.2111/extras/$basearch/os/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-8
enabled=1
EOF
                    $SUDO cp /tmp/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo
                    ok "dnf 源已切换为 vault.centos.org"
                fi
            fi
            ;;
    esac
}

# ── 系统依赖安装（按发行版族）───────────────────────────────────────────────
install_system_deps() {
    info "安装系统依赖..."
    case "$OS_FAMILY" in
        debian)
            export DEBIAN_FRONTEND=noninteractive
            if ! $SUDO apt-get update -qq; then
                warn "apt-get update 失败（网络或源问题），继续尝试安装..."
            fi
            retry $SUDO apt-get install -y --no-install-recommends \
                git curl ca-certificates \
                python3 python3-venv python3-pip python3-dev python3-full \
                gcc build-essential \
                libncursesw5-dev libffi-dev libssl-dev pkg-config \
                || fail "apt 安装系统依赖失败"
            # 兼容新版系统的 ncurses 开发包名称
            $SUDO apt-get install -y --no-install-recommends libncurses-dev 2>/dev/null || true
            ;;
        rhel)
            install_rhel_deps ;;
        arch)
            retry $SUDO pacman -Sy --noconfirm \
                git curl ca-certificates \
                python python-pip \
                gcc make \
                ncurses libffi openssl \
                || fail "pacman 安装系统依赖失败"
            ;;
        alpine)
            $SUDO apk add --no-cache \
                git curl ca-certificates \
                python3 py3-pip py3-virtualenv \
                gcc g++ make musl-dev \
                ncurses-dev libffi-dev openssl-dev \
                linux-headers \
                || fail "apk 安装系统依赖失败"
            ;;
        *)
            warn "未知系统家族，跳过系统依赖自动安装。请手动确保 git / python3 / venv / pip 可用。"
            ;;
    esac
}

install_rhel_deps() {
    fix_eol_repos

    local common="git curl ca-certificates python3 python3-pip python3-devel \
                  gcc gcc-c++ make \
                  ncurses-devel libffi-devel openssl-devel pkgconfig"

    case "$RHEL_MAJOR" in
        7)
            # CentOS 7: 系统仅有 python2，此处只安装编译工具链
            $SUDO yum install -y \
                git curl ca-certificates \
                gcc gcc-c++ make perl \
                zlib-devel bzip2-devel readline-devel sqlite-devel \
                libffi-devel ncurses-devel openssl-devel \
                || fail "yum 安装编译工具链失败"
            $SUDO yum install -y glibc-common 2>/dev/null || true
            ;;
        8)
            if ! $SUDO dnf install -y $common; then
                warn "dnf 安装失败，启用 EPEL 后重试..."
                $SUDO dnf install -y epel-release || true
                $SUDO dnf install -y $common || fail "dnf 安装系统依赖失败"
            fi
            $SUDO dnf install -y glibc-langpack-en 2>/dev/null || true
            ;;
        *)
            # RHEL 9 / CentOS Stream 9 / Rocky 9 / AlmaLinux 9 / Fedora
            if ! $SUDO dnf install -y $common; then
                warn "dnf 安装失败，启用 EPEL 后重试..."
                $SUDO dnf install -y epel-release || true
                $SUDO dnf install -y $common || fail "dnf 安装系统依赖失败"
            fi
            $SUDO dnf install -y glibc-langpack-en 2>/dev/null || true
            ;;
    esac
}

# ── 克隆 / 更新项目 ──────────────────────────────────────────────────────────
clone_project() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "项目已存在，执行 git pull 更新..."
        cd "$INSTALL_DIR"
        if ! git pull --ff-only 2>/dev/null; then
            warn "git pull 失败，尝试重置到远端最新..."
            git fetch --all 2>/dev/null && git reset --hard "origin/$BRANCH" 2>/dev/null \
                || warn "重置失败，继续使用现有代码"
        fi
    else
        info "克隆项目 $REPO_URL (分支: $BRANCH)..."
        $SUDO mkdir -p "$(dirname "$INSTALL_DIR")"
        if retry $SUDO git clone -b "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"; then
            ok "项目克隆完成"
        else
            warn "git clone 失败（git 版本过旧或网络问题），回退为下载源码包..."
            local tgz_url="${REPO_URL%.git}/archive/refs/heads/$BRANCH.tar.gz"
            local tgz="/tmp/itml-src.tar.gz"
            retry curl -fsSL "$tgz_url" -o "$tgz" || fail "源码下载失败: $tgz_url"
            $SUDO mkdir -p "$INSTALL_DIR"
            tar xzf "$tgz" -C /tmp || fail "解压源码失败"
            $SUDO cp -rf /tmp/Immortal-TUI-MEFrp-Launcher-*/. "$INSTALL_DIR"/ || fail "复制源码失败"
            ok "项目源码已下载（非 git 方式，更新时重新执行本脚本即可）"
        fi
        cd "$INSTALL_DIR"
    fi

    # 非 root 运行时下放目录权限，避免后续 pip 写入失败
    if [ "$(id -u)" -ne 0 ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$INSTALL_DIR" 2>/dev/null || true
    fi
    # 标记 tarball 安装方式（更新提示用）
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        touch "$INSTALL_DIR/.tarball-install" 2>/dev/null || true
    fi
}

# ── 创建虚拟环境（多重回退）──────────────────────────────────────────────────
create_venv() {
    if [ -d "$VENV_DIR" ]; then
        info "虚拟环境已存在: $VENV_DIR"
        return 0
    fi
    info "创建虚拟环境: $VENV_DIR"

    if "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null; then
        ok "虚拟环境创建成功"
        return 0
    fi
    warn "标准 venv 创建失败，尝试修复..."

    case "$OS_FAMILY" in
        debian) $SUDO apt-get install -y python3-venv python3-full 2>/dev/null || true ;;
        rhel)   $SUDO dnf install -y python3-virtualenv 2>/dev/null || $SUDO yum install -y python3-virtualenv 2>/dev/null || true ;;
        arch)   $SUDO pacman -Sy --noconfirm python-virtualenv 2>/dev/null || true ;;
        alpine) $SUDO apk add --no-cache py3-virtualenv 2>/dev/null || true ;;
    esac

    if "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null; then
        ok "虚拟环境创建成功（修复后）"
        return 0
    fi

    info "尝试使用 virtualenv 创建..."
    "$PYTHON" -m pip install --user -q virtualenv 2>/dev/null || true
    if "$PYTHON" -m virtualenv "$VENV_DIR" 2>/dev/null; then
        ok "virtualenv 创建成功"
        return 0
    fi

    return 1
}

# ── 安装 Python 依赖 ─────────────────────────────────────────────────────────
install_python_deps() {
    info "安装 Python 依赖..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"

    pip install -U pip setuptools wheel -q 2>/dev/null || true
    retry pip install -r requirements.txt -q || fail "安装 requirements.txt 失败"
    pip install -e . -q || fail "pip install -e . 失败（缺少编译工具? 请检查 gcc/make/python3-dev）"
    ok "Python 依赖安装完成"
}

# ── 生成 sml 启动命令 ────────────────────────────────────────────────────────
generate_launcher() {
    info "生成 sml 启动命令..."
    $SUDO "$PYTHON" - "$VENV_DIR" "$BIN_SML" << 'PYEOF'
import sys, os, stat

venv_dir    = sys.argv[1]
bin_sml     = sys.argv[2]
venv_python = os.path.join(venv_dir, "bin", "python")

content = (
    "#!/usr/bin/env bash\n"
    "# ITML 启动脚本 - 由 onekeyinstall.sh 自动生成\n"
    "export PYTHONUTF8=1\n"
    f"exec \"{venv_python}\" -m sml \"$@\"\n"
)

with open(bin_sml, "w") as f:
    f.write(content)
os.chmod(bin_sml, os.stat(bin_sml).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print("已生成: " + bin_sml)
PYEOF
    ok "已安装启动命令: $BIN_SML"
}

# ── 安装内置 mefrpc ──────────────────────────────────────────────────────────
install_mefrpc() {
    info "安装内置 mefrpc..."
    if "$VENV_DIR/bin/python" -c "from sml.installer import is_installed; raise SystemExit(0 if is_installed() else 1)" 2>/dev/null; then
        ok "mefrpc 已安装"
    else
        if "$VENV_DIR/bin/python" -c "from sml.installer import install; ok, msg = install(); print(msg); raise SystemExit(0 if ok else 1)" 2>/dev/null; then
            ok "mefrpc 安装完成"
        else
            warn "mefrpc 安装失败（首次启动 sml 时会自动重试安装）"
        fi
    fi
}

# ── 验证安装 ─────────────────────────────────────────────────────────────────
verify_install() {
    info "验证安装..."
    local ver
    ver=$("$VENV_DIR/bin/python" -c "import sml; print(sml.__version__)" 2>/dev/null) || fail "SML 导入失败，安装可能不完整"
    ok "SML 版本: $ver"

    local mefrpc_path
    mefrpc_path=$("$VENV_DIR/bin/python" -c "from sml.installer import get_install_path; print(get_install_path())" 2>/dev/null || true)
    if [ -n "$mefrpc_path" ] && [ -x "$mefrpc_path" ]; then
        ok "mefrpc: $mefrpc_path"
    else
        warn "mefrpc 尚未就绪（首次启动 sml 时会自动安装）"
    fi

    [ -x "$BIN_SML" ] && ok "sml 命令可用: $BIN_SML" || warn "sml 命令生成失败: $BIN_SML"
}

# ── 完成输出与启动 ───────────────────────────────────────────────────────────
finish() {
    echo ""
    cat <<EOF
${GREEN}╔════════════════════════════════════════════════════════════════════════╗${NC}
${GREEN}║  ITML 安装完成！                                                ║${NC}
${GREEN}╠════════════════════════════════════════════════════════════════════════╣${NC}
${GREEN}║  启动: sml                                                          ║${NC}
${GREEN}║  安装目录: $INSTALL_DIR                                          ║${NC}
${GREEN}║  日志: $LOG_FILE                                            ║${NC}
${GREEN}║  更新: cd $INSTALL_DIR && git pull && bash onekeyinstall.sh${NC}${GREEN}║${NC}
${GREEN}║  卸载: rm -rf $INSTALL_DIR $BIN_SML                          ║${NC}
${GREEN}╚════════════════════════════════════════════════════════════════════════╝${NC}
EOF
    echo ""

    if [ "$START_MODE" = "yes" ]; then
        info "启动 SML..."
        exec "$BIN_SML"
    elif [ "$START_MODE" = "ask" ] && [ -t 0 ]; then
        printf "${CYAN}是否现在启动 SML？[y/N] ${NC}"
        if read -r START_NOW && [[ "$START_NOW" =~ ^[Yy]$ ]]; then
            info "启动 SML..."
            exec "$BIN_SML"
        fi
        info "跳过启动。随时运行 sml 即可启动。"
    else
        info "无人值守模式，跳过启动。随时运行 sml 即可启动。"
    fi
}

# ── 主流程 ───────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"
    VENV_DIR="$INSTALL_DIR/venv"

    # 确保日志文件可用
    touch "$LOG_FILE" 2>/dev/null || LOG_FILE="/tmp/onekeyinstall.log"

    detect_sudo
    detect_os

    info "安装目录: $INSTALL_DIR"
    info "日志文件: $LOG_FILE"

    # 1. 系统依赖（缺少核心工具时自动安装）
    local needs_deps=0
    command -v git &>/dev/null     || needs_deps=1
    command -v curl &>/dev/null    || needs_deps=1
    command -v python3 &>/dev/null || needs_deps=1
    if [ "$needs_deps" -eq 1 ]; then
        install_system_deps
    else
        info "核心工具 (git/curl/python3) 已存在，跳过系统依赖安装"
    fi

    # 2. Python 3.8+（缺失或版本过低时自动安装/编译）
    ensure_python || fail "无法获得 Python 3.8+。请手动安装 Python 3.8+ 后重试。"
    info "使用 Python: $PYTHON ($("$PYTHON" --version 2>&1))"

    # 3. 克隆 / 更新项目
    clone_project

    # 4. 创建虚拟环境
    create_venv || fail "无法创建虚拟环境，请手动检查系统依赖（python3-venv / gcc / make）"

    # 5. 安装 Python 依赖
    install_python_deps

    # 6. 生成 sml 命令
    generate_launcher

    # 7. 安装 mefrpc
    install_mefrpc

    # 8. 验证
    verify_install

    # 9. 完成
    finish
}

main "$@"
