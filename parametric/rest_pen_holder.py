"""Tombstone-style desk pen holder inspired by the provided reference image."""

from __future__ import annotations

import cadquery as cq

from . import _common as cm

CHINESE_FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"


def _rounded_box(width: float, depth: float, height: float, radius: float) -> cq.Workplane:
    """Rounded-rectangle prism with Z from 0 to height."""
    radius = min(radius, width / 2 - 0.01, depth / 2 - 0.01)
    return cq.Workplane("XY").rect(width, depth).extrude(height).edges("|Z").fillet(radius)


def _box_at(
    width: float,
    depth: float,
    height: float,
    *,
    x: float = 0,
    y: float = 0,
    z: float = 0,
) -> cq.Workplane:
    return cq.Workplane("XY").box(width, depth, height).translate((x, y, z + height / 2))


def _cylinder_at(
    diameter: float,
    height: float,
    *,
    x: float = 0,
    y: float = 0,
    z: float = 0,
) -> cq.Workplane:
    return cq.Workplane("XY").circle(diameter / 2).extrude(height).translate((x, y, z))


def _arch_prism(
    width: float,
    shoulder_height: float,
    thickness: float,
    *,
    front_y: float,
    z: float,
    x: float = 0,
) -> cq.Workplane:
    """Arch profile in XZ, extruded from front_y toward the back by thickness."""
    radius = width / 2
    return (
        cq.Workplane("XZ")
        .moveTo(-radius, 0)
        .lineTo(radius, 0)
        .lineTo(radius, shoulder_height)
        .threePointArc((0, shoulder_height + radius), (-radius, shoulder_height))
        .close()
        .extrude(thickness)
        .translate((x, front_y + thickness, z))
    )


def _text_solid(
    text: str,
    size: float,
    depth: float,
    *,
    x: float,
    front_y: float,
    z: float,
    font: str = "Arial",
    font_path: str | None = None,
) -> cq.Workplane:
    """Text in XZ, extruded from front_y toward the back by depth."""
    return (
        cq.Workplane("XZ")
        .text(text, size, depth, font=font, fontPath=font_path, halign="center", valign="center")
        .translate((x, front_y + depth, z))
    )


def build(
    base_width: float = 150,
    base_depth: float = 110,
    base_height: float = 8,
    tombstone_width: float = 86,
    tombstone_shoulder_height: float = 56,
    tombstone_thickness: float = 7,
    cup_width: float = 84,
    cup_depth: float = 58,
    cup_height: float = 72,
    wall: float = 3.2,
    text_top: str = "REST",
    text_bottom: str = "工位",
) -> cq.Workplane:
    """Build a one-piece printable pen holder.

    Dimensions are in millimeters. The default size is intended for Bambu Studio
    import as a decorative desk organizer, not as a mechanical interface.
    """
    front_y = -20
    panel_bottom_z = base_height + 6
    cup_front_y = front_y + tombstone_thickness
    cup_back_y = cup_front_y + cup_depth
    cup_center_y = (cup_front_y + cup_back_y) / 2

    base = _rounded_box(base_width, base_depth, base_height, 8)
    base = base.edges(">Z").chamfer(1.2)

    # Low plinth under the tombstone, matching the blocky raised strip in the image.
    plinth = _rounded_box(102, 22, 7, 3).translate((0, front_y + 6, base_height))
    plinth = plinth.edges(">Z").chamfer(0.8)

    tombstone = _arch_prism(
        tombstone_width,
        tombstone_shoulder_height,
        tombstone_thickness,
        front_y=front_y,
        z=panel_bottom_z,
    )
    tombstone = tombstone.edges("|Y").fillet(1.0)

    # Recessed center face leaves a raised arched border.
    recess_depth = 1.0
    inner = _arch_prism(
        tombstone_width - 18,
        tombstone_shoulder_height - 10,
        recess_depth,
        front_y=front_y - 0.01,
        z=panel_bottom_z + 9,
    )
    tombstone = tombstone.cut(inner)

    # Engraved lettering. Chinese font availability varies, PingFang is present on macOS.
    letter_front_y = front_y + recess_depth
    tombstone = tombstone.cut(
        _text_solid(
            text_top,
            15,
            3.2,
            x=0,
            front_y=letter_front_y,
            z=panel_bottom_z + 68,
            font="Times New Roman",
        )
    )
    if text_bottom == "工位":
        tombstone = tombstone.cut(
            _text_solid(
                "工",
                22,
                3.8,
                x=0,
                front_y=letter_front_y,
                z=panel_bottom_z + 46,
                font_path=CHINESE_FONT_PATH,
            )
        )
        tombstone = tombstone.cut(
            _text_solid(
                "位",
                22,
                3.8,
                x=0,
                front_y=letter_front_y,
                z=panel_bottom_z + 21,
                font_path=CHINESE_FONT_PATH,
            )
        )
    else:
        tombstone = tombstone.cut(
            _text_solid(
                text_bottom,
                25,
                1.6,
                x=0,
                front_y=letter_front_y,
                z=panel_bottom_z + 34,
                font_path=CHINESE_FONT_PATH,
            )
        )

    # Open pen cup behind the tombstone. The tombstone acts as the front wall.
    bottom = _box_at(cup_width, cup_depth, 3.2, y=cup_center_y, z=base_height)
    back_wall = _box_at(cup_width, wall, cup_height, y=cup_back_y - wall / 2, z=base_height)
    left_wall = _box_at(wall, cup_depth, cup_height, x=-cup_width / 2 + wall / 2, y=cup_center_y, z=base_height)
    right_wall = _box_at(wall, cup_depth, cup_height, x=cup_width / 2 - wall / 2, y=cup_center_y, z=base_height)
    cup = bottom.union(back_wall).union(left_wall).union(right_wall)
    cup = cup.edges("|Z").fillet(0.8)
    cup = cup.edges(">Z").chamfer(0.8)

    # Small front steps and two round posts are decorative references from the photo.
    step_y = -base_depth / 2 + 12
    step1 = _box_at(34, 7, 2.0, y=step_y, z=base_height)
    step2 = _box_at(28, 7, 4.0, y=step_y + 7, z=base_height)
    step3 = _box_at(22, 7, 6.0, y=step_y + 14, z=base_height)

    post_l = _cylinder_at(11, 6, x=-54, y=-36, z=base_height)
    post_r = _cylinder_at(11, 6, x=54, y=-36, z=base_height)
    cap_l = _cylinder_at(8, 2, x=-54, y=-36, z=base_height + 6)
    cap_r = _cylinder_at(8, 2, x=54, y=-36, z=base_height + 6)
    posts = post_l.union(post_r).union(cap_l).union(cap_r)
    posts = posts.edges(">Z").fillet(0.6)

    part = base.union(plinth).union(tombstone).union(cup).union(step1).union(step2).union(step3).union(posts)
    return part


if __name__ == "__main__":
    cm.export(build(), "rest_pen_holder")
