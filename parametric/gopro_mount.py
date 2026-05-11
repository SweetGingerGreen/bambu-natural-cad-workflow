"""
GoPro 三爪母接口（受体侧），含中央 M5 通孔。

GoPro 标准三爪：
- 三个耳片，每片厚 ~3.0mm
- 总宽 ~22mm（含间隙）
- 中央 M5 螺孔（蝶形螺丝穿过）
- 耳片中心间距 5.5mm
"""

import cadquery as cq
from . import _common as cm


def build(
    finger_count: int = 2,    # 母接口通常是 2 爪（公接口是 3 爪）；亦可设 3
    finger_thickness: float = 3.5,
    gap: float = 3.5,         # 爪间空隙（接公爪 3.0mm + 间隙）
    finger_radius: float = 7.5,   # 爪外半径
    mount_thickness: float = 6.0, # 底座厚度
    mount_size: tuple[float, float] = (24.0, 16.0),  # 底座长宽
    bolt_size: str = "M5",
):
    """生成 GoPro 三爪母接口（带 M5 通孔贯穿三爪）。"""
    total_w = finger_count * finger_thickness + (finger_count - 1) * gap

    # 底座
    base = cq.Workplane("XY").box(
        mount_size[0], mount_size[1], mount_thickness, centered=(True, True, True)
    )

    # 爪片（圆头长方形，沿 X 排列）
    fingers = None
    x_start = -total_w / 2 + finger_thickness / 2
    for i in range(finger_count):
        x = x_start + i * (finger_thickness + gap)
        # 一个圆头 finger：圆+矩形结合
        finger = (
            cq.Workplane("YZ")
            .moveTo(0, mount_thickness / 2)   # 起点在底座顶
            .circle(finger_radius)
            .extrude(finger_thickness)
            .translate((x - finger_thickness / 2, 0, 0))
        )
        fingers = finger if fingers is None else fingers.union(finger)

    part = base.union(fingers) if fingers is not None else base

    # 中央 M5 贯穿孔（沿 X 方向）
    d = cm.thru_hole_d(bolt_size)
    part = (
        part.faces(">X")
        .workplane(centerOption="CenterOfMass")
        .moveTo(0, mount_thickness / 2)
        .hole(d)
    )

    return part


if __name__ == "__main__":
    p = build()
    cm.export(p, "gopro_mount_2finger")
