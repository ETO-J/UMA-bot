"""统一记忆系统 - 门面模式"""
from typing import List, Optional
from langchain_core.documents import Document

from .chat_history import ChatHistoryMemory
from .knowledge_base import KnowledgeBaseMemory
from ...config import CHAT_HISTORY_LIMIT, KNOWLEDGE_SEARCH_K


class MemorySystem:
    """综合记忆系统（全局单例）"""

    def __init__(self):
        self.chat_history = ChatHistoryMemory()
        self.knowledge_base = KnowledgeBaseMemory()

    def save_context(self, session_id: int, user_id: int, user_input: str, session_type: str = "group"):
        """保存聊天上下文"""
        self.chat_history.save_message(session_id, user_id, user_input, session_type)

    def get_context(self, session_id: int, user_input: str, session_type: str = "group") -> dict:
        """获取综合上下文（历史 + 知识库检索）"""
        if session_type == "private":
            history = self.chat_history.get_private_recent_chat(session_id, limit=CHAT_HISTORY_LIMIT)
        else:
            history = self.chat_history.get_recent_chat(session_id, session_type, limit=CHAT_HISTORY_LIMIT)

        return {
            "history": history,
            "knowledge": self.knowledge_base.search_knowledge(user_input, k=KNOWLEDGE_SEARCH_K),
        }

    # --- 知识库代理方法 ---
    def get_all_knowledge(self) -> List[Document]:
        return self.knowledge_base.get_all_knowledge()

    def add_knowledge(self, text: str, metadata: dict = None):
        self.knowledge_base.add_knowledge(text, metadata)

    def bulk_add_knowledge(self, texts: List[str], metadatas: List[dict] = None):
        self.knowledge_base.add_knowledge_batch(texts, metadatas)

    def search_knowledge(self, query: str, k: int = 5, metadata_filter: dict = None) -> str:
        return self.knowledge_base.search_knowledge(query, k, metadata_filter)

    def delete_knowledge_by_content(self, content: str) -> bool:
        return self.knowledge_base.delete_knowledge_by_content(content)

    def delete_knowledge_by_index(self, index: int) -> bool:
        return self.knowledge_base.delete_knowledge_by_index(index)


# 全局单例
memory = MemorySystem()
