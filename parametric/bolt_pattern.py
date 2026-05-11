"""
通用螺孔阵列工具：在已有 part 上按 (x, y) 列表打通孔（带螺母槽）。
"""

import cadquery as cq
from . import _common as cm


def add_holes(part: cq.Workplane,
              points: list[tuple[float, float]],
              m_size: str = "M5",
              plate_thickness: float = None,
              with_nut_pocket: bool = True,
              top_face: str = ">Z",
              bottom_face: str = "<Z") -> cq.Workplane:
    """
    在 part 顶面（top_face）按 points 打通孔。
    如果 with_nut_pocket=True，则在底面（bottom_face）开六角螺母槽。

    plate_thickness: 通孔深度（=板厚）；None 则贯穿。
    """
    spec = cm.M_SPECS[m_size]
    d_thru = cm.thru_hole_d(m_size)
    nut_af = spec["nut_af"] + 0.2
    nut_h = spec["nut_h"] + 0.2

    wp = part.faces(top_face).workplane(centerOption="CenterOfMass")
    wp = wp.pushPoints(points)
    if plate_thickness:
        wp = wp.hole(d_thru, depth=plate_thickness + 0.5)
    else:
        wp = wp.cutThruAll() if False else wp.hole(d_thru)  # hole 默认贯穿

    if with_nut_pocket:
        wp2 = wp.faces(bottom_face).workplane(centerOption="CenterOfMass")
        wp2 = wp2.pushPoints(points)
        wp = wp2.polygon(6, nut_af / 0.866).cutBlind(-nut_h)

    return wp


def grid(rows: int, cols: int, dx: float, dy: float) -> list[tuple[float, float]]:
    """生成 (rows×cols) 网格点，居中。"""
    pts = []
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * dx
            y = (r - (rows - 1) / 2) * dy
            pts.append((x, y))
    return pts


if __name__ == "__main__":
    # 演示：100×60×4 板，4 个 M5 角孔
    plate = cq.Workplane("XY").box(100, 60, 4, centered=True)
    plate = add_holes(plate, grid(2, 2, 80, 40), m_size="M5", plate_thickness=4)
    cm.export(plate, "demo_bolt_plate")
