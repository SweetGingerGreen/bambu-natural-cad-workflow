"""
GoPro 三爪小样：复用 gopro_mount.build，缩短底座只测爪部配合。

打印后跟手头任何 GoPro 配件（公爪）配，看蝶形螺丝能否对穿。
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from parametric import gopro_mount as gm
from parametric import _common as cm


def build():
    return gm.build(
        finger_count=2,
        mount_size=(20.0, 14.0),
        mount_thickness=4.0,
    )


if __name__ == "__main__":
    p = build()
    cm.export(p, "cal_gopro_mini")
