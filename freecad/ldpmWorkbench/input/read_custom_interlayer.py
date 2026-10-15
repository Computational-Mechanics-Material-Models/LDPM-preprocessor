## ===========================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023
## All rights reserved.
##
## Use of this source code is governed by a BSD-style license that can be
## found in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ===========================================================================
##
## This file parses the inputs for Custom Interlayer
##
## ===========================================================================

import math
import re

from freecad.ldpmWorkbench.input.read_reinforcement_dxf import read_dxf_polylines

_PLANE_AXES = {"Z": ("X", "Y"), "X": ("Y", "Z"), "Y": ("X", "Z")}
_REF_PLANES = {"XY": ("X", "Y", "Z"), "XZ": ("X", "Z", "Y"), "YZ": ("Y", "Z", "X")}
_POINT_LINE = re.compile(r"^point\s*:", re.IGNORECASE)
_PATH_HEADER = re.compile(r"^Path\s*\[", re.IGNORECASE)
_REPEAT_LINE = re.compile(
    r"^([XYZ])_list\s*=\s*\[([^\]]*)\]\s*,\s*mf\s*=\s*([1-9]\d*)\s*$",
    re.IGNORECASE,
)
_LAYER_HEADER = re.compile(r"Layer\(\s*([XYZ])\s*\)\s*\[", re.IGNORECASE)
_CORNER_LINE = re.compile(r"corner\s+\d+\s*:", re.IGNORECASE)
_COORD = re.compile(r"([XYZ])\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", re.IGNORECASE)
_LIST_LINE = re.compile(
    r"^([XYZ])_list\s*=\s*\[([^\]]*)\]\s*,\s*mf\s*=\s*([1-9]\d*)\s*$",
    re.IGNORECASE,
)


def _clean_lines(text):

    lines = []
    for line in str(text or "").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if stripped:
            lines.append(stripped)
    return lines


def _parse_corner(line, axis):

    plane_axes = _PLANE_AXES[axis]
    values = {}
    for match in _COORD.finditer(line):
        key = match.group(1).upper()
        if key in plane_axes:
            values[key] = float(match.group(2))
    if set(values.keys()) != set(plane_axes):
        raise ValueError("Corner must define " + plane_axes[0] + " and " + plane_axes[1])
    return {plane_axes[0]: values[plane_axes[0]], plane_axes[1]: values[plane_axes[1]]}


def _parse_positions(text):

    if not str(text).strip():
        return []
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_custom_interlayer(text):

    lines = _clean_lines(text)
    if not lines:
        return []

    blocks = []
    index = 0
    while index < len(lines):
        header = _LAYER_HEADER.match(lines[index])
        if not header:
            raise ValueError("Expected Layer(...) [ at: " + lines[index])

        axis = header.group(1).upper()
        index += 1
        corner_lines = []
        while index < len(lines) and lines[index] != "]":
            corner_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ValueError("Missing ] for Layer(" + axis + ") block")

        index += 1
        if index >= len(lines):
            raise ValueError("Missing " + axis + "_list for Layer(" + axis + ") block")

        list_match = _LIST_LINE.match(lines[index])
        if not list_match or list_match.group(1).upper() != axis:
            raise ValueError("Expected " + axis + "_list = [...], mf=... after Layer(" + axis + ") block")

        corners = []
        for line in corner_lines:
            if _CORNER_LINE.search(line):
                corners.append(_parse_corner(line, axis))

        if len(corners) != 4:
            raise ValueError("Layer(" + axis + ") requires 4 corners")

        blocks.append(
            {
                "axis": axis,
                "planeAxes": _PLANE_AXES[axis],
                "corners": corners,
                "positions": _parse_positions(list_match.group(2)),
                "mf": int(list_match.group(3)),
            }
        )
        index += 1

    return blocks


def _ref_plane(name):

    key = str(name or "XY").strip().upper()
    if key not in _REF_PLANES:
        raise ValueError("Reference plane must be XY, XZ, or YZ")
    return _REF_PLANES[key]


def _parse_start_position(text):

    parts = [item.strip() for item in re.split(r"[,\s]+", str(text or "")) if item.strip()]
    values = [0.0, 0.0, 0.0]
    for index, part in enumerate(parts[:3]):
        values[index] = float(part)
    return values


def _dedupe_2d(points, tol=1e-9):

    kept = []
    for point in points:
        xy = (float(point[0]), float(point[1]))
        if kept and math.hypot(xy[0] - kept[-1][0], xy[1] - kept[-1][1]) <= tol:
            continue
        kept.append(xy)
    if len(kept) >= 2 and math.hypot(kept[0][0] - kept[-1][0], kept[0][1] - kept[-1][1]) <= tol:
        kept = kept[:-1]
    return kept


def _shoelace(points):

    area = 0.0
    count = len(points)
    for index, point in enumerate(points):
        nxt = points[(index + 1) % count]
        area += point[0] * nxt[1] - nxt[0] * point[1]
    return 0.5 * area


def _close_polygon(points):

    pts = _dedupe_2d(points)
    if len(pts) < 3 or abs(_shoelace(pts)) < 1e-8:
        return None
    return [[point[0], point[1]] for point in pts]


def _sample_spline(points, samples_per_span=12):

    pts = _dedupe_2d(points)
    if len(pts) < 3:
        return pts
    chain = [pts[0]] + pts + [pts[-1]]
    sampled = []
    for index in range(1, len(chain) - 2):
        p0, p1, p2, p3 = chain[index - 1], chain[index], chain[index + 1], chain[index + 2]
        for step in range(samples_per_span):
            t = step / float(samples_per_span)
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2.0 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2.0 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
            )
            sampled.append((x, y))
        sampled.append(p2)
    return _dedupe_2d(sampled)


def _map_point(values, plane_axes):

    a0, a1 = plane_axes
    if a0 in values and a1 in values:
        return (values[a0], values[a1])
    if "X" in values and "Y" in values:
        return (values["X"], values["Y"])
    raise ValueError("Point must define " + a0 + " and " + a1)


def _point_values(line):

    values = {}
    for match in _COORD.finditer(line):
        values[match.group(1).upper()] = float(match.group(2))
    return values


def _repeat_heights(plane_height, listed):

    heights = [float(plane_height)]
    for value in listed:
        if all(abs(float(value) - item) > 1e-9 for item in heights):
            heights.append(float(value))
    return heights


def _surface(polygon, plane, positions, mf):

    a0, a1, normal = _ref_plane(plane)
    return {
        "plane": plane,
        "axis": normal,
        "planeAxes": [a0, a1],
        "polygon": polygon,
        "positions": positions,
        "mf": int(mf),
    }


def parse_path_ribbon(text, plane="XY", path_type="Polyline", plane_height=0.0):

    notes = []
    path_type = str(path_type or "Polyline").strip().title()
    if path_type not in ("Line", "Polyline", "Spline"):
        path_type = "Polyline"
    a0, a1, normal = _ref_plane(plane)
    lines = _clean_lines(text)
    if not lines:
        return [], ["Path ribbon text is empty."]

    surfaces = []
    index = 0
    while index < len(lines):
        if not _PATH_HEADER.match(lines[index]):
            raise ValueError("Expected Path [ at: " + lines[index])
        index += 1
        point_lines = []
        while index < len(lines) and lines[index] != "]":
            point_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ValueError("Missing ] for Path block")
        index += 1
        if index >= len(lines):
            raise ValueError("Missing height list after Path block")
        list_match = _REPEAT_LINE.match(lines[index])
        if not list_match:
            raise ValueError("Expected X_list, Y_list, or Z_list after Path block")
        list_axis = list_match.group(1).upper()
        if list_axis != normal:
            notes.append(
                "Path repeat list is "
                + list_axis
                + "_list; using those heights along "
                + normal
                + "."
            )
        raw_points = []
        for line in point_lines:
            if not _POINT_LINE.match(line):
                continue
            raw_points.append(_map_point(_point_values(line), (a0, a1)))
        if path_type == "Spline":
            raw_points = _sample_spline(raw_points)
        polygon = _close_polygon(raw_points)
        if polygon is None:
            notes.append("A path does not enclose a surface and was skipped.")
        else:
            surfaces.append(
                _surface(
                    polygon,
                    plane,
                    _repeat_heights(plane_height, _parse_positions(list_match.group(2))),
                    int(list_match.group(3)),
                )
            )
        index += 1
    return surfaces, notes


def _join_open_chains(chains, tol=1e-4):

    open_chains = [list(chain) for chain in chains]
    changed = True
    while changed and len(open_chains) > 1:
        changed = False
        for i in range(len(open_chains)):
            for j in range(i + 1, len(open_chains)):
                a = open_chains[i]
                b = open_chains[j]
                pairs = (
                    (a, b, False, False),
                    (a, b, False, True),
                    (a, b, True, False),
                    (a, b, True, True),
                )
                joined = None
                for left, right, flip_left, flip_right in pairs:
                    aa = list(reversed(left)) if flip_left else list(left)
                    bb = list(reversed(right)) if flip_right else list(right)
                    if math.hypot(aa[-1][0] - bb[0][0], aa[-1][1] - bb[0][1]) <= tol:
                        joined = aa + bb[1:]
                        break
                if joined is None:
                    continue
                open_chains[i] = joined
                del open_chains[j]
                changed = True
                break
            if changed:
                break
    return open_chains


def dxf_surfaces(path, plane="XY", plane_height=0.0, start_position="0, 0, 0", mf=2):

    notes = []
    if not str(path or "").strip():
        return [], ["DXF / CAD file is not set."]
    try:
        polylines, skipped = read_dxf_polylines(path)
    except Exception as exc:
        return [], [str(exc)]
    if skipped:
        notes.append("Skipped DXF entities: " + ", ".join(sorted(skipped)))

    a0, a1, _normal = _ref_plane(plane)
    start = _parse_start_position(start_position)
    axis_index = {"X": 0, "Y": 1, "Z": 2}
    i0 = axis_index[a0]
    i1 = axis_index[a1]
    closed = []
    open_chains = []
    for poly in polylines:
        points = []
        for point in poly.get("points") or []:
            shifted = [float(point[k]) + start[k] for k in range(3)]
            points.append((shifted[i0], shifted[i1]))
        points = _dedupe_2d(points)
        if len(points) < 2:
            continue
        if poly.get("closed"):
            polygon = _close_polygon(points)
            if polygon is not None:
                closed.append(polygon)
            else:
                notes.append("A closed DXF curve does not enclose a surface and was skipped.")
        else:
            open_chains.append(points)

    for chain in _join_open_chains(open_chains):
        polygon = _close_polygon(chain)
        if polygon is None:
            notes.append("An open DXF curve does not enclose a surface and was skipped.")
        else:
            closed.append(polygon)

    surfaces = [
        _surface(polygon, plane, _repeat_heights(plane_height, []), int(mf or 2))
        for polygon in closed
    ]
    if not surfaces and not notes:
        notes.append("DXF / CAD file has no usable curves.")
    return surfaces, notes


def build_custom_surfaces(params):

    params = params or {}
    mode = str(params.get("customMode", "fourPoint")).strip()
    if mode == "pathRibbon":
        return parse_path_ribbon(
            params.get("customPathRibbonDefinition", ""),
            params.get("customPathRibbonPlane", "XY"),
            params.get("customPathRibbonType", "Polyline"),
            params.get("customPathRibbonPlaneHeight", 0.0),
        )
    if mode == "dxfImport":
        return dxf_surfaces(
            params.get("customDxfCadFile", ""),
            params.get("customDxfPlane", "XY"),
            params.get("customDxfPlaneHeight", 0.0),
            params.get("customDxfStartPosition", "0, 0, 0"),
            params.get("customDxfMf", 2),
        )
    return [], []
