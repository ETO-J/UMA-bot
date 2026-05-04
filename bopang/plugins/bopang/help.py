"""帮助信息"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from typing import Union


help_cmd = on_command("help", priority=2, block=True)

HELP_TEXT = """【使用指南】
/波旁 [内容] - 与波旁对话（含记忆+联网搜索）
/人设列表 / 切换人设 [名称] - 查看与切换人设
/识图 - 反向搜图
/今日担当 - 每日一次邂逅
/学习 [知识] - 教机器人新知识
/批量学习 / 知识列表 / 删除知识 - 知识库管理(管理员)
/开启模拟聊天 / 关闭模拟聊天 - 自由对话模式(管理员)
/重启 / 清除 - 管理员专用

【详细示例】
/波旁 今天的天气怎么样？
/学习 波旁的生日是4月15日"""


@help_cmd.handle()
async def handle_help(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state):
    await bot.send(event, HELP_TEXT)
