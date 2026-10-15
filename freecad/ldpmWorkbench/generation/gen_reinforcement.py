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
## Generate reinforcement data file
##
## ===========================================================================


import math
from pathlib import Path

from freecad.ldpmWorkbench.input.read_reinforcement_dxf import (
    read_dxf_polylines,
    validate_reinforcement_dxf,
)


def parse_height_values(text):
    if text is None:
        return []
    raw = str(text).replace(";", ",").replace("\n", ",")
    values = []
    for chunk in raw.split(","):
        for token in chunk.split():
            try:
                values.append(float(token))
            except ValueError:
                continue
    return values


def cad_heights(first_layer, extra_text):
    heights = [float(first_layer)]
    heights.extend(parse_height_values(extra_text))
    return heights


def polylines_from_grid(min_c, grid):
    origin_x = float(min_c[0]) + float(grid.get("start_x", 0.0))
    origin_y = float(min_c[1]) + float(grid.get("start_y", 0.0))
    base_z = float(min_c[2])
    polylines = []
    for direction in grid.get("directions", []):
        distance = float(direction.get("distance", 0.0))
        count = int(direction.get("count", 1))
        spacing = float(direction.get("spacing", 0.0))
        axis = str(direction.get("axis", "X")).strip().upper()
        heights = direction.get("heights", [])
        if distance <= 0.0 or count < 1 or axis not in ("X", "Y"):
            continue
        for height in heights:
            z = base_z + float(height)
            for copy_index in range(count):
                if axis == "X":
                    x0 = origin_x
                    y0 = origin_y + copy_index * spacing
                    x1 = origin_x + distance
                    y1 = y0
                else:
                    x0 = origin_x + copy_index * spacing
                    y0 = origin_y
                    x1 = x0
                    y1 = origin_y + distance
                polylines.append({"points": [(x0, y0, z), (x1, y1, z)], "closed": False})
    return polylines


def polylines_from_cad(min_c, cad):
    skipped = {}
    if cad.get("polylines") is not None:
        source = cad["polylines"]
    else:
        path = cad.get("path")
        error = validate_reinforcement_dxf(path)
        if error:
            raise ValueError(error)
        source, skipped = read_dxf_polylines(path)
    start_x = float(cad.get("start_x", 0.0))
    start_y = float(cad.get("start_y", 0.0))
    angle = math.radians(float(cad.get("rotation_deg", 0.0)))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    heights = list(cad.get("heights", []))
    origin_x = float(min_c[0]) + start_x
    origin_y = float(min_c[1]) + start_y
    origin_z = float(min_c[2])
    use_native_z = _source_has_native_z(source)
    layer_heights = list(heights) if heights else [0.0]
    placed = []
    for item in source:
        if isinstance(item, dict):
            points = item["points"]
            closed = bool(item.get("closed", False))
        else:
            points = item
            closed = False
        rotated = []
        for point in points:
            x = float(point[0])
            y = float(point[1])
            z = float(point[2]) if len(point) > 2 else 0.0
            rotated.append((cosine * x - sine * y, sine * x + cosine * y, z))
        if len(rotated) < 2:
            continue
        if use_native_z:
            placed.append({
                "points": [
                    (origin_x + x, origin_y + y, origin_z + z) for x, y, z in rotated
                ],
                "closed": closed,
            })
            continue
        for height in layer_heights:
            z = origin_z + float(height)
            placed.append({
                "points": [(origin_x + x, origin_y + y, z) for x, y, _z in rotated],
                "closed": closed,
            })
    return placed, skipped


def _source_has_native_z(source):
    values = []
    for item in source:
        points = item["points"] if isinstance(item, dict) else item
        for point in points:
            values.append(float(point[2]) if len(point) > 2 else 0.0)
    if not values:
        return False
    if max(abs(value) for value in values) > 1e-6:
        return True
    return (max(values) - min(values)) > 1e-6


def count_nodes_outside_bbox(nodes, min_c, max_c, tol=1e-6):
    if not nodes:
        return 0
    min_x = float(min_c[0]) - tol
    min_y = float(min_c[1]) - tol
    min_z = float(min_c[2]) - tol
    max_x = float(max_c[0]) + tol
    max_y = float(max_c[1]) + tol
    max_z = float(max_c[2]) + tol
    outside = 0
    for point in nodes:
        x, y, z = float(point[0]), float(point[1]), float(point[2])
        if x < min_x or x > max_x or y < min_y or y > max_y or z < min_z or z > max_z:
            outside += 1
    return outside


def mesh_polylines(polylines, step):
    size = float(step)
    if size <= 0.0:
        size = 1.0
    nodes = []
    elements = []
    for poly in polylines:
        sampled = _chain_nodes(poly["points"], size, bool(poly.get("closed", False)))
        count = len(sampled)
        if count < 2:
            continue
        base = len(nodes)
        nodes.extend(sampled)
        for index in range(count - 1):
            elements.append((base + index, base + index + 1))
        if poly.get("closed", False):
            elements.append((base + count - 1, base))
    return nodes, elements


_REINF_HEADER = """\
// ================================================================================
// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/LDPM-preprocessor
//
// Copyright (c) 2023
// All rights reserved.
//
// Use of the code that generated this file is governed by a BSD-style license that
// can be found in the LICENSE file at the top level of the distribution and at
// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
//
// ================================================================================
// Reinforcement Data File
// ================================================================================
//
// ElementType = {element_type}
// Nominal element length mm = {element_length:.10g}
// Diameter mm = {diameter:.10g}
//
// Data Structure:
// Nodes:
// id X Y Z
//
// Elements:
// id node1 node2 length diameter X Y Z
// node1 node2 are the connected node ids
// length is the distance between those nodes
// diameter is the bar diameter
// X Y Z is the element midpoint
//
// ================================================================================
"""


def write_reinforcement_dat(
    geo_name,
    out_dir,
    nodes,
    elements,
    element_length=1.0,
    diameter=1.0,
    element_type="2DOF-T2D2/LINK1",
):
    path = Path(out_dir) / f"{geo_name}-data-reinforcement.dat"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        element_length = float(element_length)
    except (TypeError, ValueError):
        element_length = 1.0
    try:
        diameter = float(diameter)
    except (TypeError, ValueError):
        diameter = 1.0
    element_type = str(element_type or "").strip() or "2DOF-T2D2/LINK1"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_REINF_HEADER.format(
            element_type=element_type,
            element_length=element_length,
            diameter=diameter,
        ))
        handle.write("// Nodes\n")
        for index, point in enumerate(nodes):
            handle.write(
                "%d %.10g %.10g %.10g\n"
                % (index, float(point[0]), float(point[1]), float(point[2]))
            )
        handle.write("// Elements\n")
        for index, element in enumerate(elements):
            n1 = int(element[0])
            n2 = int(element[1])
            p1 = nodes[n1]
            p2 = nodes[n2]
            length = _dist(p1, p2)
            midpoint = (
                0.5 * (float(p1[0]) + float(p2[0])),
                0.5 * (float(p1[1]) + float(p2[1])),
                0.5 * (float(p1[2]) + float(p2[2])),
            )
            handle.write(
                "%d %d %d %.10g %.10g %.10g %.10g %.10g\n"
                % (index, n1, n2, length, diameter, midpoint[0], midpoint[1], midpoint[2])
            )
    return path


def generate_reinforcement(
    geo_name,
    out_dir,
    min_c,
    max_c,
    grid=None,
    cad=None,
    element_length=1.0,
    diameter=1.0,
    element_type="2DOF-T2D2/LINK1",
    log=None,
):
    """Generate reinforcement without aborting the host mesh job on CAD/DXF errors."""
    def _log(message):
        if log is not None:
            log(message)
            return
        print(message)

    try:
        if cad and cad.get("polylines") is None:
            error = validate_reinforcement_dxf(cad.get("path"))
            if error:
                _log("Reinforcement skipped: " + error)
                return None
        result = _build_reinforcement(
            geo_name,
            out_dir,
            min_c,
            max_c,
            grid=grid,
            cad=cad,
            element_length=element_length,
            diameter=diameter,
            element_type=element_type,
        )
    except Exception as exc:
        _log("Reinforcement skipped: " + str(exc))
        return None
    if result.get("skipped"):
        _log("Reinforcement DXF skipped entities: " + str(result["skipped"]))
    if result.get("outside"):
        _log(
            "Reinforcement: rebar placed outside the geometry ("
            + str(int(result["outside"]))
            + " nodes)."
        )
    if not result.get("path"):
        _log("Reinforcement: no bars were written.")
    return result


def _build_reinforcement(
    geo_name,
    out_dir,
    min_c,
    max_c,
    grid=None,
    cad=None,
    element_length=1.0,
    diameter=1.0,
    element_type="2DOF-T2D2/LINK1",
):
    polylines = []
    skipped = {}
    if grid:
        polylines.extend(polylines_from_grid(min_c, grid))
    if cad:
        placed, skipped = polylines_from_cad(min_c, cad)
        polylines.extend(placed)
    try:
        step = float(element_length)
    except (TypeError, ValueError):
        step = 1.0
    if step <= 0.0:
        step = 1.0
    try:
        diameter = float(diameter)
    except (TypeError, ValueError):
        diameter = 1.0
    element_type = str(element_type or "").strip() or "2DOF-T2D2/LINK1"
    nodes, elements = mesh_polylines(polylines, step)
    outside = count_nodes_outside_bbox(nodes, min_c, max_c)
    if not nodes:
        return {
            "path": "",
            "vtkPath": "",
            "nodes": nodes,
            "elements": elements,
            "step": step,
            "diameter": diameter,
            "elementType": element_type,
            "skipped": skipped,
            "outside": outside,
        }
    path = write_reinforcement_dat(
        geo_name,
        out_dir,
        nodes,
        elements,
        element_length=step,
        diameter=diameter,
        element_type=element_type,
    )
    return {
        "path": str(path),
        "vtkPath": "",
        "nodes": nodes,
        "elements": elements,
        "step": step,
        "diameter": diameter,
        "elementType": element_type,
        "skipped": skipped,
        "outside": outside,
    }


def _chain_nodes(points, step, closed):
    if not points:
        return []
    dedup = [_xyz(points[0])]
    for point in points[1:]:
        current = _xyz(point)
        if _dist(current, dedup[-1]) > 1e-9:
            dedup.append(current)
    if closed and len(dedup) > 1 and _dist(dedup[0], dedup[-1]) <= 1e-9:
        dedup = dedup[:-1]
    if len(dedup) < 2:
        return []
    path = list(dedup)
    if closed:
        path.append(dedup[0])
    sampled = _sample_open(path, step)
    if closed and len(sampled) > 1 and _dist(sampled[0], sampled[-1]) <= 1e-6:
        sampled = sampled[:-1]
    return sampled


def _sample_open(path, step):
    total = 0.0
    for index in range(len(path) - 1):
        total += _dist(path[index], path[index + 1])
    if total <= 1e-12:
        return []
    nodes = [path[0]]
    target = step
    seg_index = 0
    seg_start = 0.0
    limit = int(total / step) + len(path) + 3
    while target < total - 1e-8:
        while seg_index < len(path) - 1:
            start = path[seg_index]
            end = path[seg_index + 1]
            seg_len = _dist(start, end)
            seg_end = seg_start + seg_len
            if target <= seg_end + 1e-9:
                ratio = 0.0 if seg_len <= 1e-12 else (target - seg_start) / seg_len
                if ratio < 0.0:
                    ratio = 0.0
                if ratio > 1.0:
                    ratio = 1.0
                nodes.append((
                    start[0] + ratio * (end[0] - start[0]),
                    start[1] + ratio * (end[1] - start[1]),
                    start[2] + ratio * (end[2] - start[2]),
                ))
                break
            seg_index += 1
            seg_start = seg_end
        else:
            break
        target += step
        if len(nodes) > limit:
            break
    if _dist(nodes[-1], path[-1]) > 1e-6:
        nodes.append(path[-1])
    return nodes


def _xyz(point):
    return (float(point[0]), float(point[1]), float(point[2]))


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
