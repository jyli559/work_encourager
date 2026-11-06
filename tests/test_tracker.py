"""计时引擎单元测试：python tests/test_tracker.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["WORK_ENCOURAGER_DATA_DIR"] = tempfile.mkdtemp(prefix="we_test_")

import datetime as dt

from work_encourager.messages import fmt_countdown, pick_message
from work_encourager.storage import Settings, State, load_state, save_state
from work_encourager.tracker import Tracker, parse_hhmm, today_str


class FakeClock:
    def __init__(self, wall=None, mono=1_000.0):
        # wall 用真实时间基点，保证 fromtimestamp 推出的日期与 today_str 一致
        self.wall = wall if wall is not None else __import__("time").time()
        self.mono = mono

    def __call__(self):
        return self.wall, self.mono

    def advance(self, w=0.0, m=None):
        self.wall += w
        self.mono += (w if m is None else m)


def make_tracker(status="off", acc=0.0, wage=36.0, date=None, history=None):
    clock = FakeClock()
    state = State(date=date or today_str(), status=status, acc_seconds=acc,
                  history=history or {}, last_save=0.0)
    tracker = Tracker(Settings(salary_value=wage), state, clock=clock)
    return tracker, clock


def test_basic_accumulation():
    t, c = make_tracker()
    t.clock_in()
    assert t.st.status == "working"
    c.advance(w=10.0)
    delta = t.tick()
    assert abs(delta - 10.0) < 1e-6, delta
    assert abs(t.st.acc_seconds - 10.0) < 1e-6
    # 时薪 36 -> 每秒 0.01 元
    assert abs(t.earned_today() - 0.1) < 1e-9
    assert abs(t.per_second() - 0.01) < 1e-12


def test_pause_stops_counting():
    t, c = make_tracker(status="working", acc=100.0)
    t.pause()
    assert t.st.status == "paused"
    c.advance(w=60.0)
    t.tick()
    assert abs(t.st.acc_seconds - 100.0) < 1e-6  # 暂停期间不累计
    t.resume()
    c.advance(w=5.0)
    t.tick()
    assert abs(t.st.acc_seconds - 105.0) < 1e-6


def test_sleep_time_dropped():
    """休眠：wall 走了 2 小时，mono 只走了 0.5 秒 -> 不累计。"""
    t, c = make_tracker(status="working", acc=50.0)
    c.advance(w=7200.0, m=0.5)
    delta = t.tick()
    assert delta == 0.0
    assert abs(t.st.acc_seconds - 50.0) < 1e-6


def test_max_tick_cap():
    """mono 与 wall 同步大步推进（QPC 计休眠的兜底）：单次最多 30 秒。"""
    t, c = make_tracker(status="working", acc=0.0)
    c.advance(w=3600.0, m=3600.0)
    delta = t.tick()
    assert delta <= Tracker.MAX_TICK + 1e-6


def test_clock_rollback():
    """系统时钟被回拨：按 mono 真实流逝计。"""
    t, c = make_tracker(status="working", acc=0.0)
    c.advance(w=-100.0, m=8.0)
    delta = t.tick()
    assert abs(delta - 8.0) < 1e-6


def test_clock_out_archives_today():
    t, c = make_tracker(status="working", acc=3600.0, wage=36.0)
    today = t.st.date
    t.clock_out()
    assert t.st.status == "off"
    rec = t.st.history[today]
    assert abs(rec["seconds"] - 3600.0) < 0.01
    assert abs(rec["earned"] - 36.0) < 1e-6
    assert abs(t.earned_month() - 36.0) < 1e-6  # 本月累计包含今天


def test_rollover_on_tick():
    yest = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    t, c = make_tracker(status="working", acc=100.0, date=yest)
    c.advance(w=5.0)
    t.tick()
    assert t.st.date == today_str()
    assert abs(t.st.history[yest]["seconds"] - 100.0) < 0.01
    assert abs(t.st.acc_seconds - 5.0) < 1e-6  # 新的一天从 0 开始累计


def test_rollover_on_startup():
    yest = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    t, c = make_tracker(status="paused", acc=7200.0, date=yest, wage=36.0)
    assert t.st.date == today_str()
    assert abs(t.st.acc_seconds - 0.0) < 1e-6
    assert abs(t.st.history[yest]["earned"] - 72.0) < 1e-6


def test_state_persistence_roundtrip():
    t, c = make_tracker(status="working", acc=1234.5, wage=20.0)
    t.save(force=True)
    loaded = load_state()
    assert abs(loaded.acc_seconds - 1234.5) < 1e-6
    assert loaded.status == "working"
    t2 = Tracker(Settings(salary_value=20.0), loaded, clock=c)
    assert abs(t2.st.acc_seconds - 1234.5) < 1e-6  # 重开后金额无缝恢复
    assert abs(t2.earned_today() - 1234.5 * 20.0 / 3600.0) < 1e-9


def test_multiple_sessions_per_day():
    t, c = make_tracker(acc=100.0)
    t.clock_in()      # 第二次上班
    c.advance(w=30.0)
    t.tick()
    assert abs(t.st.acc_seconds - 130.0) < 1e-6  # 同一天多段累计
    t.pause()
    t.clock_in()
    c.advance(w=10.0)
    t.tick()
    assert abs(t.st.acc_seconds - 140.0) < 1e-6


def test_countdown_text():
    t, c = make_tracker()
    now = dt.datetime.now()
    t.s.end_time = (now + dt.timedelta(hours=1, minutes=30)).strftime("%H:%M")
    text = t.countdown_text()
    if t.is_workday():
        assert "距离下班还有" in text
        assert "1小时" in text
    t.s.end_time = (now - dt.timedelta(minutes=10)).strftime("%H:%M")
    if t.is_workday():
        assert "已过下班时间" in t.countdown_text()
    # 非工作日
    for d in range(7):
        if dt.date.today().weekday() not in (d,):
            pass
    t.s.workdays = [(dt.date.today().weekday() + 1) % 7]  # 今天必然不是工作日
    assert "今天休息" in t.countdown_text()


def test_parse_and_format():
    assert parse_hhmm("09:05", "09:00") == dt.time(9, 5)
    assert parse_hhmm("bad", "18:30") == dt.time(18, 30)
    assert fmt_countdown(2 * 3600 + 54 * 60 + 18) == "2小时54分18秒"
    assert fmt_countdown(54 * 60 + 5) == "54分05秒"
    assert fmt_countdown(9) == "9秒"


def test_messages():
    msgs = {pick_message(10.0, 0.01, "working") for _ in range(60)}
    assert all(isinstance(m, str) and m for m in msgs)
    assert pick_message(10.0, 0.0, "working")    # rate=0 不崩溃
    assert pick_message(10.0, 0.01, "off")
    assert pick_message(10.0, 0.01, "paused")


def test_monthly_wage_conversion():
    """月薪按 月均工作日 × 每日工时 折算时薪。"""
    s = Settings(salary_type="monthly", salary_value=10000.0,
                 daily_target_hours=7.5, workdays=[0, 1, 2, 3, 4])
    expected = 10000.0 / (5 * 52.0 / 12.0 * 7.5)   # ≈ 61.73 元/时
    assert abs(s.hourly_wage - expected) < 1e-9
    assert abs(s.monthly_workdays - 5 * 52.0 / 12.0) < 1e-9
    # 时薪模式下原样返回
    h = Settings(salary_type="hourly", salary_value=30.0)
    assert h.hourly_wage == 30.0
    # 工作日全部取消时不除零（按 21.75 兜底）
    empty = Settings(salary_type="monthly", salary_value=10000.0,
                     daily_target_hours=7.5, workdays=[])
    assert abs(empty.hourly_wage - 10000.0 / (21.75 * 7.5)) < 1e-9
    # 换算时薪直接参与收入计算：工作满 1 小时 = 折算时薪
    t = Tracker(s, State(date=today_str(), status="working"), clock=FakeClock())
    t.st.acc_seconds = 3600.0
    assert abs(t.earned_today() - expected) < 1e-6


def run_all():
    fails = 0
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS {name}")
        except AssertionError as e:
            fails += 1
            print(f"  FAIL {name}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} tests passed")
    return fails


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
