# 🥃 bopang

基于 [NoneBot2](https://nonebot.dev/) 的多功能 QQ 机器人，支持 AI 对话、知识库管理、Pixiv 搜图、ComfyUI 绘图等功能。

## ✨ 功能

- **AI 对话** — 基于 DeepSeek 的群聊/私聊对话，支持上下文记忆
- **知识库** — FAISS 向量检索，支持导入/搜索/删除/管理（带 GUI 工具）
- **视觉识别** — 豆包视觉模型，图片内容理解
- **Pixiv 搜图** — 热门/插画/漫画搜索
- **ComfyUI 绘图** — 文生图，支持多种分辨率
- **今日担当** — 每日随机角色
- **SauceNAO 识图** — 以图搜源

## 🚀 快速开始

### 环境要求

- Python >= 3.9
- pip

### 配置

编辑项目根目录下的 `.env` 文件，填写你的 API Key：

```ini
# DeepSeek (AI 对话，必填)
AICHATKEY1=sk-your-key-here

# 豆包 (视觉识别)
VIRSIONKEY1=your-doubao-key

# Bing 搜索
BINGSEARCHKEY1=your-bing-key

# SauceNAO (识图)
SAUCENAO_API_KEY=your-saucenao-key

# Pixiv
PIXIV_REFRESH_TOKEN=your-pixiv-token
```

> 至少需要填写 `AICHATKEY1`，其余按需配置。

### 运行

**启动机器人：**

```bash
# Windows
.venv\Scripts\python bot.py

# Linux / macOS
.venv/bin/python bot.py
```

或使用 NoneBot CLI：

```bash
# Windows
.venv\Scripts\activate && nb run

# Linux / macOS
source .venv/bin/activate && nb run
```

**启动知识库管理工具（GUI）：**

```bash
# Windows
.venv\Scripts\python knowledge_manager.py

# Linux / macOS
.venv/bin/python knowledge_manager.py
```

## 📁 项目结构

```
bopang/
├── bot.py                    # 机器人入口
├── knowledge_manager.py      # 知识库管理 GUI 工具
├── setup.py                  # 首次安装脚本
├── requirements.txt          # 依赖清单
├── .env.example              # 环境变量模板
├── pyproject.toml            # 项目配置 & NoneBot 插件加载
├── bopang/
│   └── plugins/
│       └── bopang/           # 统一插件
│           ├── config.py     # 配置中心
│           ├── help.py       # /help 命令
│           ├── ai/           # AI 相关模块
│           │   ├── chat.py       # 对话处理
│           │   ├── client.py     # LLM 客户端
│           │   ├── freechat.py   # 自由聊天
│           │   ├── memory/       # 记忆系统
│           │   │   ├── knowledge_base.py  # FAISS 知识库
│           │   │   ├── chat_history.py     # 聊天记录
│           │   │   └── memory_system.py    # 统一门面
│           │   ├── persona/      # 人设管理
│           │   └── vision/       # 视觉识别
│           ├── features/    # 功能模块
│           │   ├── comfyui.py    # ComfyUI 绘图
│           │   ├── dailywife.py  # 今日担当
│           │   ├── image_search.py # SauceNAO 识图
│           │   └── pixiv.py      # Pixiv 搜图
│           ├── admin/       # 管理员命令
│           └── utils/       # 工具函数
├── data/                     # 运行时数据（自动创建，不入 Git）
│   ├── knowledge_db/         # FAISS 向量库
│   ├── model_cache/          # Embedding 模型缓存
│   └── aissetting/           # AI 设置
└── images/                   # 图片存储（自动创建）
```

## ⚙️ 手动安装

如果你不想使用一键安装脚本：

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填写 API Key

# 5. 运行
python bot.py
```

## 📄 License

MIT
