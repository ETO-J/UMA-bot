"""聊天记录存储 - SQLite"""
import sqlite3
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from nonebot.log import logger

from ...config import CHAT_DB_PATH

# 北京时间
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time() -> str:
    """获取当前北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")


class ChatHistoryMemory:
    def __init__(self):
        self.db_path = CHAT_DB_PATH
        self._init_db()

    def _init_db(self):
        """初始化数据库，确保表结构正确"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT,
                    session_type TEXT DEFAULT 'group'
                )
            """)
            # 兼容旧数据库：添加缺失的列
            try:
                conn.execute("ALTER TABLE chat_history ADD COLUMN session_type TEXT DEFAULT 'group'")
            except sqlite3.OperationalError:
                pass
            conn.execute("UPDATE chat_history SET session_type = 'group' WHERE session_type IS NULL")
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_group ON chat_history (group_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON chat_history (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_type ON chat_history (session_type)")

    def save_message(self, session_id: int, user_id: int, content: str, session_type: str = "group"):
        """保存单条聊天记录"""
        beijing_time = get_beijing_time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO chat_history (group_id, user_id, content, session_type, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, content, session_type, beijing_time),
            )
            logger.info(f"Saved message: session_id={session_id}, user={user_id}, type={session_type}, time={beijing_time}")

    def get_recent_chat(self, session_id: int, session_type: str = "group", limit: int = 10) -> List[Dict]:
        """获取最近N条用户历史（排除AI回复）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id, content FROM chat_history "
                "WHERE group_id = ? AND session_type = ? AND user_id != 'assistant' "
                "ORDER BY timestamp DESC LIMIT ?",
                (session_id, session_type, limit),
            )
            return [{"user": row[0], "content": row[1]} for row in cursor.fetchall()]

    def get_private_recent_chat(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取私聊最近N条用户历史（排除AI回复）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id, content FROM chat_history "
                "WHERE user_id = ? AND session_type = 'private' "
                "ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit),
            )
            return [{"user": row[0], "content": row[1]} for row in cursor.fetchall()]

    def get_ai_timestamps(self, group_id: int, limit: int = 20, time_window_seconds: int = 600) -> List[float]:
        """获取AI在指定群组内最近一段时间的发言时间戳"""
        time_threshold = datetime.now(BEIJING_TZ) - timedelta(seconds=time_window_seconds)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT strftime('%s', timestamp)
                FROM chat_history
                WHERE group_id = ?
                  AND user_id = 'assistant'
                  AND content != '未回复'
                  AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (group_id, time_threshold, limit),
            )
            return [float(row[0]) for row in cursor.fetchall() if row[0] is not None]
