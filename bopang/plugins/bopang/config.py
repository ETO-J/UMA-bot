"""统一配置中心 - 所有配置项集中管理"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === 项目路径 ===
PROJECT_ROOT = Path(__file__).absolute().parent.parent.parent.parent  # bopang/
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = PROJECT_ROOT / "images"
PIXIV_IMAGES_DIR = PROJECT_ROOT / "pixiv_images"
COMFYUI_DIR = PROJECT_ROOT / "comfyui"
AISSETTING_DIR = DATA_DIR / "aisetting"
ERROR_IMAGES_DIR = IMAGES_DIR / "errors"

# 确保目录存在
for d in [DATA_DIR, IMAGES_DIR, PIXIV_IMAGES_DIR, ERROR_IMAGES_DIR, AISSETTING_DIR, COMFYUI_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === 管理员 ===
ADMIN_IDS: list[int] = [3197425473]

def is_admin(user_id: int) -> bool:
    """判断是否为管理员"""
    return user_id in ADMIN_IDS

# === AI 模型配置 ===
DEEPSEEK_API_KEY = os.getenv("AICHATKEY1", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_CHAT_MODEL = "deepseek-v4-flash"
DEEPSEEK_REASONER_MODEL = "deepseek-v4-pro"

OLLAMA_HOST = "http://127.0.0.1:11434/v1"
OLLAMA_MODEL = "glm-4.7-flash:latest"

DOUBAO_API_KEY = os.getenv("VIRSIONKEY1", "")
DOUBAO_VISION_MODEL = "doubao-seed-1-6-vision-250815"

# === 搜索 ===
BING_API_KEY = os.getenv("BINGSEARCHKEY1", "")
BING_SEARCH_URL = "https://api.bocha.cn/v1/web-search"

# === Pixiv ===
PIXIV_REFRESH_TOKEN = os.getenv("PIXIV_REFRESH_TOKEN")

# === SauceNAO ===
SAUCENAO_API_KEY = os.getenv("SAUCENAO_API_KEY")
SAUCENAO_MIN_SIMILARITY = 60

# === 群聊自由聊天模式 ===
GROUP_CHAT_STATUS: dict[int, bool] = {
    #工会群
    971602815: False,
    #bot测试
    864323384: True,
    878099781: False,
}

def is_freechat_enabled(group_id: int) -> bool:
    """判断群是否开启自由聊天"""
    return GROUP_CHAT_STATUS.get(group_id, True)

# === 记忆系统 ===
CHAT_DB_PATH = DATA_DIR / "chat_history.db"
KNOWLEDGE_DB_PATH = DATA_DIR / "knowledge_db"
MODEL_CACHE_PATH = DATA_DIR / "model_cache"
MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)
EMBEDDING_MODEL_NAME = "GanymedeNil/text2vec-base-chinese"

# === 疲劳因子 ===
FATIGUE_HALF_LIFE = 240
FATIGUE_THRESHOLD_K = 3.0
FATIGUE_STEEPNESS_N = 4.0
FATIGUE_OBSERVATION_WINDOW = 900

# === 定时消息 ===
SCHEDULED_MESSAGE_GROUPS: list[int] = [971602815]
SCHEDULED_GOOD_MORNING_HOUR = 7
SCHEDULED_GOOD_MORNING_MINUTE = 30
SCHEDULED_GOOD_NIGHT_HOUR = 23
SCHEDULED_GOOD_NIGHT_MINUTE = 0

# === 对话参数 ===
CHAT_HISTORY_LIMIT = 10
KNOWLEDGE_SEARCH_K = 3
CHAT_MAX_TOKENS = 8192
CHAT_TEMPERATURE = 1.0

# === ComfyUI ===
COMFYUI_DEFAULT_RESOLUTIONS = {
    "1": (832, 1216),   # 竖屏
    "2": (1024, 1024),  # 正方形
    "3": (1216, 832),   # 横屏
}

# === 国内 HuggingFace 镜像 ===
HF_MIRRORS = [
    "https://hf-mirror.com",
    "https://hf-mirror.cos.accelerate.myqcloud.com",
    "https://hub.yzuu.cf",
]
