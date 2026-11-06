"""PyInstaller 打包脚本：生成 dist/上班鼓励器.exe

用法: python build_exe.py
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(ROOT, "assets", "icon.ico")


def main() -> int:
    if not os.path.exists(ICON):
        print("warning: assets/icon.ico 不存在，将不带图标打包")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--windowed", "--onefile",
        "--name", "上班鼓励器",
        "--distpath", os.path.join(ROOT, "dist"),
        "--workpath", os.path.join(ROOT, "build"),
        "--specpath", os.path.join(ROOT, "build"),
        os.path.join(ROOT, "run.py"),
    ]
    if os.path.exists(ICON):
        cmd += ["--icon", ICON]

    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)
    exe = os.path.join(ROOT, "dist", "上班鼓励器.exe")
    print("\nDone:", exe, f"({os.path.getsize(exe) / 1e6:.1f} MB)" if os.path.exists(exe) else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
