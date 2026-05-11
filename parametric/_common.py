"""
全局工程常量 + 通用 CadQuery 工具。

校准件打印实测后，更新 HOLE_OFFSET / SLIDE_FIT_OFFSET 即可让所有模板生效。
"""

import cadquery as cq
from pathlib import Path

# ---------- 校准参数（打 hole_test_card 后更新这里） ----------
HOLE_OFFSET = 0.30          # 通孔放大量 (mm)，初始经验值 0.3
SLIDE_FIT_OFFSET = 0.20     # 紧配合销孔放大量 (mm)
CLEARANCE = 0.30            # 一般间隙 (mm)

# ---------- 公制螺丝标准尺寸表 ----------
# (孔径名义, 螺母对边宽 across-flats, 螺母厚, 头部直径, 头部厚)
M_SPECS = {
    "M3": {"d": 3.0, "nut_af": 5.5, "nut_h": 2.4, "head_d": 5.5, "head_h": 3.0},
    "M4": {"d": 4.0, "nut_af": 7.0, "nut_h": 3.2, "head_d": 7.0, "head_h": 4.0},
    "M5": {"d": 5.0, "nut_af": 8.0, "nut_h": 4.0, "head_d": 8.5, "head_h": 5.0},
    "M6": {"d": 6.0, "nut_af": 10.0, "nut_h": 5.0, "head_d": 10.0, "head_h": 6.0},
}

# ---------- 输出路径 ----------
ROOT = Path(__file__).resolve().parents[1]
STEP_DIR = ROOT / "output" / "step"
STL_DIR = ROOT / "output" / "stl"
STEP_DIR.mkdir(parents=True, exist_ok=True)
STL_DIR.mkdir(parents=True, exist_ok=True)


def export(part: cq.Workplane, name: str, formats=("step", "stl")) -> dict:
    """统一导出。返回 {format: path}。"""
    paths = {}
    if "step" in formats:
        p = STEP_DIR / f"{name}.step"
        cq.exporters.export(part, str(p))
        paths["step"] = str(p)
    if "stl" in formats:
        p = STL_DIR / f"{name}.stl"
        cq.exporters.export(part, str(p), tolerance=0.01, angularTolerance=0.1)
        paths["stl"] = str(p)
    return paths


def thru_hole_d(m_size: str) -> float:
    """带补偿的通孔直径。"""
    return M_SPECS[m_size]["d"] + HOLE_OFFSET


def hex_pocket(width: float, depth: float) -> cq.Workplane:
    """生成一个六角螺母槽（across-flats=width，深 depth），可与 cut 配合使用。"""
    return cq.Workplane("XY").polygon(6, width / 0.866, forConstruction=False).extrude(depth)


def add_bolt_hole_with_nut(part: cq.Workplane, m_size: str,
                           length: float, nut_depth_from_back: float = 4.0,
                           normal: str = "Z"):
    """
    在 part 当前选中的 face 中心打一个 M 螺丝通孔 + 背面六角螺母槽。
    length: 板厚（贯穿）
    nut_depth_from_back: 螺母槽离背面深度
    normal: "Z"（沿 Z 钻），其他方向需先旋转 workplane
    """
    spec = M_SPECS[m_size]
    d_thru = thru_hole_d(m_size)
    nut_af = spec["nut_af"] + 0.2
    nut_h = spec["nut_h"] + 0.2

    part = part.faces(f">{normal}").workplane().hole(d_thru, depth=length)
    # 背面六角槽（注意 Z 反向）
    part = (
        part.faces(f"<{normal}")
        .workplane()
        .polygon(6, nut_af / 0.866)
        .cutBlind(-nut_h)
    )
    return part
