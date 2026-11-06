"""趣味鼓励语生成。"""

from __future__ import annotations

import random

# (名称, 价格) —— 用于"再过 X 就赚回来了"
ITEMS = [
    ("蜜雪冰城", 6), ("瑞幸咖啡", 9.9), ("奶茶", 15), ("一顿午饭", 22),
    ("打车回家", 28), ("星巴克拿铁", 35), ("炸鸡", 33), ("电影票", 45),
    ("游戏皮肤", 60), ("一件T恤", 79), ("一顿火锅", 89), ("一支口红", 159),
    ("一双球鞋", 699), ("一部手机", 5999),
]

WORK_QUOTES = [
    "钱在跳，别慌，稳住我们能赢。",
    "别人的班是上班，你的班是在提款。",
    "带薪呼吸进行中，每一秒都算钱。",
    "别眨眼，钱正在变成小数点后四位。",
    "工作使我快乐，更使我变富。",
    "今天也是离财务自由更近的一天（一点点）。",
    "摸鱼一时爽，但看着数字跳更爽。",
    "坚持住，工资正在赶来的路上。",
    "再坚持一下，工位就是你的提款机。",
]

REST_QUOTES = [
    "休息是为了赚更多的钱。",
    "暂停中：钱包正在充能。",
    "歇会儿，钱不会跑，但奶茶会凉。",
    "劳逸结合，赚钱效率更高。",
]

OFF_QUOTES = [
    "点一下「上班打卡」，开始今天的进账。",
    "还没打卡，钱包正在等你。",
    "新的一天，从第一秒进账开始。",
]


def fmt_countdown(seconds: float) -> str:
    """把秒数格式化为「2小时54分18秒」样式。"""
    s = max(0, int(seconds))
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h > 0:
        return f"{h}小时{m:02d}分{s:02d}秒"
    if m > 0:
        return f"{m}分{s:02d}秒"
    return f"{s}秒"


def pick_message(earned: float, rate: float, status: str) -> str:
    """根据今日已赚、每秒收入和打卡状态，随机生成一条鼓励语。"""
    if status == "working":
        if rate > 0 and random.random() < 0.62:
            name, price = random.choice(ITEMS)
            if earned >= price:
                return f"「{name}」的钱已经赚回来了，接下来全是纯赚！"
            need = (price - earned) / rate
            return f"再过 {fmt_countdown(need)}，「{name}」就赚回来了"
        return random.choice(WORK_QUOTES)
    if status == "paused":
        return random.choice(REST_QUOTES)
    return random.choice(OFF_QUOTES)
