"""One-piece open nest orb for six large air plants."""

from __future__ import annotations

import math

import cadquery as cq

from . import _common as cm


Point = tuple[float, float, float]


def _rod_between(start: Point, end: Point, radius: float) -> cq.Workplane:
    vx, vy, vz = (end[0] - start[0], end[1] - start[1], end[2] - start[2])
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    direction = (vx / length, vy / length, vz / length)

    rod = cq.Workplane("XY").circle(radius).extrude(length)
    dot = max(-1.0, min(1.0, direction[2]))
    angle = math.degrees(math.acos(dot))
    axis = (-direction[1], direction[0], 0)
    axis_len = math.sqrt(axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2)
    if axis_len > 1e-6:
        axis = (axis[0] / axis_len, axis[1] / axis_len, axis[2] / axis_len)
        rod = rod.rotate((0, 0, 0), axis, angle)
    elif direction[2] < 0:
        rod = rod.rotate((0, 0, 0), (1, 0, 0), 180)
    return rod.translate(start)


def _sphere_at(point: Point, radius: float) -> cq.Workplane:
    return cq.Workplane("XY").sphere(radius).translate(point)


def _torus_like_loop(center: Point, outer_r: float, tube_r: float) -> cq.Workplane:
    outer = cq.Workplane("XY").circle(outer_r + tube_r).extrude(tube_r * 2)
    inner = cq.Workplane("XY").circle(outer_r - tube_r).extrude(tube_r * 2 + 1).translate((0, 0, -0.5))
    return outer.cut(inner).translate((center[0], center[1], center[2] - tube_r))


def _point(radius: float, z: float, angle_deg: float) -> Point:
    angle = math.radians(angle_deg)
    return (radius * math.cos(angle), radius * math.sin(angle), z)


def build(
    outer_d: float = 116,
    height: float = 108,
    rib_r: float = 3.2,
    node_r: float = 5.0,
    top_loop_inner_d: float = 16,
) -> cq.Workplane:
    """Build a printable open orb.

    Six large triangular windows are left intentionally open. Air plants are
    inserted into those windows, and their leaves form the visible flower ball.
    """
    r = outer_d / 2
    bottom_z = 7
    lower_z = height * 0.32
    upper_z = height * 0.68
    top_z = height - 4

    lower = [_point(r * 0.80, lower_z, a) for a in (30, 150, 270)]
    upper = [_point(r * 0.80, upper_z, a) for a in (90, 210, 330)]
    bottom = [_point(r * 0.42, bottom_z, a) for a in (90, 210, 330)]
    top = [_point(r * 0.36, top_z, a) for a in (30, 150, 270)]

    center_bottom = (0, 0, node_r)
    top_center = (0, 0, top_z)
    nodes = lower + upper + bottom + top + [center_bottom, top_center]
    part = _sphere_at(nodes[0], node_r)
    for p in nodes[1:]:
        part = part.union(_sphere_at(p, node_r))

    # Six side ribs form large insertion windows instead of dense honeycomb.
    for i in range(3):
        part = part.union(_rod_between(lower[i], upper[i], rib_r))
        part = part.union(_rod_between(lower[i], upper[(i - 1) % 3], rib_r))
        part = part.union(_rod_between(lower[i], bottom[i], rib_r))
        part = part.union(_rod_between(upper[i], top[i], rib_r))
        part = part.union(_rod_between(bottom[i], center_bottom, rib_r * 0.95))
        part = part.union(_rod_between(top[i], top_center, rib_r * 0.95))

    # Upper/lower rings keep the orb coherent and create a woven nest silhouette.
    for i in range(3):
        part = part.union(_rod_between(lower[i], lower[(i + 1) % 3], rib_r))
        part = part.union(_rod_between(upper[i], upper[(i + 1) % 3], rib_r))
        part = part.union(_rod_between(bottom[i], bottom[(i + 1) % 3], rib_r * 0.9))
        part = part.union(_rod_between(top[i], top[(i + 1) % 3], rib_r * 0.9))

    # Top hanging loop and braces.
    loop_z = height + 12
    loop_outer = cq.Workplane("XZ").center(0, loop_z).circle(top_loop_inner_d / 2 + rib_r).extrude(rib_r * 2)
    loop_inner = (
        cq.Workplane("XZ")
        .center(0, loop_z)
        .circle(top_loop_inner_d / 2)
        .extrude(rib_r * 2 + 1)
        .translate((0, -0.5, 0))
    )
    loop = loop_outer.cut(loop_inner).translate((0, -rib_r, 0))
    part = part.union(loop)
    part = part.union(_rod_between(top_center, (0, 0, loop_z - 6), rib_r))
    part = part.union(_rod_between((-7, 0, top_z - 1), (-7, 0, loop_z - 6), rib_r * 0.85))
    part = part.union(_rod_between((7, 0, top_z - 1), (7, 0, loop_z - 6), rib_r * 0.85))

    try:
        part = part.combine(clean=True, tol=0.05)
    except Exception:
        try:
            part = part.clean()
        except Exception:
            pass
    return part


if __name__ == "__main__":
    cm.export(build(), "air_plant_nest_orb_v2")
