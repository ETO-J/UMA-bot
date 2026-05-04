"""统一聊天处理器 - 合并命令式对话与自由聊天"""
import os
import random
from typing import Union

from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot.log import logger

from .chat import chat_with_ai, adapt_response_for_user
from .memory import memory
from .search_judge import needs_search_async, search_web
from .reply_judge import should_reply_with_ai
from .vision import analyze_image, build_vision_prompt
from ..config import ERROR_IMAGES_DIR, is_admin, is_freechat_enabled
from ..utils.user_info import get_user_info


# ========== 错误图片发送 ==========
async def send_error_image(bot: Bot, event):
    """发送错误占位图"""
    files = [f for f in os.listdir(ERROR_IMAGES_DIR) if os.path.isfile(os.path.join(ERROR_IMAGES_DIR, f))]
    if files:
        selected = random.choice(files)
        file_uri = f"file://{os.path.abspath(os.path.join(ERROR_IMAGES_DIR, selected))}"
        await bot.send(event, MessageSegment.image(file_uri))
    else:
        await bot.send(event, "服务暂时不可用，请稍后再试~")


# ========== 统一对话回复流程 ==========
async def _do_chat_reply(bot: Bot, event, prompt: str, session_id: int, user_id: int, session_type: str):
    """统一的聊天回复流程：搜索判断 -> AI调用 -> 回复"""
    search_result = ""
    needs, search_query, search_reason = await needs_search_async(prompt)
    if needs:
        await bot.send(event, "正在搜索相关信息...")
        logger.info(f"搜索: {search_query}, 理由: {search_reason}")
        search_result = search_web(search_query)
        logger.info(f"搜索结果: {search_result}")

    gpt_reply = await chat_with_ai(
        prompt=prompt,
        session_id=session_id,
        user_id=user_id,
        session_type=session_type,
        include_search_result=search_result,
    )

    memory.save_context(session_id, "assistant", gpt_reply, session_type)

    if gpt_reply.startswith(("抱歉", "请求出错")):
        await send_error_image(bot, event)
    else:
        gpt_reply = adapt_response_for_user(gpt_reply, user_id)
        await bot.send(event, gpt_reply)


# ========== /波旁 命令处理 ==========
bourbon_cmd = on_message(priority=4, block=False)


@bourbon_cmd.handle()
async def handle_bourbon(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    """处理 /波旁 命令 - 直接触发 AI 对话"""
    args = event.get_message().extract_plain_text().strip()
    if args.startswith("/波旁"):
        prompt = args[3:].strip() if args else ""

        if not prompt:
            await bourbon_cmd.finish("请输入你想说的话，例如：/波旁 今天的天气怎么样？")
            return

        user_info = await get_user_info(bot, event)
        session_id = user_info["session_id"]
        user_id = user_info["user_id"]
        session_type = user_info["session_type"]
        nickname = user_info["nickname"]

        prompt += f"[这条发言的用户昵称与id：]{nickname, user_id}"
        logger.info(f"{session_type}用户{user_id}输入：{prompt}")

        memory.save_context(session_id, user_id, prompt, session_type)
        await _do_chat_reply(bot, event, prompt, session_id, user_id, session_type)


# ========== 自由聊天处理 ==========
freechat_handler = on_message(priority=5, block=False)

@freechat_handler.handle()
async def handle_freechat(bot: Bot, event: GroupMessageEvent, state: T_State):
    """自由聊天 - 监听群消息，AI 自主判断是否回复"""
    if not isinstance(event, GroupMessageEvent):
        return

    user_id = event.user_id
    group_id = event.group_id
    message = event.get_message()
    plain_text = message.extract_plain_text().strip()

    # 跳过命令
    if plain_text.startswith("/"):
        return

    # 检查群聊自由聊天模式
    if not is_freechat_enabled(group_id):
        return

    user_info = await get_user_info(bot, event)
    nickname = user_info["nickname"]
    session_id = user_info["session_id"]
    session_type = user_info["session_type"]

    logger.info(f"自由聊天 群【{group_id}】用户【{nickname}】(QQ:{user_id}): {plain_text}")

    # --- 图片消息处理 ---
    has_image = any(seg.type == "image" for seg in message)
    if has_image:
        image_url = None
        for seg in message:
            if seg.type == "image":
                image_url = seg.data.get("url", "")
                break

        if image_url:
            logger.info("检测到图片消息，启动视觉理解")
            image_description = analyze_image(image_url)
            full_prompt = build_vision_prompt(image_description, plain_text)
            full_prompt += f"\n[以下是当前对话用户昵称与QQ号：]\n{nickname, user_id}"

            memory.save_context(session_id, user_id, full_prompt, session_type)

            if event.is_tome():
                await _do_chat_reply(bot, event, full_prompt, session_id, user_id, session_type)
            else:
                should = await should_reply_with_ai(full_prompt, group_id, nickname, user_id)
                if should:
                    await _do_chat_reply(bot, event, full_prompt, session_id, user_id, session_type)
                else:
                    memory.save_context(session_id, "assistant", "未回复", session_type)
        return

    # --- 跳过 @他人 和空消息 ---
    has_at_others = any(seg.type == "at" for seg in message)
    if has_at_others and not event.is_tome():
        return
    if event.reply is not None and not event.is_tome():
        return
    if not plain_text:
        return

    # --- 文本消息处理 ---
    full_prompt = plain_text + f"[这条发言的用户昵称与id：]{nickname, user_id}"
    memory.save_context(session_id, user_id, full_prompt, session_type)

    if event.is_tome():
        logger.info("检测到@或引用，强制发言")
        await _do_chat_reply(bot, event, full_prompt, session_id, user_id, session_type)
        return

    should = await should_reply_with_ai(plain_text, group_id, nickname, user_id)
    if should:
        logger.info("AI判断需要回复")
        await _do_chat_reply(bot, event, full_prompt, session_id, user_id, session_type)
    else:
        logger.info("AI判断不需要回复")
        memory.save_context(session_id, "assistant", "未回复", session_type)
