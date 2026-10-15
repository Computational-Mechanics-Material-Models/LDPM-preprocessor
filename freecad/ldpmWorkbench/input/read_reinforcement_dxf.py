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
## Read DXF file for reinforcement and CAD profile
##
## ===========================================================================


import math
from pathlib import Path


def validate_reinforcement_dxf(path):
    """Return None if the DXF looks usable, otherwise an error message string."""
    if path is None or str(path).strip() == "":
        return "Reinforcement CAD file is not set."
    dxf_path = Path(path)
    if not dxf_path.is_file():
        return "Reinforcement CAD file not found: " + str(dxf_path)
    try:
        text = _read_dxf_text(dxf_path)
        pairs = _dxf_pairs(text)
        sections = _dxf_sections(pairs)
    except (OSError, ValueError) as exc:
        return str(exc)
    has_entities = any(name == "ENTITIES" for name, _body in sections)
    if not has_entities:
        return "DXF has no ENTITIES section."
    return None


def read_dxf_polylines(path):
    error = validate_reinforcement_dxf(path)
    if error:
        raise ValueError(error)
    dxf_path = Path(path)
    pairs = _dxf_pairs(_read_dxf_text(dxf_path))
    sections = _dxf_sections(pairs)
    blocks_section = []
    entities = []
    for name, body in sections:
        if name == "BLOCKS":
            blocks_section = body
        elif name == "ENTITIES":
            entities = body
    blocks = _parse_blocks(blocks_section)
    model_entities = _model_entities(entities)
    skipped = {}
    polylines = _entities_to_polylines(model_entities, blocks, 0, (), skipped)
    return polylines, skipped


def _read_dxf_text(path):
    data = Path(path).read_bytes()
    if data.startswith(b"AutoCAD Binary DXF"):
        raise ValueError("Binary DXF is not supported. Re-save as ASCII DXF.")
    if len(data) >= 6 and data[:2] == b"AC" and data[2:6].isdigit():
        raise ValueError("This is a DWG file, not a DXF. Convert it to ASCII DXF first.")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("DXF text could not be read. Re-save as ASCII DXF.") from None


def _dxf_pairs(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and lines[-1].strip() == "":
        lines.pop()
    if len(lines) % 2:
        raise ValueError("DXF has an odd number of lines; file is truncated or damaged")
    pairs = []
    for index in range(0, len(lines), 2):
        code_text = lines[index].strip()
        try:
            code = int(code_text)
        except ValueError:
            code = None
        if code is None:
            raise ValueError(f"DXF line {index + 1}: expected a group code, got {code_text!r}")
        pairs.append((code, lines[index + 1].strip()))
    return pairs


def _dxf_sections(pairs):
    sections = []
    index = 0
    count = len(pairs)
    while index < count:
        code, value = pairs[index]
        if code == 0 and value.upper() == "SECTION":
            name = ""
            index += 1
            if index < count and pairs[index][0] == 2:
                name = pairs[index][1].upper()
                index += 1
            start = index
            while index < count and not (pairs[index][0] == 0 and pairs[index][1].upper() == "ENDSEC"):
                index += 1
            sections.append((name, pairs[start:index]))
            if index < count:
                index += 1
            continue
        index += 1
    return sections


def _parse_blocks(pairs):
    blocks = {}
    index = 0
    count = len(pairs)
    while index < count:
        code, value = pairs[index]
        if code == 0 and value.upper() == "BLOCK":
            body = []
            index += 1
            while index < count and not (pairs[index][0] == 0 and pairs[index][1].upper() == "ENDBLK"):
                body.append(pairs[index])
                index += 1
            name, base, entities = _block_record(body)
            if name:
                blocks[name.upper()] = {"base": base, "entities": entities}
            if index < count:
                index += 1
            continue
        index += 1
    return blocks


def _block_record(pairs):
    header = []
    for pair in pairs:
        if pair[0] == 0:
            break
        header.append(pair)
    name = _first_str(header, 2)
    base = _point(header, 10, 20, 30) or (0.0, 0.0, 0.0)
    entities = _model_entities(pairs)
    return name, base, entities


def _model_entities(pairs):
    raw, _end = _collect_entities(pairs)
    kept = []
    for entity in raw:
        if _is_paper_space(entity["pairs"]):
            continue
        kept.append(entity)
    return _absorb_polylines(kept)


def _collect_entities(pairs):
    entities = []
    current = None
    index = 0
    count = len(pairs)
    while index < count:
        code, value = pairs[index]
        if code == 0:
            if current is not None:
                entities.append(current)
            name = value.upper()
            if name in ("ENDSEC", "ENDBLK"):
                return entities, index
            current = {"type": name, "pairs": []}
        elif current is not None:
            current["pairs"].append((code, value))
        index += 1
    if current is not None:
        entities.append(current)
    return entities, index


def _absorb_polylines(entities):
    absorbed = []
    index = 0
    count = len(entities)
    while index < count:
        entity = entities[index]
        if entity["type"] != "POLYLINE":
            absorbed.append(entity)
            index += 1
            continue
        vertices = []
        index += 1
        while index < count and entities[index]["type"] != "SEQEND":
            if entities[index]["type"] == "VERTEX":
                vertices.append(entities[index])
            index += 1
        absorbed.append({"type": "POLYLINE", "pairs": entity["pairs"], "vertices": vertices})
        if index < count and entities[index]["type"] == "SEQEND":
            index += 1
    return absorbed


def _is_paper_space(pairs):
    for code, value in pairs:
        if code == 67 and value.strip() == "1":
            return True
    return False


def _entities_to_polylines(entities, blocks, depth, stack, skipped):
    polylines = []
    if depth > 8:
        return polylines
    for entity in entities:
        kind = entity["type"]
        if kind == "LINE":
            poly = _line_poly(entity["pairs"])
            if poly is not None:
                polylines.append(poly)
        elif kind == "LWPOLYLINE":
            poly = _lwpolyline_poly(entity["pairs"])
            if poly is not None:
                polylines.append(poly)
        elif kind == "POLYLINE":
            poly = _polyline_poly(entity)
            if poly is not None:
                polylines.append(poly)
        elif kind == "ARC":
            poly = _arc_poly(entity["pairs"])
            if poly is not None:
                polylines.append(poly)
            else:
                _note_skip(skipped, kind)
        elif kind == "CIRCLE":
            poly = _circle_poly(entity["pairs"])
            if poly is not None:
                polylines.append(poly)
            else:
                _note_skip(skipped, kind)
        elif kind == "SPLINE":
            poly = _spline_poly(entity["pairs"])
            if poly is not None:
                polylines.append(poly)
            else:
                _note_skip(skipped, kind)
        elif kind == "INSERT":
            polylines.extend(_insert_polys(entity["pairs"], blocks, depth, stack, skipped))
        else:
            _note_skip(skipped, kind)
    return polylines


def _line_poly(pairs):
    start = _point(pairs, 10, 20, 30)
    end = _point(pairs, 11, 21, 31)
    if start is None or end is None:
        return None
    points = [start, end]
    if _dist(points[0], points[1]) <= 1e-9:
        return None
    return {"points": points, "closed": False}


def _lwpolyline_poly(pairs):
    vertices = []
    current = None
    elevation = 0.0
    for code, value in pairs:
        if code == 38:
            elevation = _as_float(value)
        elif code == 10:
            if current is not None:
                vertices.append(current)
            current = [_as_float(value), 0.0, 0.0]
        elif code == 20 and current is not None:
            current[1] = _as_float(value)
        elif code == 30 and current is not None:
            current[2] = _as_float(value)
        elif code == 42 and current is not None:
            current.append(_as_float(value))
    if current is not None:
        vertices.append(current)
    closed = _flag_closed(pairs)
    return _vertices_to_poly(vertices, elevation, closed)


def _polyline_poly(entity):
    vertices = []
    elevation = 0.0
    for vertex in entity.get("vertices", []):
        point = _point(vertex["pairs"], 10, 20, 30)
        if point is None:
            continue
        bulge = _first_float(vertex["pairs"], 42, 0.0)
        vertices.append([point[0], point[1], point[2], bulge])
    closed = _flag_closed(entity["pairs"])
    return _vertices_to_poly(vertices, elevation, closed)


def _vertices_to_poly(vertices, elevation, closed):
    if len(vertices) < 2:
        return None
    raw = []
    for vertex in vertices:
        z = vertex[2] if abs(vertex[2]) > 1e-12 else elevation
        bulge = vertex[3] if len(vertex) > 3 else 0.0
        raw.append((vertex[0], vertex[1], z, bulge))
    points = [(raw[0][0], raw[0][1], raw[0][2])]
    count = len(raw)
    last = count if closed else count - 1
    for index in range(last):
        a = raw[index]
        b = raw[(index + 1) % count]
        extra = _bulge_points(a, b, a[3], 0.5)
        points.extend(extra)
    scaled = _drop_duplicates(points)
    if closed and len(scaled) > 2 and _dist(scaled[0], scaled[-1]) <= 1e-6:
        scaled = scaled[:-1]
    if len(scaled) < 2:
        return None
    return {"points": scaled, "closed": closed}


def _arc_poly(pairs):
    center = _point(pairs, 10, 20, 30)
    if center is None:
        return None
    radius = _first_float(pairs, 40, 0.0)
    if radius == 0.0:
        return None
    start = _first_float(pairs, 50, 0.0)
    end = _first_float(pairs, 51, 0.0)
    points = _arc_points(center, radius, start, end, 0.5)
    scaled = _drop_duplicates(points)
    if len(scaled) < 2:
        return None
    return {"points": scaled, "closed": False}


def _circle_poly(pairs):
    center = _point(pairs, 10, 20, 30)
    if center is None:
        return None
    radius = _first_float(pairs, 40, 0.0)
    if radius <= 0.0:
        return None
    points = _arc_points(center, radius, 0.0, 360.0, 0.5)
    scaled = _drop_duplicates(points)
    if len(scaled) > 2 and _dist(scaled[0], scaled[-1]) <= 1e-6:
        scaled = scaled[:-1]
    if len(scaled) < 2:
        return None
    return {"points": scaled, "closed": True}


def _spline_poly(pairs):
    flags = int(_first_float(pairs, 70, 0.0))
    closed = bool(flags & 3)
    controls = _xyz_series(pairs, 10, 20, 30)
    degree = int(_first_float(pairs, 71, 0.0))
    knots = [_as_float(value) for value in _values(pairs, 40)]
    need = len(controls) + degree + 1
    if degree >= 1 and len(controls) >= degree + 1 and len(knots) >= need:
        knots = knots[:need]
        knots_ok = True
        for index in range(1, len(knots)):
            if knots[index] + 1e-12 < knots[index - 1]:
                knots_ok = False
                break
        if knots_ok:
            weights = [_as_float(value) for value in _values(pairs, 41)]
            if len(weights) != len(controls):
                weights = [1.0] * len(controls)
            points = _sample_spline(controls, knots, degree, weights)
            if points is not None:
                points = _drop_duplicates(points)
                if len(points) > 2 and _dist(points[0], points[-1]) <= 1e-6:
                    points = points[:-1]
                    closed = True
                if len(points) >= 2:
                    return {"points": points, "closed": closed}
    fit = _xyz_series(pairs, 11, 21, 31)
    if len(fit) >= 2:
        points = _drop_duplicates(fit)
        if len(points) > 2 and _dist(points[0], points[-1]) <= 1e-6:
            points = points[:-1]
            closed = True
        if len(points) >= 2:
            return {"points": points, "closed": closed}
    if len(controls) >= 2:
        points = _drop_duplicates(controls)
        if len(points) > 2 and _dist(points[0], points[-1]) <= 1e-6:
            points = points[:-1]
            closed = True
        if len(points) >= 2:
            return {"points": points, "closed": closed}
    return None


def _sample_spline(controls, knots, degree, weights):
    u0 = knots[degree]
    u1 = knots[len(controls)]
    if u1 <= u0 + 1e-15:
        return None
    start = _spline_at(controls, knots, degree, weights, u0)
    end = _spline_at(controls, knots, degree, weights, u1)
    if start is None or end is None:
        return None
    points = [start]
    _append_spline(points, controls, knots, degree, weights, u0, u1, start, end, 0)
    return points


def _append_spline(points, controls, knots, degree, weights, u0, u1, p0, p1, depth):
    um = 0.5 * (u0 + u1)
    mid = _spline_at(controls, knots, degree, weights, um)
    if mid is None:
        points.append(p1)
        return
    deviation = _point_segment_distance(mid, p0, p1)
    if depth < 14 and deviation > 0.5:
        _append_spline(points, controls, knots, degree, weights, u0, um, p0, mid, depth + 1)
        _append_spline(points, controls, knots, degree, weights, um, u1, mid, p1, depth + 1)
        return
    if depth < 8:
        left = _spline_at(controls, knots, degree, weights, 0.5 * (u0 + um))
        right = _spline_at(controls, knots, degree, weights, 0.5 * (um + u1))
        left_off = left is not None and _point_segment_distance(left, p0, mid) > 0.5
        right_off = right is not None and _point_segment_distance(right, mid, p1) > 0.5
        if left_off or right_off:
            _append_spline(points, controls, knots, degree, weights, u0, um, p0, mid, depth + 1)
            _append_spline(points, controls, knots, degree, weights, um, u1, mid, p1, depth + 1)
            return
    points.append(p1)


def _spline_at(controls, knots, degree, weights, u):
    homo = []
    for control, weight in zip(controls, weights):
        homo.append((control[0] * weight, control[1] * weight, control[2] * weight, weight))
    point = _de_boor(homo, knots, degree, u)
    if point is None or abs(point[3]) <= 1e-15:
        return None
    return (point[0] / point[3], point[1] / point[3], point[2] / point[3])


def _de_boor(controls, knots, degree, u):
    count = len(controls) - 1
    span = _knot_span(knots, degree, count, u)
    if span < degree:
        return None
    work = [controls[span - degree + index] for index in range(degree + 1)]
    for level in range(1, degree + 1):
        for index in range(degree, level - 1, -1):
            left = knots[span - degree + index]
            right = knots[span + 1 + index - level]
            denom = right - left
            alpha = 0.0 if abs(denom) <= 1e-15 else (u - left) / denom
            previous = work[index - 1]
            current = work[index]
            work[index] = tuple(
                (1.0 - alpha) * previous[axis] + alpha * current[axis] for axis in range(4)
            )
    return work[degree]


def _knot_span(knots, degree, count, u):
    if u >= knots[count + 1]:
        return count
    if u <= knots[degree]:
        return degree
    low = degree
    high = count + 1
    while high - low > 1:
        mid = (low + high) // 2
        if u < knots[mid]:
            high = mid
        else:
            low = mid
    return low


def _point_segment_distance(point, start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    length2 = dx * dx + dy * dy + dz * dz
    if length2 <= 1e-18:
        return _dist(point, start)
    ratio = (
        (point[0] - start[0]) * dx
        + (point[1] - start[1]) * dy
        + (point[2] - start[2]) * dz
    ) / length2
    if ratio < 0.0:
        ratio = 0.0
    elif ratio > 1.0:
        ratio = 1.0
    nearest = (start[0] + ratio * dx, start[1] + ratio * dy, start[2] + ratio * dz)
    return _dist(point, nearest)


def _insert_polys(pairs, blocks, depth, stack, skipped):
    name = ""
    for code, value in pairs:
        if code == 2:
            name = value.upper()
            break
    if name == "" or name in stack or name not in blocks:
        return []
    block = blocks[name]
    origin = _point(pairs, 10, 20, 30) or (0.0, 0.0, 0.0)
    sx = _first_float(pairs, 41, 1.0)
    sy = _first_float(pairs, 42, 1.0)
    rotation = _first_float(pairs, 50, 0.0)
    nested = _entities_to_polylines(block["entities"], blocks, depth + 1, stack + (name,), skipped)
    moved = []
    base = block["base"]
    for poly in nested:
        points = []
        for point in poly["points"]:
            local = (point[0] - base[0], point[1] - base[1], point[2] - base[2])
            turned = _rotate_scale(local, sx, sy, rotation)
            points.append((turned[0] + origin[0], turned[1] + origin[1], turned[2] + origin[2]))
        points = _drop_duplicates(points)
        if len(points) >= 2:
            moved.append({"points": points, "closed": poly["closed"]})
    return moved


def _rotate_scale(point, sx, sy, rotation_deg):
    x = point[0] * sx
    y = point[1] * sy
    angle = math.radians(rotation_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    return (c * x - s * y, s * x + c * y, point[2] * sx)


def _bulge_points(start, end, bulge, chord):
    if abs(bulge) < 1e-12:
        return [(end[0], end[1], end[2])]
    x1, y1, z1 = start[0], start[1], start[2]
    x2, y2, z2 = end[0], end[1], end[2]
    dx = x2 - x1
    dy = y2 - y1
    span = math.hypot(dx, dy)
    if span <= 1e-12:
        return [(x2, y2, z2)]
    angle = 4.0 * math.atan(bulge)
    radius = span / (2.0 * math.sin(angle / 2.0))
    mx = (x1 + x2) / 2.0
    my = (y1 + y2) / 2.0
    dist_mid = math.sqrt(max(radius * radius - (span / 2.0) ** 2, 0.0))
    px = -dy / span
    py = dx / span
    if bulge < 0.0:
        px = -px
        py = -py
    if abs(angle) > math.pi:
        px = -px
        py = -py
    cx = mx + px * dist_mid
    cy = my + py * dist_mid
    a0 = math.atan2(y1 - cy, x1 - cx)
    arc_len = abs(radius * angle)
    pieces = max(1, int(math.ceil(arc_len / max(chord, 1e-6))))
    points = []
    for step_index in range(1, pieces + 1):
        theta = a0 + angle * (step_index / pieces)
        z = z1 + (z2 - z1) * (step_index / pieces)
        points.append((cx + abs(radius) * math.cos(theta), cy + abs(radius) * math.sin(theta), z))
    points[-1] = (x2, y2, z2)
    return points


def _arc_points(center, radius, start_deg, end_deg, chord):
    start = math.radians(start_deg)
    end = math.radians(end_deg)
    if end <= start:
        end += 2.0 * math.pi
    sweep = end - start
    arc_len = abs(radius) * sweep
    pieces = max(1, int(math.ceil(arc_len / max(chord, 1e-6))))
    points = []
    for step_index in range(pieces + 1):
        theta = start + sweep * (step_index / pieces)
        points.append((
            center[0] + radius * math.cos(theta),
            center[1] + radius * math.sin(theta),
            center[2],
        ))
    return points


def _flag_closed(pairs):
    flag = int(_first_float(pairs, 70, 0.0))
    return bool(flag & 1)


def _point(pairs, x_code, y_code, z_code):
    xs = _values(pairs, x_code)
    ys = _values(pairs, y_code)
    zs = _values(pairs, z_code)
    if not xs or not ys:
        return None
    return (
        _as_float(xs[0]),
        _as_float(ys[0]),
        _as_float(zs[0]) if zs else 0.0,
    )


def _xyz_series(pairs, x_code, y_code, z_code):
    points = []
    current = None
    for code, value in pairs:
        if code == x_code:
            if current is not None:
                points.append(tuple(current))
            current = [_as_float(value), 0.0, 0.0]
        elif code == y_code and current is not None:
            current[1] = _as_float(value)
        elif code == z_code and current is not None:
            current[2] = _as_float(value)
    if current is not None:
        points.append(tuple(current))
    return points


def _values(pairs, wanted):
    return [value for code, value in pairs if code == wanted]


def _first_str(pairs, code):
    for pair_code, value in pairs:
        if pair_code == code:
            return value
    return ""


def _note_skip(skipped, kind):
    skipped[kind] = skipped.get(kind, 0) + 1


def _first_float(pairs, code, default):
    for pair_code, value in pairs:
        if pair_code == code:
            return _as_float(value)
    return default


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _drop_duplicates(points):
    if not points:
        return []
    kept = [points[0]]
    for point in points[1:]:
        if _dist(point, kept[-1]) > 1e-9:
            kept.append(point)
    return kept


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)
