"""
鹿角蕨板/挂墙花盆。

参数：
- length / width / height：内尺寸（容积）
- wall：壁厚
- drain_holes：底部排水孔个数（自动均布）
- mount_holes：上沿挂墙螺孔个数（默认 2，标准 M5）
"""

import cadquery as cq
from . import _common as cm
from . import bolt_pattern as bp


def build(
    length: float = 300.0,    # 内长（mm）
    width: float = 200.0,     # 内宽（沿墙方向，"深度"）
    height: float = 80.0,     # 内高（往外伸）
    wall: float = 2.4,
    floor: float = 3.0,
    drain_holes: int = 4,
    drain_d: float = 6.0,
    mount_holes: int = 2,
    mount_bolt: str = "M5",
    mount_inset: float = 12.0,  # 螺孔距上沿的下移距离
    fillet_outer: float = 2.0,
):
    """生成挂墙花盆，返回单一 part。"""
    L = length + 2 * wall
    W = width + 2 * wall
    H = height + floor

    # 实心外壳
    outer = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))
    # 内空腔
    cavity = (
        cq.Workplane("XY", origin=(0, 0, floor))
        .box(length, width, height + 1, centered=(True, True, False))
    )
    part = outer.cut(cavity)

    # 外圆角
    if fillet_outer > 0:
        try:
            part = part.edges("|Z").fillet(fillet_outer)
        except Exception:
            pass

    # 底部排水孔（沿 length 方向均布）
    if drain_holes > 0:
        xs = [(i + 0.5) / drain_holes * length - length / 2 for i in range(drain_holes)]
        pts = [(x, 0) for x in xs]
        part = (
            part.faces("<Z").workplane(centerOption="CenterOfMass")
            .pushPoints(pts)
            .hole(drain_d, depth=floor + 0.5)
        )

    # 挂墙螺孔（在背面 -Y 那一壁上）
    # 默认背面是 -Y 朝向墙
    if mount_holes > 0:
        spec = cm.M_SPECS[mount_bolt]
        d_thru = cm.thru_hole_d(mount_bolt)
        head_d = spec["head_d"] + 0.6
        # 螺孔位置：上沿向下 mount_inset，沿 X 均布
        z_hole = H - mount_inset
        if mount_holes == 1:
            xs = [0]
        else:
            xs = [(i / (mount_holes - 1) - 0.5) * (length * 0.7) for i in range(mount_holes)]
        # 在 -Y 面打孔
        wp = part.faces("<Y").workplane(centerOption="CenterOfMass")
        # workplane 上的坐标：x' = world_x，y' = world_z - H/2（因为 face 居中在 H/2）
        for x in xs:
            local_y = z_hole - H / 2
            wp = wp.moveTo(x, local_y).hole(d_thru)
        part = wp

        # 沉头/钥匙孔（让螺丝头能挂上）：在内侧加一个钥匙孔形状
        # 简化：在 -Y 面外侧挖一个浅圆沉头让螺丝头平
        wp2 = part.faces("<Y").workplane(centerOption="CenterOfMass")
        for x in xs:
            local_y = z_hole - H / 2
            wp2 = wp2.moveTo(x, local_y).circle(head_d / 2).cutBlind(-2.0)
        part = wp2

    return part


if __name__ == "__main__":
    p = build(length=300, width=200, height=80)
    cm.export(p, "planter_30x20x8")
