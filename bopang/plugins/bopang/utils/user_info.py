"""统一用户信息获取"""
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.log import logger


async def get_user_info(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent) -> dict:
    """
    获取用户信息（昵称、user_id、session_id、session_type）

    Returns:
        dict: {
            "nickname": str,
            "user_id": int,
            "session_id": int,  # 群聊=group_id, 私聊=user_id
            "session_type": str,  # "group" | "private"
        }
    """
    user_id = event.user_id

    if isinstance(event, GroupMessageEvent):
        session_id = event.group_id
        session_type = "group"
        try:
            member_info = await bot.get_group_member_info(
                group_id=session_id, user_id=user_id
            )
            nickname = member_info.get("card") or member_info.get("nickname", "未知用户")
        except Exception as e:
            logger.error(f"获取群成员信息失败: {e}")
            nickname = "未知用户"
    else:
        session_id = user_id
        session_type = "private"
        try:
            user_info = await bot.get_stranger_info(user_id=user_id)
            nickname = user_info.get("nickname", "未知用户")
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            nickname = "未知用户"

    return {
        "nickname": nickname,
        "user_id": user_id,
        "session_id": session_id,
        "session_type": session_type,
    }
