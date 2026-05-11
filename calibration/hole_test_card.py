"""
螺孔配合测试卡：M3/M4/M5/M6 各 3 个不同补偿量孔。

打印后用对应规格的螺丝穿过，记录哪个孔顺/紧/松。
把"最顺"的补偿量告诉 Claude，更新 _common.py 的 HOLE_OFFSET。

布局（俯视）：
  M3: +0.2  +0.3  +0.4
  M4: +0.2  +0.3  +0.4
  M5: +0.2  +0.3  +0.4
  M6: +0.2  +0.3  +0.4
"""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

import cadquery as cq
from parametric import _common as cm


def build():
    sizes = ["M3", "M4", "M5", "M6"]
    offsets = [0.2, 0.3, 0.4]
    pitch_x = 14.0   # 列间距
    pitch_y = 14.0   # 行间距
    margin = 8.0
    thickness = 4.0

    cols = len(offsets)
    rows = len(sizes)
    plate_w = cols * pitch_x + 2 * margin
    plate_h = rows * pitch_y + 2 * margin

    plate = cq.Workplane("XY").box(plate_w, plate_h, thickness, centered=True)

    # 在每个网格点钻孔
    for r, m in enumerate(sizes):
        nominal = cm.M_SPECS[m]["d"]
        for c, off in enumerate(offsets):
            x = (c - (cols - 1) / 2) * pitch_x
            y = (r - (rows - 1) / 2) * pitch_y
            d = nominal + off
            plate = (
                plate.faces(">Z")
                .workplane(centerOption="CenterOfMass")
                .moveTo(x, y)
                .hole(d, depth=thickness + 0.5)
            )

    # 在每行/每列旁边阴刻文字标记（CadQuery text emboss/cut）
    for r, m in enumerate(sizes):
        y = (r - (rows - 1) / 2) * pitch_y
        plate = (
            plate.faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .moveTo(-plate_w / 2 + margin / 2, y)
            .text(m, fontsize=4, distance=-0.6, valign="center", halign="center")
        )
    for c, off in enumerate(offsets):
        x = (c - (cols - 1) / 2) * pitch_x
        plate = (
            plate.faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .moveTo(x, plate_h / 2 - margin / 2)
            .text(f"+{off:.1f}", fontsize=3, distance=-0.6, valign="center", halign="center")
        )

    return plate


if __name__ == "__main__":
    p = build()
    cm.export(p, "cal_hole_test_card")
