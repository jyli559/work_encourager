"""生成 assets/icon.ico（多尺寸）。开发辅助脚本，需要 PySide6 + Pillow。

用法: python tools/gen_icon.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> int:
    from PySide6.QtWidgets import QApplication
    app = QApplication([])

    from work_encourager.icon import make_pixmap

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "icon.ico")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    pngs = []
    for s in SIZES:
        pm = make_pixmap(s, "working")
        path = os.path.join(tempfile.mkdtemp(prefix="we_icon_"), f"{s}.png")
        if not pm.save(path, "PNG"):
            print(f"save png failed: {s}")
            return 1
        pngs.append(path)

    try:
        from PIL import Image
    except ImportError:
        # 无 Pillow 时退化为 Qt 单尺寸 ico
        ok = make_pixmap(256, "working").save(out, "ICO")
        print("multi-size failed, fallback:", out, "ok =", ok)
        return 0 if ok else 1

    imgs = [Image.open(p).convert("RGBA") for p in pngs]  # 小 -> 大
    largest = imgs[-1]
    largest.save(out, format="ICO",
                 append_images=imgs[:-1],
                 sizes=[(s, s) for s in SIZES],
                 bitmap_format="png")
    print("icon written:", out, os.path.getsize(out), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
