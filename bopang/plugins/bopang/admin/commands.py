"""管理员命令模块 - 重启/清除/广播/知识库管理/人设切换/模拟聊天"""
import os
import sys
from nonebot import on_message, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot.log import logger

from ..utils.user_info import get_user_info
from ..ai.memory import memory
from ..ai.persona import persona_manager
from ..ai.persona.manager import handle_persona_list, handle_switch_persona
from ..config import CHAT_DB_PATH, ADMIN_IDS, GROUP_CHAT_STATUS, is_admin


# ========== 重启命令（保留 on_command，因为需要 got 确认流程）==========
restart_cmd = on_command("重启", priority=1, block=True)


@restart_cmd.handle()
async def handle_restart(bot: Bot, event, state: T_State):
    if not is_admin(event.user_id):
        await restart_cmd.finish("⚠️ 权限不足，仅管理员可执行此操作")
        return
    state["confirm_step"] = True
    await restart_cmd.send("⚠️ 确认要重启服务吗？这将导致短暂中断！\n请回复【确认】继续操作，或任意内容取消")


@restart_cmd.got("confirm")
async def got_restart_confirm(bot: Bot, event, state: T_State):
    if str(event.get_message()).strip() != "确认":
        await restart_cmd.finish("已取消重启操作")
        return
    try:
        await restart_cmd.send("🔄 服务重启中，请稍后...")
        logger.info(f"管理员 {event.user_id} 正在重启服务...")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        logger.error(f"重启失败: {e}")
        await restart_cmd.finish(f"重启失败: {e}")


# ========== 清除命令（保留 on_command，因为需要 got 确认流程）==========
clear_cmd = on_command("清除", priority=1, block=True)


@clear_cmd.handle()
async def handle_clear(bot: Bot, event, state: T_State):
    if not is_admin(event.user_id):
        await clear_cmd.finish("⚠️ 权限不足，仅管理员可执行此操作")
        return
    state["confirm_step"] = True
    await clear_cmd.send("⚠️ 确认要清除所有缓存并重启吗？\n请回复【确认】继续操作，或任意内容取消")


@clear_cmd.got("confirm")
async def got_clear_confirm(bot: Bot, event, state: T_State):
    if str(event.get_message()).strip() != "确认":
        await clear_cmd.finish("已取消清除操作")
        return
    try:
        deleted = 0
        if os.path.exists(CHAT_DB_PATH):
            os.remove(CHAT_DB_PATH)
            deleted += 1
            logger.info(f"已删除文件: {CHAT_DB_PATH}")

        report = f"✅ 缓存清除完成\n已删除文件：{deleted}个\n🔄 正在重新启动服务..."
        await clear_cmd.send(report)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        logger.error(f"清除失败: {e}")
        await clear_cmd.finish(f"清除失败: {e}")


# ========== 消息路由器（on_message 方式处理其余命令）==========
message_handler = on_message(priority=4, block=False)


@message_handler.handle()
async def handle_message(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent, state: T_State):
    # 仅处理纯文本消息
    message = event.get_message()
    plain_text = message.extract_plain_text().strip()

    # 只处理 / 开头的命令
    if not plain_text.startswith("/"):
        return

    # 排除features模块已处理的命令
    excluded_commands = ["/draw", "/随机美图", "/工作流列表", "/切换工作流", "/切换分辨率", "/涩图", "/识图", "/今日担当"]
    if any(plain_text.startswith(cmd) for cmd in excluded_commands):
        return

    user_id = event.user_id
    is_group = isinstance(event, GroupMessageEvent)
    group_id = event.group_id if is_group else None

    # 获取昵称
    if is_group:
        try:
            member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            nickname = member_info.get('card') or member_info.get('nickname', '未知用户')
        except Exception as e:
            logger.error(f"获取群成员信息失败: {str(e)}")
            nickname = "未知用户"
    else:
        try:
            user_info = await bot.get_stranger_info(user_id=user_id)
            nickname = user_info.get('nickname', '未知用户')
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            nickname = "未知用户"

    logger.info(f"命令路由 群【{group_id}】用户【{nickname}】(QQ:{user_id}): {plain_text}")

    # ---------- /人设列表 ----------
    if plain_text == "/人设列表":
        await handle_persona_list(bot, event)
        return

    # ---------- /切换人设 ----------
    if plain_text.startswith("/切换人设"):
        await handle_switch_persona(bot, event)
        return

    # ---------- /广播 ----------
    if plain_text.startswith("/广播"):
        if not is_group:
            await bot.send(event, "⚠️ 广播功能仅限群聊使用")
            return
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可广播")
            return
        content = plain_text[3:].strip()
        if not content:
            await bot.send(event, "请输入广播内容")
            return
        try:
            await bot.send_group_msg(
                group_id=event.group_id,
                message=MessageSegment.at("all") + f" {content}",
            )
            await bot.send(event, "✅ 公告已发布")
            logger.info(f"管理员 {nickname} 在群 {event.group_id} 广播: {content}")
        except Exception as e:
            logger.error(f"广播失败: {e}")
            await bot.send(event, f"广播失败: {e}")
        return

    # ---------- /开启模拟聊天 ----------
    if plain_text.startswith("/开启模拟聊天"):
        if not is_group:
            await bot.send(event, "⚠️ 此功能仅限群聊使用")
            return
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可操作")
            return
        GROUP_CHAT_STATUS[event.group_id] = True
        await bot.send(event, "✅ 自由聊天模式已开启")
        return

    # ---------- /关闭模拟聊天 ----------
    if plain_text.startswith("/关闭模拟聊天"):
        if not is_group:
            await bot.send(event, "⚠️ 此功能仅限群聊使用")
            return
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可操作")
            return
        GROUP_CHAT_STATUS[event.group_id] = False
        await bot.send(event, "✅ 自由聊天模式已关闭")
        return

    # ---------- /学习 ----------
    if plain_text.startswith("/学习"):
        knowledge = plain_text[3:].strip()
        if not knowledge:
            await bot.send(event, "请输入有效知识内容，格式：/学习 北京是中国的首都")
            return
        try:
            memory.add_knowledge(knowledge)
            await bot.send(event, f"新知识已掌握：{knowledge}")
            logger.success(f"知识库更新：{knowledge}")
        except Exception as e:
            await bot.send(event, f"学习失败：{e}")
            logger.error(f"知识库更新失败: {e}")
        return

    # ---------- /批量学习 ----------
    if plain_text.startswith("/批量学习"):
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可批量教学")
            return
        knowledge_block = plain_text[5:].strip()
        if not knowledge_block:
            await bot.send(event, "请输入知识内容，格式：/批量学习 [知识1]\\n[知识2]\\n...")
            return
        try:
            knowledge_items = [k.strip() for k in knowledge_block.split('\n') if k.strip()]
            if not knowledge_items:
                await bot.send(event, "未检测到有效的知识条目")
                return
            success_count = 0
            for item in knowledge_items:
                try:
                    memory.add_knowledge(item)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"知识添加失败: {item} - {e}")
            await bot.send(event, f"✅ 批量学习完成！成功添加 {success_count}/{len(knowledge_items)} 条知识")
            logger.success(f"管理员 {nickname} 批量添加了 {success_count} 条知识")
        except Exception as e:
            await bot.send(event, f"❌ 批量学习失败: {e}")
            logger.error(f"批量学习失败: {e}")
        return

    # ---------- /知识列表 ----------
    if plain_text.startswith("/知识列表"):
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可查看知识库")
            return
        try:
            all_knowledge = memory.get_all_knowledge()
            if not all_knowledge:
                await bot.send(event, "📚 知识库目前为空")
                return

            PAGE_SIZE = 10
            total_pages = (len(all_knowledge) + PAGE_SIZE - 1) // PAGE_SIZE
            page_num = 1
            args = plain_text.split()
            if len(args) > 1 and args[1].isdigit():
                page_num = max(1, min(int(args[1]), total_pages))

            start_idx = (page_num - 1) * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, len(all_knowledge))

            knowledge_list = f"📖 知识库条目列表(第{page_num}/{total_pages}页):\n"
            for idx in range(start_idx, end_idx):
                content = all_knowledge[idx].page_content
                if len(content) > 100:
                    content = content[:97] + "..."
                knowledge_list += f"{idx + 1}. {content}\n"

            if total_pages > 1:
                knowledge_list += f"\n使用 /知识列表 [页码] 查看其他页"

            await bot.send(event, knowledge_list)
            logger.success(f"管理员 {nickname} 查看了知识库列表 (第{page_num}页)")
        except Exception as e:
            await bot.send(event, f"❌ 获取知识列表失败: {e}")
            logger.error(f"知识库列表获取失败: {e}")
        return

    # ---------- /删除知识 ----------
    if plain_text.startswith("/删除知识"):
        if not is_admin(user_id):
            await bot.send(event, "⚠️ 权限不足，仅管理员可删除知识")
            return
        arg = plain_text[5:].strip()
        if not arg:
            await bot.send(event, "请指定要删除的知识内容或序号\n格式：/删除知识 [序号] 或 /删除知识 [内容片段]")
            return
        try:
            index = int(arg)
            success = memory.delete_knowledge_by_index(index)
            if success:
                await bot.send(event, f"✅ 知识条目 #{index} 已成功删除")
                logger.success(f"管理员 {nickname} 删除了知识条目 #{index}")
            else:
                await bot.send(event, f"❌ 删除失败：序号 {index} 无效")
        except ValueError:
            success = memory.delete_knowledge_by_content(arg)
            if success:
                await bot.send(event, f"✅ 包含 '{arg}' 的知识条目已删除")
                logger.success(f"管理员 {nickname} 删除了包含'{arg}'的知识条目")
            else:
                await bot.send(event, f"❌ 未找到包含 '{arg}' 的知识条目")
        return
