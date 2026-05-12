"""Build a cleaner E2-derived staghorn board without stacked center disks."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


def find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "parametric").is_dir() and (parent / "output").is_dir():
            return parent
    return Path(__file__).resolve().parents[1]


ROOT = find_repo_root()
DEFAULT_IMAGE = ROOT / "input" / "staghorn_e2_reference.png"
OUT_STL = ROOT / "output/stl/staghorn_e2_clean_v3.stl"
OUT_MASK = ROOT / "output/preview/staghorn_e2_clean_v3_mask.png"


def largest_component(mask: np.ndarray) -> np.ndarray:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n <= 1:
        return mask
    idx = max(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA])
    return (labels == idx).astype(np.uint8) * 255


def extract_material_mask(image_path: Path) -> tuple[np.ndarray, tuple[int, int, int, int], tuple[float, float]]:
    im = Image.open(image_path).convert("RGB")
    crop = im.crop((520, 120, 820, 575))
    rgb = np.array(crop)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    mask = np.zeros(gray.shape, np.uint8)
    rect = (25, 30, 250, 385)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 8, cv2.GC_INIT_WITH_RECT)
    outer = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)
    outer = largest_component(outer)

    holes = ((gray < 200) & (outer > 0)).astype(np.uint8) * 255
    holes = cv2.morphologyEx(holes, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats(holes, 8)
    keep = np.zeros_like(holes)
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        # Keep the obvious apertures, but discard image-border shadows and text.
        if 12 <= area <= 2300 and x > 23 and y > 47 and x + w < 276 and y + h < 426:
            keep[labels == i] = 255

    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    material = ((outer > 0) & (keep == 0)).astype(np.uint8) * 255
    material = cv2.morphologyEx(material, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    material = largest_component(material)

    ys, xs = np.nonzero(material)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    disk_center_px = (151.5, 276.0)
    return material, bbox, disk_center_px


def mask_to_polygon(mask: np.ndarray, bbox: tuple[int, int, int, int], target_h: float = 224.0):
    x0, y0, x1, y1 = bbox
    scale = target_h / (y1 - y0)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)
    if hierarchy is None:
        raise RuntimeError("No contours found")
    hierarchy = hierarchy[0]

    polys: list[Polygon] = []
    for i, contour in enumerate(contours):
        if hierarchy[i][3] != -1 or cv2.contourArea(contour) < 100:
            continue

        approx = cv2.approxPolyDP(contour, 1.35, True)
        outer = [((float(p[0]) - cx) * scale, (cy - float(p[1])) * scale) for p in approx[:, 0, :]]

        holes = []
        child = hierarchy[i][2]
        while child != -1:
            hcontour = contours[child]
            if cv2.contourArea(hcontour) > 16:
                happ = cv2.approxPolyDP(hcontour, 1.2, True)
                hole = [((float(p[0]) - cx) * scale, (cy - float(p[1])) * scale) for p in happ[:, 0, :]]
                if len(hole) >= 4:
                    holes.append(hole)
            child = hierarchy[child][0]

        poly = Polygon(outer, holes).buffer(0)
        if not poly.is_empty:
            polys.append(poly)

    merged = unary_union(polys).buffer(0)
    if merged.geom_type != "Polygon":
        merged = max(merged.geoms, key=lambda g: g.area)

    # Round off raster stair-steps without closing the E2-style apertures.
    smoothed = merged.buffer(1.15, resolution=8, join_style=1).buffer(-1.15, resolution=8, join_style=1)
    if smoothed.geom_type != "Polygon":
        smoothed = max(smoothed.geoms, key=lambda g: g.area)
    return smoothed.buffer(0), scale, (cx, cy)


def clean_center_disk(poly: Polygon, scale: float, origin_px: tuple[float, float], disk_center_px: tuple[float, float]) -> Polygon:
    cx, cy = origin_px
    dcx = (disk_center_px[0] - cx) * scale
    dcy = (cy - disk_center_px[1]) * scale
    center = Point(dcx, dcy)

    # Replace the traced center completely. The source concept has shadows and
    # rings around the circular disk; keeping that area and adding a clean disk
    # creates the visible "two overlapped circles" failure. Remove a larger
    # circular zone first, then put back exactly one disk.
    clear_zone = center.buffer(37.0, resolution=96)
    disk = center.buffer(42.0, resolution=96)
    tie_holes = [center.buffer(3.0, resolution=24)]
    for r, count, start in [(18.0, 8, 22.5), (29.0, 16, 0)]:
        for i in range(count):
            a = np.deg2rad(start + i * 360 / count)
            tie_holes.append(Point(dcx + r * np.cos(a), dcy + r * np.sin(a)).buffer(2.0, resolution=18))

    return poly.difference(clear_zone).union(disk).difference(unary_union(tie_holes)).buffer(0)


def save_preview(poly: Polygon) -> None:
    minx, miny, maxx, maxy = poly.bounds
    scale = 3.0
    pad = 12
    w = int((maxx - minx) * scale + 2 * pad)
    h = int((maxy - miny) * scale + 2 * pad)
    img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(img)

    def tx(pt):
        x, y = pt
        return ((x - minx) * scale + pad, (maxy - y) * scale + pad)

    draw.polygon([tx(p) for p in poly.exterior.coords], fill=255)
    for ring in poly.interiors:
        draw.polygon([tx(p) for p in ring.coords], fill=0)

    img.save(OUT_MASK)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trace an E2-style staghorn board concept image into an STL.")
    parser.add_argument(
        "--image",
        type=Path,
        default=DEFAULT_IMAGE,
        help="Path to the concept/reference image. Defaults to input/staghorn_e2_reference.png.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = args.image.expanduser().resolve()
    if not image_path.exists():
        raise SystemExit(
            f"Reference image not found: {image_path}\n"
            "Pass one with --image, or place it at input/staghorn_e2_reference.png."
        )

    OUT_STL.parent.mkdir(parents=True, exist_ok=True)
    OUT_MASK.parent.mkdir(parents=True, exist_ok=True)

    mask, bbox, disk_center_px = extract_material_mask(image_path)
    poly, scale, origin_px = mask_to_polygon(mask, bbox)
    poly = clean_center_disk(poly, scale, origin_px, disk_center_px)
    if poly.geom_type != "Polygon":
        poly = max(poly.geoms, key=lambda g: g.area)

    save_preview(poly)
    mesh = trimesh.creation.extrude_polygon(poly, height=10.5)
    mesh.export(OUT_STL)

    print(f"wrote {OUT_STL}")
    print(f"preview {OUT_MASK}")
    print("bounds", mesh.bounds.tolist())
    print("extents", mesh.extents.tolist())


if __name__ == "__main__":
    main()
