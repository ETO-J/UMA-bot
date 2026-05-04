"""ComfyUI AI 绘画模块（含遗传提示词生成器）"""
import os
import random
import json
import urllib.request
from pathlib import Path
from typing import Union, Optional

from nonebot import on_message
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot.typing import T_State
from nonebot.log import logger
from openai import AsyncOpenAI
import httpx

from ..config import COMFYUI_DIR, COMFYUI_DEFAULT_RESOLUTIONS

from dotenv import load_dotenv
load_dotenv()
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8000")
AICHAT_KEY1 = os.getenv("AICHATKEY1", "")


# ========== 工作流管理器 ==========
class WorkflowManager:
    def __init__(self):
        self.comfyui_dir = COMFYUI_DIR
        self.current_workflow_name: str = "sek_BW"
        self.current_resolution: tuple = (832, 1216)

    def get_available_workflows(self) -> list:
        if not self.comfyui_dir.exists():
            return []
        return [f.stem for f in self.comfyui_dir.glob("*.json")]

    def get_workflow_path(self, name: str) -> Optional[Path]:
        path = self.comfyui_dir / f"{name}.json"
        return path if path.exists() else None


wm = WorkflowManager()


# ========== ComfyUI API 调用 ==========
async def generate_image(prompt: str, workflow_name: str = None) -> Optional[str]:
    """调用 ComfyUI 生成图片"""
    if workflow_name is None:
        workflow_name = wm.current_workflow_name

    workflow_path = wm.get_workflow_path(workflow_name)
    if not workflow_path:
        logger.error(f"工作流不存在: {workflow_name}")
        return None

    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        w, h = wm.current_resolution
        for node_id, node_data in workflow.items():
            if "inputs" in node_data:
                if "text" in node_data["inputs"] and node_data.get("class_type") == "CLIPTextEncode":
                    node_data["inputs"]["text"] = prompt
                if "width" in node_data["inputs"]:
                    node_data["inputs"]["width"] = w
                if "height" in node_data["inputs"]:
                    node_data["inputs"]["height"] = h

        prompt_data = {"prompt": workflow}
        data = json.dumps(prompt_data).encode("utf-8")
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())

        import asyncio
        await asyncio.sleep(5)

        history_req = urllib.request.Request(f"{COMFYUI_URL}/history/{result['prompt_id']}")
        with urllib.request.urlopen(history_req) as response:
            history = json.loads(response.read())

        for prompt_id, outputs in history.items():
            for node_id, node_output in outputs.get("outputs", {}).items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        img_url = f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder', '')}&type={img.get('type', 'output')}"
                        return img_url
        return None
    except Exception as e:
        logger.error(f"ComfyUI 生成失败: {e}")
        return None


# ========== AI 提示词转换 ==========
async def _convert_prompt_to_en(prompt: str) -> str:
    client = AsyncOpenAI(
        api_key=AICHAT_KEY1, base_url="https://api.deepseek.com",
        http_client=httpx.AsyncClient(trust_env=False),
    )
    messages = [
        {"role": "system", "content": "你是一个智能AI绘画提示词生成助手，负责将用户需求转换为专业的stable diffusion绘画英文提示词。对不安全提示词直接拒绝输出。将用户输入转换为适合SD绘画的单词短语提示词模式。最终输出必须为英文提示词格式。"},
        {"role": "user", "content": prompt},
    ]
    try:
        response = await client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=4096, temperature=1)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"请求出错：{e}"


# ========== 遗传提示词生成器 ==========
class GeneticPromptGenerator:
    def __init__(self):
        self.gene_pool = {
            "character": {
                "special week/(umamusume)/": ["school", "active"],
                "silence suzuka/(umamusume)/": ["school", "quiet", "run"],
                "gold ship/(umamusume)/": ["playful", "wild", "water"],
                "mejiro mcqueen/(umamusume)/": ["elegant", "garden", "tea"],
                "satono diamond/(umamusume)/": ["elegant", "rich"],
                "kitasan black/(umamusume)/": ["energetic", "festival", "japanese"],
                "Tokai Teio/(umamusume)/": ["school", "active", "naughty"],
                "Mihono Bourbon/(umamusume)/": ["like a robot", "Precise"],
                "Rice Shower/(umamusume)/": ["timid", "like sister"],
                "Nice Nature/(umamusume)/": ["Supporting role", "kind", "Ordinary"],
                "Mejiro Ardan/(umamusume)/": ["weak", "beautiful", "kind", "determined", "gental", "rich"],
            },
            "clothes": {
                "tracen school uniform": ["school", "daily"],
                "casual wear": ["daily", "street", "cafe"],
                "slingshot swimsuit": ["sexy", "water", "summer", "beach"],
                "school swimsuit": ["school", "water", "pool", "summer"],
                "kimono": ["japanese", "festival", "winter", "formal"],
                "winter coat": ["winter", "cold", "snow", "street"],
                "pajamas": ["sleep", "indoor", "night", "bed"],
                "evening gown": ["formal", "party", "elegant", "night"],
                "gym clothes": ["sport", "school", "run"],
                "summer_dress": ["summer", "trees", "flowers"],
                "weeding_dress": ["weeding", "beautiful"],
                "lolita_fashion": ["elegent", "quiet"],
            },
            "scene": {
                "classroom": ["school", "indoor", "daily"],
                "beach": ["water", "summer", "day", "hot"],
                "poolside": ["water", "summer", "school", "hot"],
                "winter village": ["winter", "snow", "cold", "outdoor"],
                "summer festival": ["festival", "japanese", "night", "summer"],
                "bedroom": ["indoor", "bed", "sleep", "private"],
                "shrine": ["japanese", "quiet", "outdoor"],
                "racetrack": ["run", "sport", "turf", "outdoor"],
                "cafe": ["indoor", "daily", "relax"],
                "flower_field": ["in spring or in summer", "flowers"],
            },
            "action": {
                "standing": ["daily", "neutral"],
                "sitting": ["daily", "relax", "indoor"],
                "running": ["run", "sport", "active"],
                "swimming": ["water", "sport"],
                "sleeping": ["sleep", "bed"],
                "praying": ["shrine", "quiet"],
                "eating": ["cafe", "festival", "daily"],
                "lying": ["bed", "flower_field"],
                "head tilt": ["cute", "question"],
            },
            "weather": {
                "sunny day": ["day", "summer", "hot"],
                "night": ["night", "dark"],
                "sunset": ["evening", "romantic"],
                "snowing": ["winter", "cold", "snow"],
                "star_night": ["star", "moon", "night", "quiet"],
            },
        }

    def _calculate_weight(self, gene_tags, context_tags):
        base_weight = 10
        bonus = sum(1 for tag in gene_tags if tag in context_tags) * 50
        return base_weight + bonus

    def generate(self) -> str:
        order = ["character", "clothes", "scene", "weather", "action"]
        selected = []
        context_tags = []
        for category in order:
            options = self.gene_pool[category]
            candidates = list(options.keys())
            weights = [self._calculate_weight(options[g], context_tags) for g in candidates]
            choice = random.choices(candidates, weights=weights, k=1)[0]
            selected.append(choice)
            context_tags.extend(options[choice])
        return "1girl, " + ", ".join(selected) + ", best quality, masterpiece, highres"


genetic_generator = GeneticPromptGenerator()


# ========== 命令注册 ==========
draw_cmd = on_command("draw", priority=4, block=True)
random_image_cmd = on_command("随机美图", priority=4, block=True)
workflow_list_cmd = on_command("工作流列表", priority=4, block=True)
switch_workflow_cmd = on_command("切换工作流", priority=4, block=True)
switch_resolution_cmd = on_command("切换分辨率", priority=4, block=True)


@draw_cmd.handle()
async def handle_draw(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    args = event.get_message().extract_plain_text().strip()
    selected_wf = wm.current_workflow_name
    if args.startswith("-w "):
        parts = args.split(" ", 2)
        if len(parts) >= 3:
            selected_wf = parts[1]
            args = parts[2]
    if not args:
        await draw_cmd.finish("请输入提示词")
        return
    w, h = wm.current_resolution
    await bot.send(event, f"使用 [{selected_wf}] ({w}x{h}) 绘制中...")
    try:
        image_data = await generate_image(args, selected_wf)
        if image_data:
            await bot.send(event, MessageSegment.image(image_data))
        else:
            await bot.send(event, "绘图失败，请确认工作流文件内容正确")
    except Exception as e:
        await bot.send(event, f"错误: {e}")

@random_image_cmd.handle()
async def handle_random_image(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    await bot.send(event, "正在生成随机美图，请稍后...")
    random_prompt = genetic_generator.generate()
    try:
        image_data = await generate_image(random_prompt)
        if image_data:
            await bot.send(event, MessageSegment.image(image_data))
        else:
            await bot.send(event, "生成图片失败，请重试")
    except Exception as e:
        await bot.send(event, f"生成图片时出错: {e}")


@workflow_list_cmd.handle()
async def handle_workflow_list(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    workflows = wm.get_available_workflows()
    if not workflows:
        await bot.send(event, f"目录中未找到JSON工作流文件\n路径: {COMFYUI_DIR}")
    else:
        msg = "可用的工具流列表：\n" + "\n".join([f"- {name}" for name in workflows])
        msg += f"\n\n当前正在使用: {wm.current_workflow_name}"
        msg += "\n使用 [/切换工作流 名称] 进行更改"
        await bot.send(event, msg)


@switch_workflow_cmd.handle()
async def handle_switch_workflow(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    args = event.get_message().extract_plain_text().strip()
    if not args:
        await switch_workflow_cmd.finish("请输入工作流名称")
        return
    workflows = wm.get_available_workflows()
    if args in workflows:
        wm.current_workflow_name = args
        await bot.send(event, f"工具流已切换为: {args}")
    else:
        await bot.send(event, f"找不到工具流 '{args}'")


@switch_resolution_cmd.handle()
async def handle_switch_resolution(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent], state: T_State):
    args = event.get_message().extract_plain_text().strip()
    if args in COMFYUI_DEFAULT_RESOLUTIONS:
        wm.current_resolution = COMFYUI_DEFAULT_RESOLUTIONS[args]
        w, h = wm.current_resolution
        await bot.send(event, f"分辨率已切换为：{w} x {h}")
    else:
        msg = (
            "请选择分辨率编号：\n"
            "1. 832 x 1216 (竖屏)\n"
            "2. 1024 x 1024 (正方形)\n"
            "3. 1216 x 832 (横屏)\n"
            "示例：/切换分辨率 2"
        )
        await bot.send(event, msg)
