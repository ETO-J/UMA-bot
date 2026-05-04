"""自由聊天回复判断模块（含疲劳因子）"""
import time
import math

from nonebot.log import logger
from openai import AsyncOpenAI
import httpx

from .client import ollama_client
from .memory import memory
from ..config import (
    OLLAMA_MODEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_CHAT_MODEL,
    DEEPSEEK_BASE_URL,
    FATIGUE_HALF_LIFE,
    FATIGUE_THRESHOLD_K,
    FATIGUE_STEEPNESS_N,
    FATIGUE_OBSERVATION_WINDOW,
)


def calculate_fatigue_T(group_id: int) -> float:
    """
    计算疲劳衰减因子 T (0.0 ~ 1.0)
    T = 1.0 表示精力充沛，T -> 0.0 表示极度疲劳
    """
    try:
        timestamps = memory.chat_history.get_ai_timestamps(
            group_id=group_id,
            limit=10,
            time_window_seconds=FATIGUE_OBSERVATION_WINDOW,
        )
        if not timestamps:
            return 1.0

        current_time = time.time()
        tau = FATIGUE_HALF_LIFE / 0.6931

        heat = 0.0
        for ts in timestamps:
            delta_t = max(0, current_time - ts)
            if delta_t <= FATIGUE_OBSERVATION_WINDOW:
                heat += math.exp(-delta_t / tau)

        if heat < 0.01:
            return 1.0

        term = (heat / FATIGUE_THRESHOLD_K) ** FATIGUE_STEEPNESS_N
        t_score = 1.0 / (1.0 + term)
        logger.debug(f"[疲劳计算] 群{group_id} | 热度:{heat:.2f} | T值:{t_score:.2f}")
        return t_score
    except Exception as e:
        logger.error(f"计算疲劳因子T失败: {e}")
        return 1.0


async def should_reply_with_ai(
    message: str, group_id: int, nickname: str, user_id: int
) -> bool:
    """
    使用次级 AI 模型判断是否需要回复

    Args:
        message: 用户消息内容
        group_id: 群组ID
        nickname: 用户昵称
        user_id: 用户ID

    Returns:
        True=需要回复, False=不需要
    """
    try:
        T = calculate_fatigue_T(group_id)
        context = memory.get_context(group_id, message, session_type="group")

        history_text = ""
        if context["history"]:
            history_text = "\n".join(
                [f"[历史消息] 用户{msg['user']}: {msg['content']}" for msg in context["history"][-10:]]
            )
        else:
            history_text = "（暂无历史消息）"

        judge_prompt = f"""你是一个智能回复判断助手。请根据以下信息判断美浦波旁（我）是否需要回复这条消息。你只能输出0或1。1代表回复，0代表不回复。
【当前对话信息】
- 用户昵称：{nickname}
- 用户ID：{user_id}
- 群组ID：{group_id}
- 用户消息：{message}
- 疲劳因子T（0.0-1.0，1.0表示精力充沛，0.0表示极度疲劳）：{T:.2f}
【最近群聊历史消息】
{history_text}

【判断标准】
1. 当T值较低（<0.3）时，除非消息明显需要回复（如直接提问、呼唤等），否则倾向于不回复。当T值较高（>0.7）时，可以更积极地参与对话
2. 优先回复与你(美浦波旁，简称波旁，或赛马娘同学)相关的消息，如你的同学：米浴，优秀素质，创世驹，目白阿尔丹等人
3. 对于普通闲聊，根据T值和消息内容综合判断。可以解答单条消息，但最好不要插入正在进行的话题
4. 如果历史消息显示话题与美浦波旁（我）相关，即使T值较低也应考虑回复

请只回复一个数字：1（需要回复）或0（不需要回复）"""

        response = await ollama_client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "你是一个智能回复判断助手，只输出0或1。"},
                {"role": "user", "content": judge_prompt},
            ],
            max_tokens=1024,
            temperature=0.1,
        )

        result = response.choices[0].message.content.strip()
        should_reply = result == "1"
        logger.info(f"AI判断结果：{result} (消息: {message[:20]}...), T值: {T:.2f}")
        return should_reply

    except Exception as e:
        logger.error(f"AI判断是否回复时出错: {e}")
        T = calculate_fatigue_T(group_id)
        return T > 0.5
