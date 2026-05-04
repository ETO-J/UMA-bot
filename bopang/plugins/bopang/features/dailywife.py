"""今日担当模块"""
import random
import datetime
from typing import Dict

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.log import logger

from ..config import PIXIV_IMAGES_DIR

# 用户调用记录
user_last_call: Dict[int, datetime.date] = {}

# 角色映射（中文 -> 日文文件夹名）
DAILYWIFE_MAP = {
    "特别周": "スペシャルウィーク", "无声铃鹿": "サイレンススズカ",
    "目白多伯": "メジロドーベル", "东海帝皇": "トウカイテイオー",
    "丸善斯基": "マルゼンスキー", "小栗帽": "オグリキャップ",
    "黄金船": "ゴールドシップ", "大和赤骥": "ダイワスカーレット",
    "大树快车": "タイキシャトル", "草上飞": "グラスワンダー",
    "目白麦昆": "メジロマックイーン", "神鹰": "エルコンドルパサー",
    "好歌剧": "テイエムオペラオー", "成田白仁": "ナリタブライアン",
    "鲁道夫象征": "シンボリルドルフ", "气槽": "エアグルーヴ",
    "爱丽数码": "アグネスデジタル", "青云天空": "セイウンスカイ",
    "玉藻十字": "タマモクロス", "美妙姿势": "ファインモーション",
    "摩耶重炮": "マヤノトップガン", "曼城茶座": "マンハッタンカフェ",
    "美浦波旁": "ミホノブルボン", "米浴": "ライスシャワー",
    "艾尼斯风神": "アイネスフウジン", "爱丽速子": "アグネスタキオン",
    "稻荷一": "イナリワン", "荣进闪耀": "エイシンフラッシュ",
    "真机伶": "カレンチャン", "黄金城": "ゴールドシチー",
    "樱花进王": "サクラバクシンオー", "东商变革": "スイープトウショウ",
    "超级小海湾": "スーパークリーク", "醒目飞鹰": "スマートファルコン",
    "成田大进": "ナリタタイシン", "西野花": "ニシノフラワー",
    "春乌拉拉": "ハルウララ", "待兼福来": "マチカネフクキタ",
    "千明代表": "ミスターシービー", "名将怒涛": "メイショウドトウ",
    "优秀素质": "ナイスネイチャ", "帝王光辉": "キングヘイロー",
    "待兼诗歌剧": "マチカネタンホイザ", "目白善信": "メジロパーマー",
    "大拓太阳神": "ダイタクヘリオス", "里见光钻": "サトノダイヤモンド",
    "北部玄驹": "キタサンブラック", "目白阿尔丹": "メジロアルダン",
    "目白光明": "メジロブライ", "樱花桂冠": "サクラローレル",
    "成田白": "ナリタトップロー", "创升": "トランセンド",
    "谷水琴蕾": "タニノギムレット", "目白高峰": "メジロラモーヌ",
    "里见皇冠": "サトノクラウン", "创世驹": "クロノジェネシス",
    "杏目": "アーモンドアイ", "秋川弥生": "秋川やよい",
    "光辉致意": "ライトハロー", "唯独爱你": "ラヴズオンリーユー",
    "速度象征": "スピードシンボリ", "黄金旅程": "ステイゴールド",
}


def _get_local_images(keyword: str) -> list:
    """从本地文件夹中获取匹配关键词的图片"""
    folder = PIXIV_IMAGES_DIR / keyword
    if not folder.exists():
        return []
    images = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.gif"]:
        images.extend(list(folder.glob(ext)))
    return images


dailywife_cmd = on_command("今日担当", priority=4, block=True)


@dailywife_cmd.handle()
async def handle_dailywife(bot: Bot, event: GroupMessageEvent, ):
    user_id = event.user_id
    today = datetime.date.today()

    # 每日限一次
    if user_id in user_last_call and user_last_call[user_id] == today:
        await bot.send(event, "你今天已经邂逅过了哦，明天再来吧~")
        return

    user_last_call[user_id] = today

    args = event.get_message().extract_plain_text().strip()
    # 移除命令前缀
    if args.startswith("/今日担当"):
        args = args[5:].strip()

    if args:
        image_files = _get_local_images(args)
        if not image_files:
            await bot.send(event, f"未找到与'{args}'相关的图片，请尝试其他关键词~")
            return
        chinese_name = args
    else:
        random_name = random.choice(list(DAILYWIFE_MAP.keys()))
        chinese_name = random_name
        image_files = list((PIXIV_IMAGES_DIR / random_name).glob("*.*"))
        if not image_files:
            await bot.send(event, f"随机选择了'{chinese_name}'，但未找到相关图片~")
            return

    selected_image = random.choice(image_files)
    file_uri = f"file:///{selected_image.absolute().as_posix()}"

    try:
        if not args:
            await bot.send(event, f"您今日的担当是：{chinese_name}")
        await bot.send(event, MessageSegment.image(file_uri))
    except Exception as e:
        logger.error(f"发送图片失败: {e}")
        await bot.send(event, "图片发送失败，请稍后再试~")
