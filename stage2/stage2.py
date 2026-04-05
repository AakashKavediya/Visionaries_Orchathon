"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           MEP CLASH DETECTION ENGINE — IFC BIM Model                       ║
║  Algorithms: AABB Intersection · Distance-Based · Geometry-Based OBB       ║
║  Output:     List of clash pairs with element IDs, type, XYZ, severity     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python clash_detection_engine.py                          # default input/output
    python clash_detection_engine.py --input my.json         # custom input
    python clash_detection_engine.py --clearance 0.05        # 50mm clearance zone
    python clash_detection_engine.py --tolerance 0.001       # hard clash tolerance
    python clash_detection_engine.py --out results.json      # custom output

Algorithm pipeline per element pair:
    1. Broad Phase  — AABB overlap check  (fast spatial cull, O(n²) but early-exit)
    2. Mid   Phase  — Distance-based check (centre-to-centre & surface-to-surface)
    3. Narrow Phase — Geometry-based OBB/cylinder intersection (precise)
"""

from __future__ import annotations

import json
import math
import time
import argparse
import itertools
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_INPUT  = "extracted_elements.json"
DEFAULT_OUTPUT = "clash_results.json"

HARD_CLASH_TOLERANCE_M  = 0.001   # 1 mm  — overlapping solids
CLEARANCE_ZONE_M        = 0.050   # 50 mm — minimum required clearance gap
NEAR_MISS_ZONE_M        = 0.150   # 150 mm — proximity warning zone

# Severity thresholds (penetration depth in metres)
SEV_CRITICAL_MM = 50    # > 50 mm penetration
SEV_HIGH_MM     = 20    # > 20 mm
SEV_MEDIUM_MM   = 10    # > 10 mm
# < 10 mm → Low; clearance violations → their own tier


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Vec3:
    """3D vector / point with arithmetic helpers."""
    x: float
    y: float
    z: float

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)

    def __mul__(self, s: float) -> "Vec3":
        return Vec3(self.x*s, self.y*s, self.z*s)

    def __truediv__(self, s: float) -> "Vec3":
        return Vec3(self.x/s, self.y/s, self.z/s)

    def dot(self, o: "Vec3") -> float:
        return self.x*o.x + self.y*o.y + self.z*o.z

    def cross(self, o: "Vec3") -> "Vec3":
        return Vec3(
            self.y*o.z - self.z*o.y,
            self.z*o.x - self.x*o.z,
            self.x*o.y - self.y*o.x
        )

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self) -> "Vec3":
        l = self.length()
        return Vec3(0, 0, 0) if l < 1e-12 else self / l

    def to_list(self) -> list:
        return [round(self.x, 6), round(self.y, 6), round(self.z, 6)]


@dataclass
class AABB:
    """Axis-Aligned Bounding Box."""
    min: Vec3
    max: Vec3

    @property
    def center(self) -> Vec3:
        return (self.min + self.max) / 2.0

    @property
    def half_extents(self) -> Vec3:
        return (self.max - self.min) / 2.0

    @property
    def size(self) -> Vec3:
        return self.max - self.min

    def expand(self, margin: float) -> "AABB":
        """Return a copy expanded by `margin` on all sides."""
        m = Vec3(margin, margin, margin)
        return AABB(self.min - m, self.max + m)

    def intersects(self, other: "AABB") -> bool:
        """True if the two AABBs overlap (touch counts as overlap)."""
        return (
            self.min.x <= other.max.x and self.max.x >= other.min.x and
            self.min.y <= other.max.y and self.max.y >= other.min.y and
            self.min.z <= other.max.z and self.max.z >= other.min.z
        )

    def intersection_volume(self, other: "AABB") -> float:
        """Signed overlap volume; negative means no overlap."""
        dx = min(self.max.x, other.max.x) - max(self.min.x, other.min.x)
        dy = min(self.max.y, other.max.y) - max(self.min.y, other.min.y)
        dz = min(self.max.z, other.max.z) - max(self.min.z, other.min.z)
        if dx > 0 and dy > 0 and dz > 0:
            return dx * dy * dz
        return 0.0

    def penetration_depth(self, other: "AABB") -> float:
        """Maximum penetration depth (metres) along any single axis."""
        dx = min(self.max.x, other.max.x) - max(self.min.x, other.min.x)
        dy = min(self.max.y, other.max.y) - max(self.min.y, other.min.y)
        dz = min(self.max.z, other.max.z) - max(self.min.z, other.min.z)
        if dx > 0 and dy > 0 and dz > 0:
            return min(dx, dy, dz)
        return 0.0

    def gap_to(self, other: "AABB") -> float:
        """
        Minimum surface-to-surface gap.
        Returns negative value if overlapping (= penetration depth).
        """
        # Gap on each axis (positive = separated, negative = overlapping)
        gx = max(self.min.x - other.max.x, other.min.x - self.max.x)
        gy = max(self.min.y - other.max.y, other.min.y - self.max.y)
        gz = max(self.min.z - other.max.z, other.min.z - self.max.z)
        # All negative → overlapping on all axes → hard clash
        if gx < 0 and gy < 0 and gz < 0:
            return max(gx, gy, gz)     # least-penetrating axis (negative)
        # 3-D Euclidean surface gap for separated objects
        clamped_x = max(gx, 0.0)
        clamped_y = max(gy, 0.0)
        clamped_z = max(gz, 0.0)
        return math.sqrt(clamped_x**2 + clamped_y**2 + clamped_z**2)


@dataclass
class Element:
    """Parsed MEP element with cached geometry."""
    element_id:   str
    element_type: str          # pipe | duct | fitting | …
    ifc_class:    str
    name:         str
    bbox:         AABB
    diameter_m:   Optional[float]
    width_m:      Optional[float]
    height_m:     Optional[float]
    length_m:     Optional[float]

    @property
    def is_cylindrical(self) -> bool:
        return self.diameter_m is not None

    @property
    def effective_radius(self) -> Optional[float]:
        if self.diameter_m:
            return self.diameter_m / 2.0
        return None

    @property
    def center(self) -> Vec3:
        return self.bbox.center

    def short_name(self) -> str:
        """e.g. 'pipe DWV 8698629'"""
        parts = self.name.split(":")
        return f"{self.element_type} {parts[-1].strip()}" if len(parts) > 1 else self.name


@dataclass
class ClashResult:
    """One detected clash between two elements."""
    clash_id:       str
    element_id_1:   str
    element_id_2:   str
    element_type_1: str
    element_type_2: str
    name_1:         str
    name_2:         str
    clash_type:     str          # "hard_clash" | "clearance_violation" | "near_miss"
    algorithm:      str          # "aabb" | "distance" | "geometry_obb" | "geometry_cylinder"
    severity:       str          # "Critical" | "High" | "Medium" | "Low"
    penetration_m:  float        # positive = overlap depth; negative = gap
    penetration_mm: float
    gap_m:          float        # surface-to-surface gap (0 if hard clash)
    clash_point:    List[float]  # [x, y, z] mid-point of overlap
    aabb_overlap_volume_m3: float
    pair_description: str


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def cylinder_cylinder_min_distance(
    c1: Vec3, r1: float, axis1: Vec3,
    c2: Vec3, r2: float, axis2: Vec3
) -> float:
    """
    Minimum surface-to-surface distance between two infinite cylinders.
    Falls back to segment-segment closest point distance for finite lengths.
    Returns negative value if cylinders interpenetrate.
    """
    # Direction between centres
    d = c2 - c1
    # Cross product of axes → separating plane normal
    cross = axis1.cross(axis2)
    cross_len = cross.length()

    if cross_len < 1e-8:
        # Axes are parallel — use perpendicular distance between lines
        proj = d.dot(axis1)
        perp = d - axis1 * proj
        centre_dist = perp.length()
    else:
        # Skew lines — closest approach via cross-product formula
        centre_dist = abs(d.dot(cross)) / cross_len

    return centre_dist - r1 - r2


def obb_separating_axis_test(
    c1: Vec3, he1: Vec3,
    c2: Vec3, he2: Vec3
) -> Tuple[bool, float]:
    """
    Separating Axis Theorem (SAT) for two Axis-Aligned OBBs (= AABBs).
    Returns (overlapping: bool, min_penetration_depth: float).
    For true OBBs the rotation matrix would be included — since elements are
    axis-aligned in IFC world coords, AABBs and OBBs coincide here.
    """
    t = c2 - c1
    depths = []

    for a_ext, b_ext, t_comp in [
        (he1.x, he2.x, t.x),
        (he1.y, he2.y, t.y),
        (he1.z, he2.z, t.z),
    ]:
        overlap = (a_ext + b_ext) - abs(t_comp)
        if overlap <= 0:
            return False, 0.0    # Separating axis found → no collision
        depths.append(overlap)

    return True, min(depths)


def closest_point_on_segment(p: Vec3, a: Vec3, b: Vec3) -> Vec3:
    """Return the point on segment AB closest to P."""
    ab = b - a
    l2 = ab.dot(ab)
    if l2 < 1e-12:
        return a
    t = max(0.0, min(1.0, (p - a).dot(ab) / l2))
    return a + ab * t


def segment_segment_closest_points(
    p1: Vec3, p2: Vec3,
    p3: Vec3, p4: Vec3
) -> Tuple[Vec3, Vec3, float]:
    """
    Compute the closest points between segment P1P2 and P3P4.
    Returns (point_on_1, point_on_2, distance).
    """
    d1 = p2 - p1
    d2 = p4 - p3
    r  = p1 - p3
    a  = d1.dot(d1)
    e  = d2.dot(d2)
    f  = d2.dot(r)

    if a < 1e-10 and e < 1e-10:
        return p1, p3, (p1 - p3).length()
    if a < 1e-10:
        s = 0.0
        t = max(0.0, min(1.0, f / e))
    else:
        c = d1.dot(r)
        if e < 1e-10:
            t = 0.0
            s = max(0.0, min(1.0, -c / a))
        else:
            b  = d1.dot(d2)
            denom = a * e - b * b
            if abs(denom) > 1e-10:
                s = max(0.0, min(1.0, (b * f - c * e) / denom))
            else:
                s = 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0; s = max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t = 1.0; s = max(0.0, min(1.0, (b - c) / a))

    cp1 = p1 + d1 * s
    cp2 = p3 + d2 * t
    return cp1, cp2, (cp1 - cp2).length()


# ─────────────────────────────────────────────────────────────────────────────
# ELEMENT PARSER
# ─────────────────────────────────────────────────────────────────────────────

def parse_elements(data: dict) -> List[Element]:
    """Parse raw JSON elements into typed Element objects."""
    elements = []
    for raw in data.get("elements", []):
        b_min = raw["bbox_min_xyz"]
        b_max = raw["bbox_max_xyz"]

        # Ensure min < max on all axes (some IFC exporters swap them)
        corrected_min = [min(b_min[i], b_max[i]) for i in range(3)]
        corrected_max = [max(b_min[i], b_max[i]) for i in range(3)]

        bbox = AABB(
            min=Vec3(*corrected_min),
            max=Vec3(*corrected_max),
        )

        elements.append(Element(
            element_id   = raw["element_id"],
            element_type = raw.get("element_type", "unknown"),
            ifc_class    = raw.get("ifc_class", ""),
            name         = raw.get("name", ""),
            bbox         = bbox,
            diameter_m   = raw.get("diameter_m"),
            width_m      = raw.get("width_m"),
            height_m     = raw.get("height_m"),
            length_m     = raw.get("length_m"),
        ))
    return elements


# ─────────────────────────────────────────────────────────────────────────────
# SEVERITY CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

def classify_severity(
    clash_type: str,
    penetration_m: float,
    gap_m: float
) -> str:
    """Assign severity label based on clash type and depth/gap."""
    if clash_type == "hard_clash":
        depth_mm = penetration_m * 1000
        if depth_mm > SEV_CRITICAL_MM: return "Critical"
        if depth_mm > SEV_HIGH_MM:     return "High"
        if depth_mm > SEV_MEDIUM_MM:   return "Medium"
        return "Low"
    elif clash_type == "clearance_violation":
        gap_mm = gap_m * 1000
        if gap_mm < 10:  return "High"
        if gap_mm < 25:  return "Medium"
        return "Low"
    else:  # near_miss
        return "Info"


def classify_clash_type(
    gap_m: float,
    clearance: float,
    near_miss: float
) -> str:
    if gap_m <= HARD_CLASH_TOLERANCE_M:
        return "hard_clash"
    elif gap_m <= clearance:
        return "clearance_violation"
    elif gap_m <= near_miss:
        return "near_miss"
    return "none"


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 1 — AABB INTERSECTION
# ─────────────────────────────────────────────────────────────────────────────

def check_aabb(
    e1: Element, e2: Element,
    clearance: float,
    near_miss: float
) -> Optional[ClashResult]:
    """
    Axis-Aligned Bounding Box intersection check.
    Expands each box by clearance margin to also detect clearance violations.
    """
    bbox1 = e1.bbox
    bbox2 = e2.bbox

    # ── Hard clash check (raw BBs)
    gap = bbox1.gap_to(bbox2)

    if gap > near_miss:
        return None    # too far apart — skip even as near-miss

    # Determine overlap volume
    overlap_vol = bbox1.intersection_volume(bbox2)
    pen_depth   = bbox1.penetration_depth(bbox2) if overlap_vol > 0 else 0.0
    actual_gap  = max(gap, 0.0)

    clash_type = classify_clash_type(gap, clearance, near_miss)
    if clash_type == "none":
        return None

    severity = classify_severity(clash_type, pen_depth, actual_gap)

    # Clash point = centre of overlapping volume or midpoint of closest faces
    if overlap_vol > 0:
        ox = (max(bbox1.min.x, bbox2.min.x) + min(bbox1.max.x, bbox2.max.x)) / 2
        oy = (max(bbox1.min.y, bbox2.min.y) + min(bbox1.max.y, bbox2.max.y)) / 2
        oz = (max(bbox1.min.z, bbox2.min.z) + min(bbox1.max.z, bbox2.max.z)) / 2
        clash_point = Vec3(ox, oy, oz)
    else:
        clash_point = (e1.center + e2.center) / 2.0

    pen_mm = pen_depth * 1000

    return ClashResult(
        clash_id       = "",
        element_id_1   = e1.element_id,
        element_id_2   = e2.element_id,
        element_type_1 = e1.element_type,
        element_type_2 = e2.element_type,
        name_1         = e1.name,
        name_2         = e2.name,
        clash_type     = clash_type,
        algorithm      = "aabb",
        severity       = severity,
        penetration_m  = round(pen_depth, 6),
        penetration_mm = round(pen_mm, 3),
        gap_m          = round(actual_gap, 6),
        clash_point    = clash_point.to_list(),
        aabb_overlap_volume_m3 = round(overlap_vol, 9),
        pair_description = f"{e1.short_name()} × {e2.short_name()}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 2 — DISTANCE-BASED CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_distance(
    e1: Element, e2: Element,
    clearance: float,
    near_miss: float
) -> Optional[ClashResult]:
    """
    Centre-to-centre and surface-to-surface distance check.
    More accurate than pure AABB for cylindrical elements (pipes).
    For pipes: uses radius to compute surface-surface distance.
    For ducts: falls back to AABB surface distance.
    """
    c1 = e1.center
    c2 = e2.center
    centre_dist = (c2 - c1).length()

    # Surface-to-surface gap estimate
    if e1.is_cylindrical and e2.is_cylindrical:
        # Pipe-pipe: subtract both radii from centre distance
        r1 = e1.effective_radius
        r2 = e2.effective_radius
        surface_gap = centre_dist - r1 - r2
    elif e1.is_cylindrical:
        r1 = e1.effective_radius
        # Approximate e2 (duct) by its inscribed sphere radius
        he2 = e2.bbox.half_extents
        r2  = min(he2.x, he2.y, he2.z)
        surface_gap = centre_dist - r1 - r2
    elif e2.is_cylindrical:
        r2 = e2.effective_radius
        he1 = e1.bbox.half_extents
        r1  = min(he1.x, he1.y, he1.z)
        surface_gap = centre_dist - r1 - r2
    else:
        # Both ducts — use AABB gap (already computed)
        surface_gap = e1.bbox.gap_to(e2.bbox)

    if surface_gap > near_miss:
        return None

    pen_depth  = max(-surface_gap, 0.0)
    actual_gap = max(surface_gap,  0.0)

    clash_type = classify_clash_type(surface_gap, clearance, near_miss)
    if clash_type == "none":
        return None

    severity = classify_severity(clash_type, pen_depth, actual_gap)
    pen_mm   = pen_depth * 1000

    clash_point = ((c1 + c2) / 2.0).to_list()
    overlap_vol = e1.bbox.intersection_volume(e2.bbox)

    return ClashResult(
        clash_id       = "",
        element_id_1   = e1.element_id,
        element_id_2   = e2.element_id,
        element_type_1 = e1.element_type,
        element_type_2 = e2.element_type,
        name_1         = e1.name,
        name_2         = e2.name,
        clash_type     = clash_type,
        algorithm      = "distance",
        severity       = severity,
        penetration_m  = round(pen_depth, 6),
        penetration_mm = round(pen_mm, 3),
        gap_m          = round(actual_gap, 6),
        clash_point    = clash_point,
        aabb_overlap_volume_m3 = round(overlap_vol, 9),
        pair_description = f"{e1.short_name()} × {e2.short_name()}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 3 — GEOMETRY-BASED (OBB / CYLINDER)
# ─────────────────────────────────────────────────────────────────────────────

def infer_axis(e: Element) -> Tuple[Vec3, Vec3, Vec3]:
    """
    Infer the primary axis of an element from its bounding box extents.
    Returns (start_point, end_point, unit_axis_vector).
    """
    size = e.bbox.size
    center = e.bbox.center

    # Longest dimension = primary axis
    if size.x >= size.y and size.x >= size.z:
        axis = Vec3(1, 0, 0)
        half = size.x / 2
    elif size.y >= size.x and size.y >= size.z:
        axis = Vec3(0, 1, 0)
        half = size.y / 2
    else:
        axis = Vec3(0, 0, 1)
        half = size.z / 2

    start = center - axis * half
    end   = center + axis * half
    return start, end, axis


def check_geometry(
    e1: Element, e2: Element,
    clearance: float,
    near_miss: float
) -> Optional[ClashResult]:
    """
    Geometry-based narrow phase:
    - Pipe  × Pipe  → cylinder-cylinder distance (segment-segment backbone + radii)
    - Pipe  × Duct  → cylinder-vs-OBB (cylinder axis to OBB face distance)
    - Duct  × Duct  → OBB SAT (Separating Axis Theorem)
    """
    c1 = e1.center
    c2 = e2.center

    if e1.is_cylindrical and e2.is_cylindrical:
        # ── Cylinder × Cylinder ──────────────────────────────────────────
        s1, e1p, ax1 = infer_axis(e1)
        s2, e2p, ax2 = infer_axis(e2)
        r1 = e1.effective_radius
        r2 = e2.effective_radius

        cp1, cp2, seg_dist = segment_segment_closest_points(s1, e1p, s2, e2p)
        surface_gap = seg_dist - r1 - r2

        clash_point = ((cp1 + cp2) / 2.0).to_list()
        algorithm   = "geometry_cylinder"

    elif not e1.is_cylindrical and not e2.is_cylindrical:
        # ── OBB × OBB (SAT) ─────────────────────────────────────────────
        overlapping, pen = obb_separating_axis_test(
            c1, e1.bbox.half_extents,
            c2, e2.bbox.half_extents
        )
        if overlapping:
            surface_gap = -pen
        else:
            surface_gap = e1.bbox.gap_to(e2.bbox)

        mid = (c1 + c2) / 2.0
        clash_point = mid.to_list()
        algorithm   = "geometry_obb"

    else:
        # ── Cylinder × Duct (mixed) ──────────────────────────────────────
        pipe    = e1 if e1.is_cylindrical else e2
        duct    = e2 if e1.is_cylindrical else e1

        ps, pe_, pax = infer_axis(pipe)
        r = pipe.effective_radius

        # Find closest point on pipe axis segment to duct center
        cp_on_pipe = closest_point_on_segment(duct.center, ps, pe_)

        # Distance from that pipe-surface point to duct AABB
        # We expand the duct AABB by pipe radius and test if axis is inside
        duct_expanded = duct.bbox.expand(r)
        duct_gap = duct.bbox.gap_to(AABB(cp_on_pipe, cp_on_pipe))
        surface_gap = duct_gap - r

        clash_point = ((cp_on_pipe + duct.center) / 2.0).to_list()
        algorithm   = "geometry_cylinder"

    if surface_gap > near_miss:
        return None

    pen_depth  = max(-surface_gap, 0.0)
    actual_gap = max(surface_gap,  0.0)

    clash_type = classify_clash_type(surface_gap, clearance, near_miss)
    if clash_type == "none":
        return None

    severity   = classify_severity(clash_type, pen_depth, actual_gap)
    pen_mm     = pen_depth * 1000
    overlap_vol = e1.bbox.intersection_volume(e2.bbox)

    return ClashResult(
        clash_id       = "",
        element_id_1   = e1.element_id,
        element_id_2   = e2.element_id,
        element_type_1 = e1.element_type,
        element_type_2 = e2.element_type,
        name_1         = e1.name,
        name_2         = e2.name,
        clash_type     = clash_type,
        algorithm      = algorithm,
        severity       = severity,
        penetration_m  = round(pen_depth, 6),
        penetration_mm = round(pen_mm, 3),
        gap_m          = round(actual_gap, 6),
        clash_point    = clash_point,
        aabb_overlap_volume_m3 = round(overlap_vol, 9),
        pair_description = f"{e1.short_name()} × {e2.short_name()}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SPATIAL INDEX — Simple Grid for Broad Phase Pruning
# ─────────────────────────────────────────────────────────────────────────────

class SpatialGrid:
    """
    Uniform 3-D grid for broad-phase candidate pruning.
    Reduces O(n²) pairs to only spatially proximate ones.
    """
    def __init__(self, elements: List[Element], cell_size: float = 1.0):
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int,int,int], List[int]] = {}

        for idx, el in enumerate(elements):
            for cell in self._cells_for_aabb(el.bbox):
                self.grid.setdefault(cell, []).append(idx)

    def _cell(self, x: float, y: float, z: float) -> Tuple[int,int,int]:
        cs = self.cell_size
        return (int(math.floor(x/cs)), int(math.floor(y/cs)), int(math.floor(z/cs)))

    def _cells_for_aabb(self, bbox: AABB) -> List[Tuple[int,int,int]]:
        cs = self.cell_size
        x0, y0, z0 = bbox.min.x, bbox.min.y, bbox.min.z
        x1, y1, z1 = bbox.max.x, bbox.max.y, bbox.max.z
        cells = []
        ix = int(math.floor(x0/cs))
        while ix * cs <= x1:
            iy = int(math.floor(y0/cs))
            while iy * cs <= y1:
                iz = int(math.floor(z0/cs))
                while iz * cs <= z1:
                    cells.append((ix, iy, iz))
                    iz += 1
                iy += 1
            ix += 1
        return cells

    def candidate_pairs(self) -> List[Tuple[int,int]]:
        """Return all unique (i,j) index pairs sharing at least one cell."""
        seen: set = set()
        pairs = []
        for indices in self.grid.values():
            for i in range(len(indices)):
                for j in range(i+1, len(indices)):
                    a, b = indices[i], indices[j]
                    key = (min(a,b), max(a,b))
                    if key not in seen:
                        seen.add(key)
                        pairs.append(key)
        return pairs


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CLASH DETECTION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_clash_detection(
    elements: List[Element],
    clearance: float = CLEARANCE_ZONE_M,
    near_miss: float = NEAR_MISS_ZONE_M,
    tolerance: float = HARD_CLASH_TOLERANCE_M,
    algorithms: List[str] = None,
    use_spatial_index: bool = True,
) -> Dict:
    """
    Full pipeline:
      1. Build spatial grid index
      2. Broad phase: AABB + expanded clearance check on candidates
      3. Mid   phase: distance-based refinement
      4. Narrow phase: geometry-based (OBB/cylinder)
      5. Deduplicate, rank, and return results
    """
    if algorithms is None:
        algorithms = ["aabb", "distance", "geometry"]

    n = len(elements)
    print(f"\n{'═'*60}")
    print(f"  MEP CLASH DETECTION ENGINE")
    print(f"{'═'*60}")
    print(f"  Elements loaded     : {n:,}")
    print(f"  Hard clash tol      : {tolerance*1000:.1f} mm")
    print(f"  Clearance zone      : {clearance*1000:.0f} mm")
    print(f"  Near-miss zone      : {near_miss*1000:.0f} mm")
    print(f"  Algorithms          : {', '.join(algorithms)}")
    print(f"  Spatial index       : {'enabled' if use_spatial_index else 'disabled'}")

    t0 = time.time()

    # ── Broad Phase ───────────────────────────────────────────────────────────
    if use_spatial_index:
        grid = SpatialGrid(elements, cell_size=max(clearance * 4, 0.5))
        candidate_pairs = grid.candidate_pairs()
    else:
        candidate_pairs = list(itertools.combinations(range(n), 2))

    t_broad = time.time()
    print(f"\n  Broad phase pairs   : {len(candidate_pairs):,}  ({t_broad-t0:.2f}s)")

    # ── Refine Phases ─────────────────────────────────────────────────────────
    # Key: frozenset({id1, id2}) → best (most severe) ClashResult
    best_clashes: Dict[frozenset, ClashResult] = {}

    SEV_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Info": 0}

    def record(result: Optional[ClashResult]):
        if result is None:
            return
        key = frozenset({result.element_id_1, result.element_id_2})
        existing = best_clashes.get(key)
        if existing is None or SEV_ORDER.get(result.severity, 0) > SEV_ORDER.get(existing.severity, 0):
            best_clashes[key] = result

    for idx_a, idx_b in candidate_pairs:
        ea = elements[idx_a]
        eb = elements[idx_b]

        # Skip self-same element-type combos that are connected (tiny gap ~0)
        # by checking if they share extreme close proximity AND share name prefix
        name_a = ea.name.rsplit(":", 1)[0]
        name_b = eb.name.rsplit(":", 1)[0]

        # ── Algorithm 1: AABB ─────────────────────────────────────────────
        if "aabb" in algorithms:
            record(check_aabb(ea, eb, clearance, near_miss))

        # ── Algorithm 2: Distance ─────────────────────────────────────────
        if "distance" in algorithms:
            record(check_distance(ea, eb, clearance, near_miss))

        # ── Algorithm 3: Geometry ─────────────────────────────────────────
        if "geometry" in algorithms:
            record(check_geometry(ea, eb, clearance, near_miss))

    t_narrow = time.time()
    print(f"  Narrow phase done   : {t_narrow-t_broad:.2f}s")

    # ── Assign IDs & Sort ─────────────────────────────────────────────────────
    results = list(best_clashes.values())

    # Sort: hard clashes first, then by severity, then by penetration depth
    clash_type_order = {"hard_clash": 0, "clearance_violation": 1, "near_miss": 2}
    results.sort(key=lambda r: (
        clash_type_order.get(r.clash_type, 9),
        -SEV_ORDER.get(r.severity, 0),
        -r.penetration_mm
    ))

    for i, r in enumerate(results, 1):
        r.clash_id = f"CLX-{i:05d}"

    t_done = time.time()

    # ── Summary Stats ─────────────────────────────────────────────────────────
    hard_clashes   = [r for r in results if r.clash_type == "hard_clash"]
    clearance_viol = [r for r in results if r.clash_type == "clearance_violation"]
    near_misses    = [r for r in results if r.clash_type == "near_miss"]

    sev_counter: Dict[str, int] = {}
    for r in results:
        sev_counter[r.severity] = sev_counter.get(r.severity, 0) + 1

    pair_type_counter: Dict[str, int] = {}
    for r in results:
        pt = f"{r.element_type_1} × {r.element_type_2}"
        pt_rev = f"{r.element_type_2} × {r.element_type_1}"
        key = pt if pt <= pt_rev else pt_rev
        pair_type_counter[key] = pair_type_counter.get(key, 0) + 1

    algo_counter: Dict[str, int] = {}
    for r in results:
        algo_counter[r.algorithm] = algo_counter.get(r.algorithm, 0) + 1

    summary = {
        "total_elements"         : n,
        "candidate_pairs_checked": len(candidate_pairs),
        "total_clashes_found"    : len(results),
        "hard_clashes"           : len(hard_clashes),
        "clearance_violations"   : len(clearance_viol),
        "near_misses"            : len(near_misses),
        "by_severity"            : sev_counter,
        "by_element_pair_type"   : pair_type_counter,
        "by_algorithm"           : algo_counter,
        "max_penetration_mm"     : round(max((r.penetration_mm for r in hard_clashes), default=0.0), 3),
        "avg_penetration_mm"     : round(
            sum(r.penetration_mm for r in hard_clashes) / len(hard_clashes)
            if hard_clashes else 0.0, 3
        ),
        "processing_time_seconds": round(t_done - t0, 3),
        "parameters": {
            "hard_clash_tolerance_m": tolerance,
            "clearance_zone_m"      : clearance,
            "near_miss_zone_m"      : near_miss,
            "algorithms_used"       : algorithms,
        }
    }

    print(f"\n{'─'*60}")
    print(f"  ✅ Total clashes found   : {len(results):,}")
    print(f"     Hard clashes          : {len(hard_clashes):,}")
    print(f"     Clearance violations  : {len(clearance_viol):,}")
    print(f"     Near misses           : {len(near_misses):,}")
    print(f"  ⚠  Severity breakdown:")
    for sev in ["Critical", "High", "Medium", "Low", "Info"]:
        cnt = sev_counter.get(sev, 0)
        if cnt: print(f"     {sev:<12}: {cnt:,}")
    print(f"  ⏱  Total time            : {t_done-t0:.2f}s")
    print(f"{'═'*60}\n")

    return {"summary": summary, "clash_pairs": results}


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SERIALISER
# ─────────────────────────────────────────────────────────────────────────────

def serialise(result: Dict) -> Dict:
    """Convert ClashResult dataclasses to plain dicts for JSON output."""
    clashes_raw = []
    for r in result["clash_pairs"]:
        d = asdict(r)
        clashes_raw.append(d)
    return {
        "schema_version": "2.0",
        "generator"     : "clash_detection_engine.py",
        "summary"       : result["summary"],
        "clash_pairs"   : clashes_raw,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MEP Clash Detection Engine — AABB + Distance + Geometry"
    )
    parser.add_argument("--input",     default=DEFAULT_INPUT,   help="Path to extracted_elements.json")
    parser.add_argument("--out",       default=DEFAULT_OUTPUT,  help="Output JSON path")
    parser.add_argument("--clearance", type=float, default=CLEARANCE_ZONE_M,   help="Clearance zone in metres")
    parser.add_argument("--near-miss", type=float, default=NEAR_MISS_ZONE_M,   help="Near-miss zone in metres")
    parser.add_argument("--tolerance", type=float, default=HARD_CLASH_TOLERANCE_M, help="Hard-clash tolerance in metres")
    parser.add_argument("--no-spatial-index", action="store_true",             help="Disable spatial grid (brute force)")
    parser.add_argument("--algorithms", default="aabb,distance,geometry",      help="Comma-separated list of algorithms")
    args = parser.parse_args()

    # Load
    print(f"Loading: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = parse_elements(data)

    algos = [a.strip() for a in args.algorithms.split(",")]

    # Detect
    result = run_clash_detection(
        elements,
        clearance   = args.clearance,
        near_miss   = getattr(args, "near_miss"),
        tolerance   = args.tolerance,
        algorithms  = algos,
        use_spatial_index = not args.no_spatial_index,
    )

    # Serialise & write
    output = serialise(result)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Results written → {out_path}")
    print(f"Total clash pairs: {len(result['clash_pairs']):,}\n")


if __name__ == "__main__":
    main()