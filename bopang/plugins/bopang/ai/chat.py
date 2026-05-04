"""核心对话逻辑 - 上下文构建 + AI 调用"""
from datetime import datetime
from typing import Optional

from nonebot.log import logger

from .client import deepseek_client
from .memory import memory
from .persona import persona_manager
from ..config import (
    DEEPSEEK_REASONER_MODEL,
    CHAT_MAX_TOKENS,
    CHAT_TEMPERATURE,
)


def build_context_prompt(session_id: int, original_prompt: str, session_type: str = "group") -> str:
    """构建包含记忆上下文的 prompt"""
    context = memory.get_context(session_id, original_prompt, session_type)
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    history_context = "\n".join(
        [f"[历史消息] 用户{msg['user']}: {msg['content']}" for msg in context["history"]]
    ) if context["history"] else ""

    knowledge_context = (
        f"[相关知识]\n当前时间：{current_time}\n{context['knowledge']}"
        if context["knowledge"]
        else f"[相关知识]\n当前时间：{current_time}"
    )

    return f"""
{knowledge_context}

{history_context}
当前对话：
用户：{original_prompt}
你："""


async def chat_with_ai(
    prompt: str,
    session_id: int,
    user_id: int,
    session_type: str = "group",
    model: str = DEEPSEEK_REASONER_MODEL,
    include_search_result: str = "",
) -> str:
    """
    统一的 AI 对话接口

    Args:
        prompt: 用户输入（已附加用户信息）
        session_id: 会话ID
        user_id: 用户ID
        session_type: 会话类型
        model: 模型名称
        include_search_result: 搜索结果（可选）

    Returns:
        str: AI 回复内容
    """
    full_prompt = build_context_prompt(session_id, prompt, session_type)
    if include_search_result:
        full_prompt += f"\n[网络搜索结果]\n{include_search_result}"

    logger.info(f"AI Chat prompt: {full_prompt[:200]}...")

    messages = [
        {"role": "system", "content": persona_manager.get_current_prompt()},
        {"role": "user", "content": full_prompt},
    ]

    try:
        response = await deepseek_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=CHAT_MAX_TOKENS,
            temperature=CHAT_TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"请求出错：{e}"


def adapt_response_for_user(response: str, user_id: int) -> str:
    """根据用户ID适配回复中的称呼"""
    if user_id == 3197425473:
        response = response.replace("Master", "教练").replace("教练", "Master")
    return response
