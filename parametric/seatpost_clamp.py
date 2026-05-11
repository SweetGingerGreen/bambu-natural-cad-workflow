"""
座管夹（两件式，与 handlebar_clamp 共用结构，参数不同）。

常见座管直径：27.2 / 30.9 / 31.6 mm。
"""

from . import handlebar_clamp as hc
from . import _common as cm


def build(
    post_diameter: float = 27.2,
    wall: float = 4.5,            # 座管夹略厚一点
    width: float = 22.0,
    bolt: str = "M5",
    platform_w: float = 30.0,
    platform_h: float = 4.0,
):
    """座管夹。复用 handlebar_clamp.build。"""
    return hc.build(
        bar_diameter=post_diameter,
        wall=wall,
        width=width,
        bolt=bolt,
        platform_w=platform_w,
        platform_h=platform_h,
    )


if __name__ == "__main__":
    parts = build(post_diameter=27.2)
    for name, p in parts.items():
        cm.export(p, f"seatpost_clamp_27_2_{name}")
