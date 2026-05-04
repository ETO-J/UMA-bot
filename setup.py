#!/usr/bin/env python3
"""
bopang 首次安装脚本
- 检测 Python 版本
- 创建虚拟环境（如不存在）
- 安装项目依赖
- 创建 .env 配置文件模板（如不存在）
- 创建必要的数据目录
"""
import sys
import os
import subprocess
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).absolute().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
ENV_TEMPLATE = PROJECT_ROOT / ".env.example"
ENV_FILE = PROJECT_ROOT / ".env"
DATA_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "data" / "knowledge_db",
    PROJECT_ROOT / "data" / "model_cache",
    PROJECT_ROOT / "data" / "aissetting",
    PROJECT_ROOT / "images",
    PROJECT_ROOT / "images" / "errors",
    PROJECT_ROOT / "pixiv_images",
    PROJECT_ROOT / "comfyui",
]

MIN_PYTHON = (3, 9)

# ─── 颜色输出 ───────────────────────────────────────
def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

if _supports_color():
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    GREEN = YELLOW = RED = CYAN = BOLD = RESET = ""

def info(msg):
    print(f"{CYAN}[INFO]{RESET} {msg}")

def ok(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")

def warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")


# ─── 步骤 ───────────────────────────────────────────
def check_python():
    """检查 Python 版本"""
    info(f"当前 Python: {sys.version}")
    if sys.version_info < MIN_PYTHON:
        fail(f"Python 版本过低！需要 >={MIN_PYTHON[0]}.{MIN_PYTHON[1]}，当前 {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    ok(f"Python 版本满足要求 (>={MIN_PYTHON[0]}.{MIN_PYTHON[1]})")


def find_venv_python():
    """查找虚拟环境中的 Python"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"


def create_venv():
    """创建虚拟环境"""
    venv_python = find_venv_python()
    if venv_python.exists():
        ok(f"虚拟环境已存在: {VENV_DIR}")
        return

    info("正在创建虚拟环境...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
        )
        ok(f"虚拟环境创建成功: {VENV_DIR}")
    except subprocess.CalledProcessError as e:
        fail(f"创建虚拟环境失败: {e}")
        sys.exit(1)


def install_dependencies():
    """安装项目依赖"""
    venv_python = find_venv_python()
    if not venv_python.exists():
        fail(f"虚拟环境 Python 不存在: {venv_python}")
        sys.exit(1)

    if not REQUIREMENTS.exists():
        fail(f"未找到 requirements.txt: {REQUIREMENTS}")
        sys.exit(1)

    info("正在安装项目依赖（可能需要几分钟）...")
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
        )
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            check=True,
        )
        ok("所有依赖安装完成！")
    except subprocess.CalledProcessError as e:
        fail(f"依赖安装失败: {e}")
        warn("你可以稍后手动运行: .venv/Scripts/python -m pip install -r requirements.txt")
        sys.exit(1)


def create_env_file():
    """创建 .env 配置文件模板"""
    if ENV_FILE.exists():
        ok(f".env 配置文件已存在，跳过")
        return

    template = """\
# ============================================================
# bopang 环境变量配置
# ============================================================
# 请根据实际情况填写以下配置项。
# 填写完成后保存，然后运行 bot 即可。
# ============================================================

# --- DeepSeek (AI 对话) ---
AICHATKEY1=your_deepseek_api_key_here

# --- 豆包 (视觉识别) ---
VIRSIONKEY1=your_doubao_api_key_here

# --- Bing 搜索 ---
BINGSEARCHKEY1=your_bing_search_api_key_here

# --- SauceNAO (识图) ---
SAUCENAO_API_KEY=your_saucenao_api_key_here

# --- Pixiv ---
PIXIV_REFRESH_TOKEN=your_pixiv_refresh_token_here
"""
    ENV_FILE.write_text(template, encoding="utf-8")
    ok(f"已创建 .env 配置模板，请编辑填写你的 API Key: {ENV_FILE}")
    warn("⚠️  请务必填写至少一个 AI 服务的 API Key，否则机器人无法正常工作！")


def create_data_dirs():
    """创建必要的数据目录"""
    for d in DATA_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    ok(f"数据目录已就绪")


def print_summary():
    """打印安装总结"""
    venv_python = find_venv_python()
    print()
    print(f"{BOLD}{'=' * 55}{RESET}")
    print(f"{BOLD}  bopang 安装完成！{RESET}")
    print(f"{BOLD}{'=' * 55}{RESET}")
    print()
    print("  接下来的步骤:")
    print()
    print(f"  1. 编辑 {YELLOW}.env{RESET} 文件，填写 API Key")
    print(f"  2. 启动机器人:")
    if sys.platform == "win32":
        print(f"     {GREEN}.venv\\Scripts\\python bot.py{RESET}")
    else:
        print(f"     {GREEN}.venv/bin/python bot.py{RESET}")
    print(f"     或:")
    if sys.platform == "win32":
        print(f"     {GREEN}.venv\\Scripts\\activate && nb run{RESET}")
    else:
        print(f"     {GREEN}source .venv/bin/activate && nb run{RESET}")
    print()
    print(f"  3. 启动知识库管理工具:")
    if sys.platform == "win32":
        print(f"     {GREEN}.venv\\Scripts\\python knowledge_manager.py{RESET}")
    else:
        print(f"     {GREEN}.venv/bin/python knowledge_manager.py{RESET}")
    print()


# ─── 主流程 ─────────────────────────────────────────
def main():
    print(f"{BOLD}bopang 首次安装向导{RESET}")
    print()

    check_python()
    create_venv()
    install_dependencies()
    create_env_file()
    create_data_dirs()
    print_summary()


if __name__ == "__main__":
    main()
