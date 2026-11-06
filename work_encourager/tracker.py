"""计时与收入引擎。

准确性设计：
- 只累计「状态为 working 且程序在运行」期间的时间，暂停/下班即停。
- 使用 wall/mono 双时钟差检测休眠与人为改钟：休眠期间的时间直接丢弃，
  单次心跳增量上限 30 秒兜底，保证休眠、关机、改时间都不会错误累计。
- 累计秒数每 5 秒原子落盘，程序崩溃最多丢 5 秒；重开后无缝恢复。
- 跨天自动把昨日数据归档进 history，并从零开始新的一天。
"""

from __future__ import annotations

import datetime as dt
import time

from . import storage
from .messages import fmt_countdown
from .storage import Settings, State

WEEK_CN = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")


def today_str(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now()).strftime("%Y-%m-%d")


def parse_hhmm(s: str, default: str) -> dt.time:
    try:
        h, m = s.split(":")
        return dt.time(int(h) % 24, int(m) % 60)
    except (ValueError, AttributeError):
        h, m = default.split(":")
        return dt.time(int(h), int(m))


class Tracker:
    MAX_TICK = 30.0        # 单次心跳最大累计秒数（休眠兜底）
    SAVE_INTERVAL = 5.0    # 自动落盘间隔（秒）

    def __init__(self, settings: Settings, state: State | None = None, clock=None):
        self.s = settings
        self.st = state if state is not None else storage.load_state()
        self._clock = clock or (lambda: (time.time(), time.monotonic()))
        self._last_wall, self._last_mono = self._clock()
        self._last_save_wall = self._last_wall
        self._ensure_day()

    # ---------- 打卡操作 ----------
    def clock_in(self) -> None:
        if self.st.status != "working":
            self.st.status = "working"
            self.save(force=True)

    def pause(self) -> None:
        if self.st.status == "working":
            self.st.status = "paused"
            self.save(force=True)

    def resume(self) -> None:
        if self.st.status == "paused":
            self.st.status = "working"
            self.save(force=True)

    def clock_out(self) -> None:
        if self.st.status != "off":
            self.st.status = "off"
            self._archive(self.st.date)
            self.save(force=True)

    # ---------- 心跳 ----------
    def tick(self) -> float:
        """推进计时，返回本次新增的工作秒数。由 UI 定时器每 100ms 调用。"""
        wall, mono = self._clock()
        wall_d = wall - self._last_wall
        mono_d = mono - self._last_mono
        self._last_wall, self._last_mono = wall, mono

        self._ensure_day(wall)

        delta = 0.0
        if self.st.status == "working":
            if wall_d < 0:
                delta = max(0.0, mono_d)      # 系统时钟被回拨：按真实流逝计
            elif wall_d > mono_d + 2.0:
                delta = 0.0                    # 休眠 / 时钟前跳：丢弃
            else:
                delta = wall_d                 # 正常流逝
            delta = min(delta, self.MAX_TICK)
            self.st.acc_seconds += delta

        if wall - self._last_save_wall >= self.SAVE_INTERVAL:
            self.save()
        return delta

    # ---------- 数值查询 ----------
    def earned_today(self) -> float:
        return self.st.acc_seconds * self.s.hourly_wage / 3600.0

    def per_second(self) -> float:
        return self.s.hourly_wage / 3600.0

    def worked_hours(self) -> float:
        return self.st.acc_seconds / 3600.0

    def target_hours(self) -> float:
        return max(0.5, self.s.daily_target_hours)

    def full_day_pay(self) -> float:
        return self.s.daily_target_hours * self.s.hourly_wage

    def earned_month(self) -> float:
        ym = today_str()[:7]
        return sum(v.get("earned", 0.0) for d, v in self.st.history.items() if d.startswith(ym))

    def is_workday(self, d: dt.date | None = None) -> bool:
        return (d or dt.date.today()).weekday() in self.s.workdays

    def countdown_text(self) -> str:
        now = dt.datetime.now()
        if not self.is_workday(now.date()):
            return "今天休息，不上班"
        start_t = parse_hhmm(self.s.start_time, "09:00")
        end_t = parse_hhmm(self.s.end_time, "18:00")
        start_dt = dt.datetime.combine(now.date(), start_t)
        end_dt = dt.datetime.combine(now.date(), end_t)
        if now < start_dt:
            return "距离上班还有 " + fmt_countdown((start_dt - now).total_seconds())
        remain = (end_dt - now).total_seconds()
        if remain < 0 and end_t <= start_t:  # 跨天夜班
            nxt = (end_dt + dt.timedelta(days=1) - now).total_seconds()
            if nxt > 0:
                remain = nxt
        if remain > 0:
            return "距离下班还有 " + fmt_countdown(remain)
        return "已过下班时间 " + fmt_countdown(-remain)

    # ---------- 内部 ----------
    def _ensure_day(self, wall: float | None = None) -> None:
        now_dt = dt.datetime.fromtimestamp(wall) if wall is not None else dt.datetime.now()
        today = now_dt.strftime("%Y-%m-%d")
        if self.st.date != today:
            if self.st.date:
                self._archive(self.st.date)
            self.st.date = today
            self.st.acc_seconds = 0.0
            self.save(force=True)
        else:
            self._archive(today)  # 今日实时入账，保证"本月累计"包含今天

    def _archive(self, date: str) -> None:
        if not date:
            return
        if self.st.acc_seconds <= 0 and date not in self.st.history:
            return
        self.st.history[date] = {
            "seconds": round(self.st.acc_seconds, 2),
            "earned": round(self.st.acc_seconds * self.s.hourly_wage / 3600.0, 4),
        }

    def save(self, force: bool = False) -> None:
        wall, _ = self._clock()
        if not force and wall - self._last_save_wall < self.SAVE_INTERVAL:
            return
        self._last_save_wall = wall
        self.st.last_save = wall
        storage.save_state(self.st)
