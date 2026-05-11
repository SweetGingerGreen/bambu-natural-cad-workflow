"""
自行车水壶架（标准车架孔距 64mm，M5 安装）。

设计：背板 + 柔性环抱（一个开口圆环 + 底托）。
"""

import cadquery as cq
from . import _common as cm
from . import bolt_pattern as bp


def build(
    bottle_diameter: float = 75.0,    # 75=保温壶常见，73=550ml 标准
    cage_height: float = 110.0,       # 沿水壶轴向的总高度
    bottle_grip_count: int = 2,       # 几道环抱
    backplate_w: float = 35.0,
    backplate_t: float = 5.0,
    mount_hole_spacing: float = 64.0, # 标准车架
    bolt_size: str = "M5",
    ring_thickness: float = 4.0,
    ring_open_angle: float = 90.0,    # 开口角度（度）
):
    """生成水壶架。返回单一 part。"""
    import math
    r_bottle = bottle_diameter / 2 + cm.CLEARANCE
    r_outer = r_bottle + ring_thickness

    # 背板（沿 Z 轴方向是高度，X 是宽度，Y 是厚度）
    backplate = cq.Workplane("XY").box(
        backplate_w, backplate_t, cage_height,
        centered=(True, True, True),
    )
    # 倒圆角防应力集中
    backplate = backplate.edges("|Y").fillet(2.0)

    # 安装孔（沿 Z 方向 64mm）
    pts = [(0, mount_hole_spacing / 2), (0, -mount_hole_spacing / 2)]
    backplate = bp.add_holes(
        backplate, pts, m_size=bolt_size,
        plate_thickness=backplate_t,
        with_nut_pocket=False,           # 通孔即可，背面贴车架
        top_face=">Y", bottom_face="<Y",
    )

    # 环抱圆（在每个 grip 高度位置画一个开口环）
    rings = None
    grip_zs = []
    if bottle_grip_count == 1:
        grip_zs = [0]
    else:
        # 均布
        gap = (cage_height - 30) / (bottle_grip_count - 1)
        for i in range(bottle_grip_count):
            z = -(cage_height/2) + 15 + i * gap
            grip_zs.append(z)

    # 环的圆心在 (X=r_outer + backplate_t/2, Y=0)；开口朝 +X 方向
    center_x = backplate_t / 2 + r_outer

    for z in grip_zs:
        # 画一个 (360 - open_angle) 弧线扫掠成环
        # 简化：先画完整圆环，再切出开口扇形
        ring = (
            cq.Workplane("XY", origin=(center_x, 0, z))
            .circle(r_outer).circle(r_bottle)
            .extrude(8.0, both=True)  # 厚 16mm
        )
        # 切开口（朝 +X）
        if ring_open_angle > 0:
            half_angle = ring_open_angle / 2
            cutter = (
                cq.Workplane("XY", origin=(center_x, 0, z))
                .moveTo(0, 0)
                .lineTo(r_outer * 1.5 * math.cos(math.radians(half_angle)),
                        r_outer * 1.5 * math.sin(math.radians(half_angle)))
                .lineTo(r_outer * 1.5 * math.cos(math.radians(-half_angle)),
                        r_outer * 1.5 * math.sin(math.radians(-half_angle)))
                .close()
                .extrude(20, both=True)
            )
            ring = ring.cut(cutter)
        rings = ring if rings is None else rings.union(ring)

    # 把环连到背板：在背板对应高度加连接桥
    bridges = None
    for z in grip_zs:
        bridge = (
            cq.Workplane("XY", origin=(0, 0, z))
            .box(8, backplate_t / 2 + r_outer * 2 + 1, 14, centered=(True, False, True))
            .translate((0, -backplate_t / 2, 0))
            # bridge 横跨从背板正面 (-backplate_t/2 + backplate_t = backplate_t/2) 到环中心+r_outer
        )
        # 简化：用一个矩形连过去（其实需要更精细的合并），让 union 处理
        bridges = bridge if bridges is None else bridges.union(bridge)

    part = backplate.union(rings) if rings is not None else backplate
    if bridges is not None:
        part = part.union(bridges)

    return part


if __name__ == "__main__":
    p = build()
    cm.export(p, "water_bottle_cage_75mm")
