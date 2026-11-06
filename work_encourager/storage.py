"""设置与运行状态的本地持久化（JSON，原子写入）。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from . import config


@dataclass
class Settings:
    salary_type: str = "hourly"        # hourly | monthly
    salary_value: float = 25.0         # 用户输入的收入原值（时薪或月薪）
    daily_target_hours: float = 7.5    # 每日目标工作时长
    start_time: str = "09:00"          # 上班时间
    end_time: str = "18:00"            # 下班时间
    workdays: list = field(default_factory=lambda: [0, 1, 2, 3, 4])  # 0=周一
    theme: str = "light"               # light | dark
    always_on_top: bool = True

    @property
    def monthly_workdays(self) -> float:
        """月均工作日数：按设置的工作日推算（每周天数 × 52 / 12）。"""
        if not self.workdays:
            return 21.75
        return len(self.workdays) * 52.0 / 12.0

    @property
    def hourly_wage(self) -> float:
        """实际计时用的时薪；月薪模式自动折算。"""
        if self.salary_type == "monthly":
            return self.salary_value / (self.monthly_workdays * max(0.5, self.daily_target_hours))
        return self.salary_value


@dataclass
class State:
    date: str = ""                     # 数据所属日期 YYYY-MM-DD
    status: str = "off"                # off | working | paused
    acc_seconds: float = 0.0           # 今日累计工作秒数（只增不减，暂停即停）
    history: dict = field(default_factory=dict)  # date -> {seconds, earned}
    last_save: float = 0.0


def _atomic_write(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_settings() -> Settings:
    s = Settings()
    path = os.path.join(config.data_dir(), "settings.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for k in ("daily_target_hours",):
            if k in raw:
                setattr(s, k, max(0.0, float(raw[k])))
        st = str(raw.get("salary_type", "hourly"))
        if st in ("hourly", "monthly"):
            s.salary_type = st
        if "salary_value" in raw:                       # 新格式
            s.salary_value = max(0.0, float(raw["salary_value"]))
        elif "hourly_wage" in raw:                      # 旧配置迁移
            s.salary_value = max(0.0, float(raw["hourly_wage"]))
        for k in ("start_time", "end_time", "theme"):
            if k in raw:
                setattr(s, k, str(raw[k]))
        if isinstance(raw.get("workdays"), list):
            s.workdays = sorted({int(x) for x in raw["workdays"] if 0 <= int(x) <= 6})
        if isinstance(raw.get("always_on_top"), bool):
            s.always_on_top = raw["always_on_top"]
    except (OSError, ValueError, TypeError):
        pass
    return s


def save_settings(s: Settings) -> None:
    _atomic_write(os.path.join(config.data_dir(), "settings.json"), {
        "salary_type": s.salary_type,
        "salary_value": s.salary_value,
        "daily_target_hours": s.daily_target_hours,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "workdays": s.workdays,
        "theme": s.theme,
        "always_on_top": s.always_on_top,
    })


def load_state() -> State:
    st = State()
    path = os.path.join(config.data_dir(), "state.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        st.date = str(raw.get("date", ""))
        status = str(raw.get("status", "off"))
        st.status = status if status in ("off", "working", "paused") else "off"
        st.acc_seconds = max(0.0, float(raw.get("acc_seconds", 0.0)))
        st.last_save = float(raw.get("last_save", 0.0))
        hist = raw.get("history")
        if isinstance(hist, dict):
            for d, v in hist.items():
                try:
                    st.history[str(d)] = {
                        "seconds": max(0.0, float(v.get("seconds", 0.0))),
                        "earned": max(0.0, float(v.get("earned", 0.0))),
                    }
                except (AttributeError, ValueError, TypeError):
                    continue
    except (OSError, ValueError, TypeError):
        pass
    return st


def save_state(st: State) -> None:
    _atomic_write(os.path.join(config.data_dir(), "state.json"), {
        "date": st.date,
        "status": st.status,
        "acc_seconds": st.acc_seconds,
        "history": st.history,
        "last_save": st.last_save,
    })
