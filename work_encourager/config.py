"""应用常量与路径。"""

import os

APP_NAME = "上班鼓励器"
APP_ID = "WorkEncourager"
VERSION = "1.0.0"


def data_dir() -> str:
    """数据目录（设置与状态 JSON）。可用环境变量 WORK_ENCOURAGER_DATA_DIR 覆盖。"""
    d = os.environ.get("WORK_ENCOURAGER_DATA_DIR")
    if not d:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(base, APP_ID)
    os.makedirs(d, exist_ok=True)
    return d
