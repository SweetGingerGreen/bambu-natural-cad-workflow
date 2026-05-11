"""
车把卡箍（两件式，2×M 螺丝合拢）。

常见车把直径：22.2 / 25.4 / 31.8 mm。
返回一个字典 {"base": ..., "cap": ...}：base 半边带平台供其他配件接入，cap 是合拢盖。
"""

import cadquery as cq
from . import _common as cm


def build(
    bar_diameter: float = 31.8,
    wall: float = 4.0,
    width: float = 20.0,
    bolt: str = "M5",
    bolt_spacing: float = None,    # 两螺丝中心距，None=自动
    platform_w: float = 30.0,
    platform_h: float = 4.0,       # 平台厚度
):
    """生成两件式车把卡箍。

    Returns dict[str, cq.Workplane] with keys "base", "cap".
    """
    r_in = bar_diameter / 2 + cm.CLEARANCE      # 内圆半径（含间隙）
    r_out = r_in + wall                          # 外圆半径
    if bolt_spacing is None:
        bolt_spacing = 2 * r_out + 4             # 螺丝离外圆约 2mm

    spec = cm.M_SPECS[bolt]
    d_thru = cm.thru_hole_d(bolt)
    head_d = spec["head_d"] + 0.4
    head_h = spec["head_h"] + 0.2
    nut_af = spec["nut_af"] + 0.2
    nut_h = spec["nut_h"] + 0.2

    block_l = bolt_spacing + max(head_d, nut_af) + 4   # X 方向
    block_h = r_out + 2                                # Y 方向（半边高度）

    # 公共：一个矩形块，中央切半圆
    def half_block(is_base: bool):
        # 块中心在原点；z 厚度 = width
        b = (
            cq.Workplane("XY")
            .box(block_l, block_h, width, centered=(True, False, True))
        )
        # 减去半圆（代表车把）
        b = (
            b.faces(">Z").workplane(centerOption="CenterOfMass")
            .moveTo(0, 0)
            .circle(r_in)
            .cutThruAll()
        )
        # 切掉下半圆外的部分（保留上半边或下半边）
        # block 的 y 范围 [0, block_h]，圆心在 (0,0)
        # 是上半部分还是下半部分由 base/cap 决定 —— 这里都用同一形状（对称）
        return b

    half = half_block(True)

    # 合拢面打通孔；base 半侧加沉头供螺丝头进入；cap 半侧加六角螺母槽
    # 两螺丝沿 X 对称布置，沿 Y 方向打孔（合拢方向）
    def add_bolt_holes(part, is_base: bool):
        # 顶面（朝向另一半）= y = 0 方向
        # 我们沿 -Y 方向打孔到块内
        # 选择 <Y 面（合拢面）作为 workplane
        wp = part.faces("<Y").workplane(origin=(0, 0, 0))
        # 在该 workplane 上 (x, z) 坐标系中布两个孔
        wp = wp.pushPoints([(-bolt_spacing/2, 0), (bolt_spacing/2, 0)])
        wp = wp.hole(d_thru, depth=block_h + 1)

        # base：螺母槽在外侧（>Y 面）
        # cap：沉头在外侧（>Y 面）
        outer = part.faces(">Y").workplane(origin=(0, 0, 0))
        outer = outer.pushPoints([(-bolt_spacing/2, 0), (bolt_spacing/2, 0)])
        if is_base:
            # 螺母槽（六角）
            outer = outer.polygon(6, nut_af / 0.866).cutBlind(-nut_h)
        else:
            # 沉头柱形槽
            outer = outer.circle(head_d / 2).cutBlind(-head_h)
        return outer

    base = add_bolt_holes(half, is_base=True)
    cap = add_bolt_holes(half_block(False), is_base=False)

    # base 加底部平台
    plat = (
        cq.Workplane("XY")
        .box(platform_w, platform_h, width, centered=(True, False, True))
        .translate((0, -platform_h, 0))   # 紧贴 base 下沿（block_h 在 +Y 方向）
    )
    # 实际 base 的 y 范围是 [0, block_h]，平台向 -Y 延伸
    base = base.union(plat)

    return {"base": base, "cap": cap}


def make_default():
    return build(bar_diameter=31.8)


if __name__ == "__main__":
    parts = make_default()
    for name, p in parts.items():
        cm.export(p, f"handlebar_clamp_31_8_{name}")
