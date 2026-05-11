"""
31.8mm 卡箍测试环：单环（开口 60°），用同一份代码测三种内径补偿。

打印一个最小化的"卡箍单半"，套到真实 31.8 车把上验证：
- 内径合不合（紧/松）
- 卡箍开合是否能用 M5 螺丝拧紧

把结果告诉 Claude（"31.8 这个略松"），它会调 CLEARANCE 或 wall。
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from parametric import handlebar_clamp as hc
from parametric import _common as cm


def build():
    parts = hc.build(bar_diameter=31.8, width=14.0, platform_w=10.0)
    return parts


if __name__ == "__main__":
    parts = build()
    for name, p in parts.items():
        cm.export(p, f"cal_ring_31_8_{name}")
