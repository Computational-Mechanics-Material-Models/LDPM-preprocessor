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
##
## ===========================================================================
##
## Tag facet mF values for 3DCP-LDPM interlayer regions.
##
## ===========================================================================

import math

import numpy as np

from freecad.ldpmWorkbench.input.read_custom_interlayer import (
    build_custom_surfaces,
    parse_custom_interlayer,
)

_AXIS = {"X": 0, "Y": 1, "Z": 2}
_UNBOUNDED = 1e30


def _report(msg):
    text = str(msg)
    try:
        import FreeCAD as App
        App.Console.PrintMessage(text + ("" if text.endswith("\n") else "\n"))
    except Exception:
        print(text)


_CANONICAL_AXES = ("X", "Y", "Z")


def _interface_positions(origin, extent, first_layer, layer_thickness):

    if first_layer <= 0 or layer_thickness <= 0 or extent <= first_layer:
        return []

    positions = []
    pos = origin + first_layer
    end = origin + extent
    while pos < end - 1e-9:
        positions.append(pos)
        pos += layer_thickness
    return positions


def _width_interface_positions(origin, extent, layer_width):

    if layer_width <= 0 or extent <= layer_width:
        return []

    positions = []
    pos = origin + layer_width
    end = origin + extent
    while pos < end - 1e-9:
        positions.append(pos)
        pos += layer_width
    return positions


def _band_mask(coords, positions, half_band):

    mask = np.zeros(len(coords), dtype=bool)
    for center in positions:
        mask |= (coords >= center - half_band) & (coords <= center + half_band)
    return mask


def _axis_mf_map(enabled_axes, params=None):

    defaults = {"X": 2, "Y": 3, "Z": 4}
    params = params or {}
    axis_mf = {
        "X": int(params.get("xMf", defaults["X"])),
        "Y": int(params.get("yMf", defaults["Y"])),
        "Z": int(params.get("zMf", defaults["Z"])),
    }
    return {ax: axis_mf[ax] for ax in _CANONICAL_AXES if ax in enabled_axes}


def _merge_direction_configs(multi_directions):

    merged = {}
    for entry in multi_directions:
        if not entry.get("enabled"):
            continue
        axis = str(entry.get("axis", "Z")).strip().upper()
        if axis not in _AXIS:
            continue
        mode = str(entry.get("mode", "Height")).strip().title()
        if mode not in ("Width", "Height"):
            mode = "Height"
        if axis in merged and merged[axis] != mode:
            _report(f"3DCP interlayer: axis {axis} has conflicting modes; using first entry.")
            continue
        merged[axis] = mode
    return merged


def apply_unidirectional(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    axis = _AXIS.get(str(params.get("axis", "Z")).strip().upper(), 2)
    minC = np.asarray(minC, dtype=float).reshape(3)
    maxC = np.asarray(maxC, dtype=float).reshape(3)

    origin = minC[axis]
    extent = maxC[axis] - minC[axis]
    first_layer = float(params.get("firstLayerThickness", 1.0))
    layer_thickness = float(params.get("layerThickness", 1.0))
    bulk_mf = int(params.get("bulkMf", 1))
    interlayer_mf = int(params.get("interlayerMf", 2))

    positions = _interface_positions(origin, extent, first_layer, layer_thickness)
    if not positions:
        _report("3DCP interlayer: no interfaces found")
        return 0

    half_band = interface_thickness / 2.0
    coords = facetData[:, 6 + axis]
    mask = _band_mask(coords, positions, half_band)

    n_tagged = int(np.count_nonzero(mask))
    if n_tagged > 0:
        facetData[~mask, 18] = bulk_mf
        facetMaterial[~mask] = bulk_mf
        facetData[mask, 18] = interlayer_mf
        facetMaterial[mask] = interlayer_mf
        _report(
            f"3DCP interlayer: tagged {n_tagged} facets along {params.get('axis', 'Z')}-axis "
            f"({len(positions)} interfaces, bulk mF={bulk_mf}, interlayer mF={interlayer_mf})"
        )
    else:
        _report("3DCP interlayer: no facets tagged")

    return n_tagged


def apply_multidirectional(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    axis_modes = _merge_direction_configs(params.get("multiDirections", []))
    if not axis_modes:
        _report("3DCP interlayer: multidirectional enabled but no axis selected; skipping.")
        return 0

    minC = np.asarray(minC, dtype=float).reshape(3)
    maxC = np.asarray(maxC, dtype=float).reshape(3)
    first_layer = float(params.get("firstLayerThickness", 1.0))
    layer_thickness = float(params.get("layerThickness", 1.0))
    layer_width = float(params.get("layerWidth", 1.0))
    bulk_mf = int(params.get("bulkMf", 1))
    overlap_mf = int(params.get("overlapMf", 5))
    half_band = interface_thickness / 2.0

    axis_masks = {}
    axis_counts = {}
    for axis, mode in axis_modes.items():
        axis_idx = _AXIS[axis]
        origin = minC[axis_idx]
        extent = maxC[axis_idx] - minC[axis_idx]
        if mode == "Height":
            positions = _interface_positions(origin, extent, first_layer, layer_thickness)
        else:
            positions = _width_interface_positions(origin, extent, layer_width)
        axis_counts[axis] = len(positions)
        if not positions:
            continue
        coords = facetData[:, 6 + axis_idx]
        axis_masks[axis] = _band_mask(coords, positions, half_band)

    if not axis_masks:
        _report("3DCP interlayer: no multidirectional interfaces found")
        return 0

    mf_map = _axis_mf_map(axis_masks.keys(), params)
    n_facets = len(facetData)
    hit_count = np.zeros(n_facets, dtype=int)
    for mask in axis_masks.values():
        hit_count[mask] += 1

    final_mf = np.full(n_facets, bulk_mf, dtype=int)
    for axis, mask in axis_masks.items():
        single = mask & (hit_count == 1)
        final_mf[single] = mf_map[axis]
    overlap = hit_count >= 2
    final_mf[overlap] = overlap_mf

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf

    n_interface = int(np.count_nonzero(hit_count > 0))
    n_overlap = int(np.count_nonzero(overlap))
    axis_summary = ", ".join(f"{ax}={axis_counts.get(ax, 0)}" for ax in mf_map)
    _report(
        f"3DCP interlayer: multidirectional tagged {n_interface} facets "
        f"(bulk mF={bulk_mf}, overlap mF={overlap_mf}, overlap facets={n_overlap}, interfaces: {axis_summary})"
    )
    return n_interface


def _footprint_mask(facetData, block):

    a0, a1 = block["planeAxes"]
    a0_idx = _AXIS[a0]
    a1_idx = _AXIS[a1]
    vals0 = [corner[a0] for corner in block["corners"]]
    vals1 = [corner[a1] for corner in block["corners"]]
    c0 = facetData[:, 6 + a0_idx]
    c1 = facetData[:, 6 + a1_idx]
    return (
        (c0 >= min(vals0))
        & (c0 <= max(vals0))
        & (c1 >= min(vals1))
        & (c1 <= max(vals1))
    )


def _polygon_mask(c0, c1, polygon):

    poly = np.asarray(polygon, dtype=float).reshape(-1, 2)
    if len(poly) >= 2 and np.allclose(poly[0], poly[-1]):
        poly = poly[:-1]
    count = len(poly)
    if count < 3:
        return np.zeros(len(c0), dtype=bool)
    x = np.asarray(c0, dtype=float)
    y = np.asarray(c1, dtype=float)
    inside = np.zeros(len(x), dtype=bool)
    prev = count - 1
    for index in range(count):
        xi = poly[index, 0]
        yi = poly[index, 1]
        xj = poly[prev, 0]
        yj = poly[prev, 1]
        denom = yj - yi
        if abs(denom) < 1e-30:
            denom = 1e-30
        crosses = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / denom + xi)
        inside ^= crosses
        prev = index
    return inside


def _point_in_polygon_2d_scalar(x, y, polygon):

    poly = np.asarray(polygon, dtype=float).reshape(-1, 2)
    if len(poly) >= 2 and np.allclose(poly[0], poly[-1]):
        poly = poly[:-1]
    count = len(poly)
    if count < 3:
        return False
    inside = False
    prev = count - 1
    for index in range(count):
        xi = poly[index, 0]
        yi = poly[index, 1]
        xj = poly[prev, 0]
        yj = poly[prev, 1]
        denom = yj - yi
        if abs(denom) < 1e-30:
            denom = 1e-30
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / denom + xi:
            inside = not inside
        prev = index
    return inside


def _polygon_slab_region(axis_idx, pos, half_band, plane_axes, corners):

    a0, a1 = plane_axes
    a0_idx = _AXIS[a0]
    a1_idx = _AXIS[a1]
    poly = np.array([[corner[a0], corner[a1]] for corner in corners], dtype=float)
    return {
        "type": "polygon_slab",
        "axis_idx": int(axis_idx),
        "pos": float(pos),
        "half_band": float(half_band),
        "a0_idx": int(a0_idx),
        "a1_idx": int(a1_idx),
        "poly": poly,
    }


def _segment_intersects_polygon_slab(p1, p2, region):

    p1 = np.asarray(p1, dtype=float).reshape(3)
    p2 = np.asarray(p2, dtype=float).reshape(3)
    axis_idx = region["axis_idx"]
    pos = region["pos"]
    half_band = region["half_band"]
    a0_idx = region["a0_idx"]
    a1_idx = region["a1_idx"]
    poly = region["poly"]
    span = float(np.linalg.norm(p2 - p1))
    step = max(half_band, 1e-3)
    samples = max(2, int(math.ceil(span / step)) + 1)
    for i in range(samples):
        t = i / float(samples - 1) if samples > 1 else 0.0
        p = (1.0 - t) * p1 + t * p2
        if abs(p[axis_idx] - pos) > half_band:
            continue
        if _point_in_polygon_2d_scalar(p[a0_idx], p[a1_idx], poly):
            return True
    return False


def _cross_2d(o, a, b):

    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _point_in_triangle_2d(p, a, b, c):

    cross = _cross_2d(a, b, c)
    if cross <= 1e-12:
        return False
    s1 = _cross_2d(a, b, p)
    s2 = _cross_2d(b, c, p)
    s3 = _cross_2d(c, a, p)
    has_neg = (s1 < -1e-12) or (s2 < -1e-12) or (s3 < -1e-12)
    has_pos = (s1 > 1e-12) or (s2 > 1e-12) or (s3 > 1e-12)
    return not (has_neg and has_pos)


def _triangulate_polygon_2d(polygon):

    poly = np.asarray(polygon, dtype=float).reshape(-1, 2)
    if len(poly) >= 2 and np.allclose(poly[0], poly[-1]):
        poly = poly[:-1]
    if len(poly) < 3:
        return []
    if len(poly) == 3:
        return [(0, 1, 2)]
    verts = [tuple(pt) for pt in poly]
    indices = list(range(len(verts)))
    triangles = []
    guard = 0
    while len(indices) > 3 and guard < len(indices) * len(indices):
        guard += 1
        n = len(indices)
        ear_found = False
        for i in range(n):
            i0 = indices[(i - 1) % n]
            i1 = indices[i]
            i2 = indices[(i + 1) % n]
            a, b, c = verts[i0], verts[i1], verts[i2]
            cross = _cross_2d(a, b, c)
            if cross <= 1e-12:
                continue
            is_ear = True
            for j in indices:
                if j in (i0, i1, i2):
                    continue
                if _point_in_triangle_2d(verts[j], a, b, c):
                    is_ear = False
                    break
            if not is_ear:
                continue
            triangles.append((i0, i1, i2))
            del indices[i]
            ear_found = True
            break
        if not ear_found:
            break
    if len(indices) == 3:
        triangles.append(tuple(indices))
    return triangles


def _custom_surfaces(params):

    surfaces = params.get("customSurfaces")
    mode = str(params.get("customMode", "fourPoint")).strip()
    if mode in ("pathRibbon", "dxfImport") and not surfaces:
        notes = list(params.get("customSurfaceNotes") or [])
        try:
            surfaces, built_notes = build_custom_surfaces(params)
            notes.extend(built_notes)
        except Exception as exc:
            surfaces = []
            notes.append(str(exc))
        params["customSurfaces"] = surfaces or []
        params["customSurfaceNotes"] = notes
    return params.get("customSurfaces") or []


def _shift_surface(surface, minC):

    a0, a1 = surface["planeAxes"]
    polygon = [
        [
            point[0] + minC[_AXIS[a0]],
            point[1] + minC[_AXIS[a1]],
        ]
        for point in surface["polygon"]
    ]
    axis_idx = _AXIS[surface["axis"]]
    positions = [float(pos) + minC[axis_idx] for pos in surface["positions"]]
    shifted = dict(surface)
    shifted["polygon"] = polygon
    shifted["positions"] = positions
    return shifted


def apply_custom_surfaces(facetData, facetMaterial, minC, params, surfaces):

    for note in params.get("customSurfaceNotes") or []:
        _report("3DCP interlayer: " + str(note))

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0 or not surfaces:
        if not surfaces:
            _report("3DCP interlayer: no custom surfaces found")
        return 0

    minC = np.asarray(minC, dtype=float).reshape(3)
    bulk_mf = int(params.get("bulkMf", 1))
    half_band = interface_thickness / 2.0
    final_mf = np.full(len(facetData), bulk_mf, dtype=int)

    for surface in surfaces:
        surface = _shift_surface(surface, minC)
        axis_idx = _AXIS[surface["axis"]]
        a0, a1 = surface["planeAxes"]
        coords = facetData[:, 6 + axis_idx]
        c0 = facetData[:, 6 + _AXIS[a0]]
        c1 = facetData[:, 6 + _AXIS[a1]]
        mask = _band_mask(coords, surface["positions"], half_band) & _polygon_mask(c0, c1, surface["polygon"])
        final_mf[mask] = int(surface.get("mf", 2))

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf
    n_tagged = int(np.count_nonzero(final_mf != bulk_mf))
    if n_tagged > 0:
        _report(
            f"3DCP interlayer: custom surface tagged {n_tagged} facets "
            f"({len(surfaces)} surfaces, bulk mF={bulk_mf})"
        )
    else:
        _report("3DCP interlayer: no custom facets tagged")
    return n_tagged


def apply_custom(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    mode = str(params.get("customMode", "fourPoint")).strip()
    if mode in ("pathRibbon", "dxfImport"):
        return apply_custom_surfaces(
            facetData, facetMaterial, minC, params, _custom_surfaces(params)
        )

    blocks = params.get("customLayers") or []
    if not blocks and params.get("customDefinition"):
        blocks = parse_custom_interlayer(params["customDefinition"])
    if not blocks:
        _report("3DCP interlayer: no custom layers found")
        return 0

    minC = np.asarray(minC, dtype=float).reshape(3)

    bulk_mf = int(params.get("bulkMf", 1))

    half_band = interface_thickness / 2.0
    final_mf = np.full(len(facetData), bulk_mf, dtype=int)

    for block in blocks:
        axis_idx = _AXIS[block["axis"]]
        positions = list(dict.fromkeys(block.get("positions") or []))
        if not positions:
            continue
        positions = [p + minC[axis_idx] for p in positions]
        block = dict(block)
        block["corners"] = [
            {a: c[a] + minC[_AXIS[a]] for a in block["planeAxes"]}
            for c in block["corners"]
        ]
        coords = facetData[:, 6 + axis_idx]
        mask = _band_mask(coords, positions, half_band) & _footprint_mask(facetData, block)
        interlayer_mf = int(block.get("mf", 2))
        final_mf[mask] = interlayer_mf

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf

    n_tagged = int(np.count_nonzero(final_mf != bulk_mf))
    if n_tagged > 0:
        _report(
            f"3DCP interlayer: custom tagged {n_tagged} facets "
            f"({len(blocks)} layer blocks, bulk mF={bulk_mf})"
        )
    else:
        _report("3DCP interlayer: no custom facets tagged")

    return n_tagged


def _fused_line_z_positions(minC, layer_height, num_layers):
    if layer_height <= 0 or num_layers < 2:
        return []
    origin_z = float(minC[2])
    return [origin_z + (k + 1) * layer_height for k in range(num_layers - 1)]


def _apply_fused_contact_masks(facetData, facetMaterial, contacts, bulk_mf, overlap_mf, label):
    n_facets = len(facetData)
    final_mf = np.full(n_facets, bulk_mf, dtype=int)
    if not contacts:
        facetData[:, 18] = final_mf
        facetMaterial[:] = final_mf
        _report(f"3DCP interlayer: fused-surface {label} has no contacts; bulk mF={bulk_mf}")
        return 0

    hit_count = np.zeros(n_facets, dtype=int)
    for mask, _mf in contacts:
        hit_count[mask] += 1

    for mask, mf in contacts:
        single = mask & (hit_count == 1)
        final_mf[single] = int(mf)
    overlap = hit_count >= 2
    final_mf[overlap] = int(overlap_mf)

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf

    n_tagged = int(np.count_nonzero(hit_count > 0))
    n_overlap = int(np.count_nonzero(overlap))
    _report(
        f"3DCP interlayer: fused-surface {label} tagged {n_tagged} facets "
        f"(bulk mF={bulk_mf}, overlap mF={overlap_mf}, overlap facets={n_overlap}, "
        f"contacts={len(contacts)})"
    )
    return n_tagged


def _square_corner_contacts(facetData, side, layer_width, half_band, enable_x, enable_y, x_mf, y_mf):
    if side <= 0 or layer_width <= 0 or half_band <= 0:
        return []
    if not enable_x and not enable_y:
        return []

    hw = layer_width / 2.0
    cx = facetData[:, 6]
    cy = facetData[:, 7]
    joints = [(side, 0.0), (side, side), (0.0, side), (0.0, 0.0)]
    contacts = []
    for jx, jy in joints:
        if enable_x:
            mask = (np.abs(cx - jx) <= half_band) & (np.abs(cy - jy) <= hw)
            contacts.append((mask, x_mf))
        if enable_y:
            mask = (np.abs(cy - jy) <= half_band) & (np.abs(cx - jx) <= hw)
            contacts.append((mask, y_mf))
    return contacts


def _square_corner_regions(side, layer_width, half_band, enable_x, enable_y):
    if side <= 0 or layer_width <= 0 or half_band <= 0:
        return []
    if not enable_x and not enable_y:
        return []

    hw = layer_width / 2.0
    joints = [(side, 0.0), (side, side), (0.0, side), (0.0, 0.0)]
    regions = []
    for jx, jy in joints:
        if enable_x:
            mins = np.array([jx - half_band, jy - hw, -_UNBOUNDED], dtype=float)
            maxs = np.array([jx + half_band, jy + hw, _UNBOUNDED], dtype=float)
            regions.append((mins, maxs))
        if enable_y:
            mins = np.array([jx - hw, jy - half_band, -_UNBOUNDED], dtype=float)
            maxs = np.array([jx + hw, jy + half_band, _UNBOUNDED], dtype=float)
            regions.append((mins, maxs))
    return regions


def _sketch_polyline_pieces(sketch_name):
    if not sketch_name or not str(sketch_name).strip():
        return [], False
    try:
        import FreeCAD as App
        import Part
    except Exception:
        return [], False

    try:
        doc = App.ActiveDocument
        if doc is None:
            return [], False
        sketch_obj = doc.getObject(str(sketch_name).strip())
        if sketch_obj is None or sketch_obj.Shape is None or sketch_obj.Shape.isNull():
            return [], False
        edges = list(sketch_obj.Shape.Edges or [])
        if not edges:
            return [], False
        try:
            wire = Part.Wire(edges)
            closed = bool(wire.isClosed())
            use_edges = list(wire.Edges)
        except Exception:
            closed = False
            use_edges = edges

        pieces = []
        for edge in use_edges:
            try:
                pts = edge.discretize(Deflection=0.05)
            except Exception:
                try:
                    va = edge.Vertexes[0].Point
                    vb = edge.Vertexes[-1].Point
                    pts = [va, vb]
                except Exception:
                    continue
            for i in range(len(pts) - 1):
                x0, y0 = float(pts[i].x), float(pts[i].y)
                x1, y1 = float(pts[i + 1].x), float(pts[i + 1].y)
                if (x1 - x0) ** 2 + (y1 - y0) ** 2 > 1e-18:
                    pieces.append((x0, y0, x1, y1))
        return pieces, closed
    except Exception:
        return [], False


def _sketch_turn_joints(pieces, closed):
    if len(pieces) < 2:
        return []

    pairs = []
    for i in range(len(pieces) - 1):
        pairs.append((pieces[i], pieces[i + 1]))
    if closed and len(pieces) >= 2:
        pairs.append((pieces[-1], pieces[0]))

    joints = []
    for (x0, y0, x1, y1), (u0, v0, u1, v1) in pairs:
        dx0, dy0 = x1 - x0, y1 - y0
        dx1, dy1 = u1 - u0, v1 - v0
        l0 = (dx0 * dx0 + dy0 * dy0) ** 0.5
        l1 = (dx1 * dx1 + dy1 * dy1) ** 0.5
        if l0 < 1e-12 or l1 < 1e-12:
            continue
        tx0, ty0 = dx0 / l0, dy0 / l0
        tx1, ty1 = dx1 / l1, dy1 / l1
        if tx0 * tx1 + ty0 * ty1 >= 0.99:
            continue
        jx, jy = x1, y1
        joints.append((jx, jy, tx0, ty0))
        joints.append((jx, jy, tx1, ty1))
    return joints


def _classify_tangent_axis(tx, ty, axis_cos=0.965925826289):
    ax = abs(tx)
    ay = abs(ty)
    if ax >= axis_cos and ax >= ay:
        return "X"
    if ay >= axis_cos and ay >= ax:
        return "Y"
    return "D"


def _sketch_corner_contacts(
    facetData,
    sketch_name,
    layer_width,
    half_band,
    enable_x,
    enable_y,
    x_mf,
    y_mf,
    overlap_mf,
):
    if layer_width <= 0 or half_band <= 0:
        return []
    if not enable_x and not enable_y:
        return []

    pieces, closed = _sketch_polyline_pieces(sketch_name)
    if not pieces:
        _report(
            f"3DCP interlayer: fused-surface sketch '{sketch_name}' "
            "was not found or has no edges; side contacts skipped."
        )
        return []

    joints = _sketch_turn_joints(pieces, closed)
    if not joints:
        return []

    hw = layer_width / 2.0
    cx = facetData[:, 6]
    cy = facetData[:, 7]
    contacts = []
    for jx, jy, tx, ty in joints:
        kind = _classify_tangent_axis(tx, ty)
        if kind == "X":
            if not enable_x:
                continue
            mf = x_mf
        elif kind == "Y":
            if not enable_y:
                continue
            mf = y_mf
        else:
            if enable_x and enable_y:
                mf = overlap_mf
            elif enable_x:
                mf = x_mf
            elif enable_y:
                mf = y_mf
            else:
                continue

        px, py = -ty, tx
        dx = cx - jx
        dy = cy - jy
        along = dx * tx + dy * ty
        across = dx * px + dy * py
        mask = (np.abs(along) <= half_band) & (np.abs(across) <= hw)
        contacts.append((mask, mf))
    return contacts


def _sketch_corner_regions(sketch_name, layer_width, half_band, enable_x, enable_y):
    if layer_width <= 0 or half_band <= 0:
        return []
    if not enable_x and not enable_y:
        return []

    pieces, closed = _sketch_polyline_pieces(sketch_name)
    joints = _sketch_turn_joints(pieces, closed)
    if not joints:
        return []

    hw = layer_width / 2.0
    pad = max(half_band, hw)
    regions = []
    for jx, jy, tx, ty in joints:
        kind = _classify_tangent_axis(tx, ty)
        if kind == "X" and not enable_x:
            continue
        if kind == "Y" and not enable_y:
            continue
        if kind == "D" and not (enable_x or enable_y):
            continue
        mins = np.array([jx - pad, jy - pad, -_UNBOUNDED], dtype=float)
        maxs = np.array([jx + pad, jy + pad, _UNBOUNDED], dtype=float)
        regions.append((mins, maxs))
    return regions


def _raster_overlap(layer_height):
    return min(0.05, max(1e-3, 0.01 * float(layer_height)))


def _raster_z_positions(minC, layer_height, num_layers):
    if layer_height <= 0 or num_layers < 2:
        return []
    overlap = _raster_overlap(layer_height)
    z_step = layer_height - overlap
    origin = float(minC[2])
    return [origin + (k + 1) * z_step + overlap / 2.0 for k in range(num_layers - 1)]


def _raster_slice_z(minC, layer_height, num_layers, index):
    overlap = _raster_overlap(layer_height) if num_layers > 1 else 0.0
    z_step = layer_height - overlap if num_layers > 1 else layer_height
    z0 = float(minC[2]) + index * z_step
    return z0, z0 + layer_height


def _raster_angle(angles, index):
    if index < len(angles):
        try:
            return float(angles[index])
        except Exception:
            pass
    return 0.0 if index % 2 == 0 else 90.0


def _mf_for_direction(nx, ny, enable_x, enable_y, x_mf, y_mf, overlap_mf):
    kind = _classify_tangent_axis(nx, ny)
    if kind == "X":
        if not enable_x:
            return None
        return x_mf
    if kind == "Y":
        if not enable_y:
            return None
        return y_mf
    if enable_x and enable_y:
        return overlap_mf
    if enable_x:
        return x_mf
    if enable_y:
        return y_mf
    return None


def _raster_centerline(total_length, spacing, layer_width, num_lines, angle_deg):
    try:
        from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry import raster_qi_centerline
    except Exception as ex:
        _report("3DCP interlayer: raster path helper unavailable (" + str(ex) + ")")
        return None
    try:
        _pts, _dom, segs, hops, _cdom, normal = raster_qi_centerline(
            total_length, spacing, layer_width, num_lines, angle_deg, detail=True
        )
    except Exception as ex:
        _report("3DCP interlayer: raster centerline failed (" + str(ex) + ")")
        return None
    return segs, hops, float(normal[0]), float(normal[1])


def _raster_slice_contacts(
    facetData,
    segs,
    hops,
    nx,
    ny,
    touch,
    layer_width,
    half_band,
    z0,
    z1,
    enable_x,
    enable_y,
    x_mf,
    y_mf,
    overlap_mf,
):
    contacts = []
    regions = []
    if layer_width <= 0:
        return contacts, regions

    nlen = (nx * nx + ny * ny) ** 0.5
    if nlen < 1e-12:
        return contacts, regions
    nx, ny = nx / nlen, ny / nlen
    ux, uy = ny, -nx
    has_facets = facetData is not None and len(facetData) > 0
    if has_facets:
        cx = facetData[:, 6]
        cy = facetData[:, 7]
        cz = facetData[:, 8]
        zmask = (cz >= z0) & (cz <= z1)
    hw = layer_width / 2.0

    if touch and len(segs) >= 2:
        for i in range(len(segs) - 1):
            x0, y0, x1, y1 = segs[i]
            u0, v0, u1, v1 = segs[i + 1]
            s0 = nx * x0 + ny * y0
            s1 = nx * u0 + ny * v0
            if abs(s1 - s0) > layer_width + 1e-6:
                continue
            mid = 0.5 * (s0 + s1)
            t0a = ux * x0 + uy * y0
            t0b = ux * x1 + uy * y1
            t1a = ux * u0 + uy * v0
            t1b = ux * u1 + uy * v1
            lo = max(min(t0a, t0b), min(t1a, t1b))
            hi = min(max(t0a, t0b), max(t1a, t1b))
            if hi - lo < 1e-6:
                continue
            mf = _mf_for_direction(nx, ny, enable_x, enable_y, x_mf, y_mf, overlap_mf)
            if mf is None:
                continue
            if has_facets:
                along = cx * ux + cy * uy
                signed = cx * nx + cy * ny
                mask = zmask & (np.abs(signed - mid) <= half_band) & (along >= lo) & (along <= hi)
                contacts.append((mask, mf))
            pad = max(half_band, hw)
            px0 = nx * mid + ux * lo
            py0 = ny * mid + uy * lo
            px1 = nx * mid + ux * hi
            py1 = ny * mid + uy * hi
            regions.append((
                np.array([min(px0, px1) - pad, min(py0, py1) - pad, z0], dtype=float),
                np.array([max(px0, px1) + pad, max(py0, py1) + pad, z1], dtype=float),
            ))

    if hops and segs and (enable_x or enable_y):
        ends = []
        for x0, y0, x1, y1 in segs:
            dx, dy = x1 - x0, y1 - y0
            length = (dx * dx + dy * dy) ** 0.5
            if length < 1e-9:
                continue
            tx, ty = dx / length, dy / length
            ends.append((x0, y0, tx, ty))
            ends.append((x1, y1, tx, ty))
        seen = set()
        for hop in hops:
            for hx, hy in ((hop[0], hop[1]), (hop[2], hop[3])):
                for ex, ey, tx, ty in ends:
                    if (hx - ex) ** 2 + (hy - ey) ** 2 > 1e-6:
                        continue
                    key = (round(ex, 4), round(ey, 4), round(tx, 3), round(ty, 3))
                    if key in seen:
                        continue
                    seen.add(key)
                    mf = _mf_for_direction(tx, ty, enable_x, enable_y, x_mf, y_mf, overlap_mf)
                    if mf is None:
                        continue
                    px, py = -ty, tx
                    if has_facets:
                        dx = cx - ex
                        dy = cy - ey
                        along = dx * tx + dy * ty
                        across = dx * px + dy * py
                        mask = zmask & (np.abs(along) <= half_band) & (np.abs(across) <= hw)
                        contacts.append((mask, mf))
                    pad = max(half_band, hw)
                    regions.append((
                        np.array([ex - pad, ey - pad, z0], dtype=float),
                        np.array([ex + pad, ey + pad, z1], dtype=float),
                    ))
    return contacts, regions


def _raster_side_contacts(facetData, params, minC, half_band, enable_x, enable_y, x_mf, y_mf, overlap_mf):
    layer_width = float(params.get("layerWidth", 0.0))
    layer_height = float(params.get("layerHeight", 0.0))
    num_layers = max(1, int(params.get("numLayers", 1)))
    spacing_in = float(params.get("rasterSpacing", 0.0))
    total_length = float(params.get("pathDistance", 0.0))
    num_lines = max(1, int(params.get("rasterLoops", 1)))
    angles = params.get("rasterAngles") or []
    if layer_width <= 0 or layer_height <= 0 or total_length <= 0:
        _report("3DCP interlayer: raster fused surfaces missing layer size or path length")
        return [], []

    call_spacing = spacing_in if spacing_in >= layer_width else layer_width
    touch = spacing_in <= layer_width + 1e-6
    contacts = []
    regions = []
    for index in range(num_layers):
        angle = _raster_angle(angles, index)
        detail = _raster_centerline(total_length, call_spacing, layer_width, num_lines, angle)
        if detail is None:
            continue
        segs, hops, nx, ny = detail
        z0, z1 = _raster_slice_z(minC, layer_height, num_layers, index)
        slice_contacts, slice_regions = _raster_slice_contacts(
            facetData,
            segs,
            hops,
            nx,
            ny,
            touch,
            layer_width,
            half_band,
            z0,
            z1,
            enable_x,
            enable_y,
            x_mf,
            y_mf,
            overlap_mf,
        )
        contacts.extend(slice_contacts)
        regions.extend(slice_regions)
    return contacts, regions


def _circular_layer_bounds(params, minC):
    from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry import circular_seam_angles

    diameter = float(params.get("circularDiameter", 0.0) or 0.0)
    if diameter <= 0.0:
        diameter = float(params.get("pathDistance", 0.0) or 0.0)
    layer_width = float(params.get("layerWidth", 0.0))
    layer_height = float(params.get("layerHeight", 0.0))
    num_layers = max(1, int(params.get("numLayers", 1)))
    if diameter <= layer_width or layer_width <= 0.0 or layer_height <= 0.0:
        _report("3DCP interlayer: circular fused surfaces missing diameter or layer size")
        return None
    radius = diameter / 2.0
    seam_on = bool(params.get("circularSeam", False))
    angles = circular_seam_angles(
        num_layers,
        radius,
        layer_width,
        params.get("circularSeamMode", "Aligned"),
        seam_on,
    )
    return {
        "radius": radius,
        "inner_r": radius - layer_width / 2.0,
        "outer_r": radius + layer_width / 2.0,
        "layer_height": layer_height,
        "angles": angles,
        "origin_z": float(minC[2]),
    }


def _circular_seam_contacts(facetData, params, minC, half_band, enable_x, enable_y, x_mf, y_mf, overlap_mf):
    if half_band <= 0.0 or (not enable_x and not enable_y):
        return [], []
    spec = _circular_layer_bounds(params, minC)
    if spec is None:
        return [], []
    contacts = []
    regions = []
    has_facets = facetData is not None and len(facetData) > 0
    if has_facets:
        cx = facetData[:, 6]
        cy = facetData[:, 7]
        cz = facetData[:, 8]
        radius_xy = np.hypot(cx, cy)
    inner_r = spec["inner_r"]
    outer_r = spec["outer_r"]
    height = spec["layer_height"]
    for index, theta in enumerate(spec["angles"]):
        z0 = spec["origin_z"] + index * height
        z1 = z0 + height
        nx = -math.sin(theta)
        ny = math.cos(theta)
        mf = _mf_for_direction(nx, ny, enable_x, enable_y, x_mf, y_mf, overlap_mf)
        if mf is None:
            continue
        if has_facets:
            signed = cx * nx + cy * ny
            mask = (
                (cz >= z0)
                & (cz <= z1)
                & (np.abs(signed) <= half_band)
                & (radius_xy >= inner_r - 1e-6)
                & (radius_xy <= outer_r + 1e-6)
            )
            contacts.append((mask, mf))
        alpha = math.asin(min(1.0, half_band / max(inner_r, 1e-6)))
        xs = []
        ys = []
        for rr in (inner_r, outer_r):
            for ang in (theta - alpha, theta + alpha):
                xs.append(rr * math.cos(ang))
                ys.append(rr * math.sin(ang))
        pad = half_band
        regions.append((
            np.array([min(xs) - pad, min(ys) - pad, z0], dtype=float),
            np.array([max(xs) + pad, max(ys) + pad, z1], dtype=float),
        ))
    return contacts, regions


def apply_fused_surfaces(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    path_type = int(params.get("fusePathType", 0))
    if path_type not in (0, 1, 2, 3, 6):
        _report(
            f"3DCP interlayer: Fused Surfaces path index "
            f"{path_type} is not implemented yet; skipping."
        )
        return 0

    minC = np.asarray(minC, dtype=float).reshape(3)
    bulk_mf = int(params.get("bulkMf", 1))
    x_mf = int(params.get("xMf", 2))
    y_mf = int(params.get("yMf", 3))
    z_mf = int(params.get("zMf", 4))
    overlap_mf = int(params.get("overlapMf", 5))
    half_band = interface_thickness / 2.0
    num_layers = max(1, int(params.get("numLayers", 1)))
    layer_height = float(params.get("layerHeight", 0.0))
    layer_width = float(params.get("layerWidth", 0.0))
    enable_x = bool(params.get("fuseInterfaceX", False))
    enable_y = bool(params.get("fuseInterfaceY", False))
    enable_z = bool(params.get("fuseInterfaceZ", True))

    contacts = []
    path_label = "line"
    if path_type == 3:
        path_label = "raster"
        if enable_z:
            positions = _raster_z_positions(minC, layer_height, num_layers)
            if positions:
                coords = facetData[:, 6 + 2]
                contacts.append((_band_mask(coords, positions, half_band), z_mf))
        side_contacts, _side_regions = _raster_side_contacts(
            facetData, params, minC, half_band, enable_x, enable_y, x_mf, y_mf, overlap_mf
        )
        contacts.extend(side_contacts)
    elif enable_z:
        positions = _fused_line_z_positions(minC, layer_height, num_layers)
        if positions:
            coords = facetData[:, 6 + 2]
            contacts.append((_band_mask(coords, positions, half_band), z_mf))

    if path_type == 1:
        path_label = "square"
        side = float(params.get("pathDistance", 0.0))
        contacts.extend(
            _square_corner_contacts(
                facetData, side, layer_width, half_band, enable_x, enable_y, x_mf, y_mf
            )
        )
    elif path_type == 2:
        path_label = "sketch"
        sketch_name = params.get("fuseSketchName", "") or ""
        contacts.extend(
            _sketch_corner_contacts(
                facetData,
                sketch_name,
                layer_width,
                half_band,
                enable_x,
                enable_y,
                x_mf,
                y_mf,
                overlap_mf,
            )
        )
    elif path_type == 6:
        path_label = "circular"
        side_contacts, _side_regions = _circular_seam_contacts(
            facetData, params, minC, half_band, enable_x, enable_y, x_mf, y_mf, overlap_mf
        )
        contacts.extend(side_contacts)

    return _apply_fused_contact_masks(
        facetData, facetMaterial, contacts, bulk_mf, overlap_mf, path_label
    )


def apply_3DCP_interlayer(facetData, facetMaterial, minC, maxC, params):

    if not params.get("enabled", False):
        return 0

    interlayer_type = params.get("interlayerType", "")
    if interlayer_type == "Unidirectional Interlayer":
        return apply_unidirectional(facetData, facetMaterial, minC, maxC, params)
    if interlayer_type == "Multidirectional Interlayer":
        return apply_multidirectional(facetData, facetMaterial, minC, maxC, params)
    if interlayer_type == "Custom":
        return apply_custom(facetData, facetMaterial, minC, maxC, params)
    if interlayer_type in ("Fused Surfaces", "Interlayer at Fused Surfaces"):
        return apply_fused_surfaces(facetData, facetMaterial, minC, maxC, params)

    _report(f"Interlayer type '{interlayer_type}' is not implemented yet; skipping.")
    return 0


def _band_bbox(axis_idx, pos, half_band):
    mins = np.array([-_UNBOUNDED, -_UNBOUNDED, -_UNBOUNDED], dtype=float)
    maxs = np.array([_UNBOUNDED, _UNBOUNDED, _UNBOUNDED], dtype=float)
    mins[axis_idx] = pos - half_band
    maxs[axis_idx] = pos + half_band
    return mins, maxs


def _footprint_band_bbox(axis_idx, pos, half_band, plane_axes, corners):
    mins = np.array([-_UNBOUNDED, -_UNBOUNDED, -_UNBOUNDED], dtype=float)
    maxs = np.array([_UNBOUNDED, _UNBOUNDED, _UNBOUNDED], dtype=float)
    mins[axis_idx] = pos - half_band
    maxs[axis_idx] = pos + half_band
    a0, a1 = plane_axes
    a0_idx = _AXIS[a0]
    a1_idx = _AXIS[a1]
    vals0 = [corner[a0] for corner in corners]
    vals1 = [corner[a1] for corner in corners]
    mins[a0_idx] = min(vals0)
    maxs[a0_idx] = max(vals0)
    mins[a1_idx] = min(vals1)
    maxs[a1_idx] = max(vals1)
    return mins, maxs


def build_interface_regions(minC, maxC, params):
    if not params or not params.get("enabled", False):
        return []

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return []

    half_band = interface_thickness / 2.0
    minC = np.asarray(minC, dtype=float).reshape(3)
    maxC = np.asarray(maxC, dtype=float).reshape(3)
    interlayer_type = params.get("interlayerType", "")
    regions = []

    if interlayer_type == "Unidirectional Interlayer":
        axis_idx = _AXIS.get(str(params.get("axis", "Z")).strip().upper(), 2)
        origin = minC[axis_idx]
        extent = maxC[axis_idx] - minC[axis_idx]
        positions = _interface_positions(
            origin,
            extent,
            float(params.get("firstLayerThickness", 1.0)),
            float(params.get("layerThickness", 1.0)),
        )
        for pos in positions:
            regions.append(_band_bbox(axis_idx, pos, half_band))
        return regions

    if interlayer_type == "Multidirectional Interlayer":
        axis_modes = _merge_direction_configs(params.get("multiDirections", []))
        first_layer = float(params.get("firstLayerThickness", 1.0))
        layer_thickness = float(params.get("layerThickness", 1.0))
        layer_width = float(params.get("layerWidth", 1.0))
        for axis, mode in axis_modes.items():
            axis_idx = _AXIS[axis]
            origin = minC[axis_idx]
            extent = maxC[axis_idx] - minC[axis_idx]
            if mode == "Height":
                positions = _interface_positions(origin, extent, first_layer, layer_thickness)
            else:
                positions = _width_interface_positions(origin, extent, layer_width)
            for pos in positions:
                regions.append(_band_bbox(axis_idx, pos, half_band))
        return regions

    if interlayer_type == "Custom":
        mode = str(params.get("customMode", "fourPoint")).strip()
        if mode in ("pathRibbon", "dxfImport"):
            for surface in _custom_surfaces(params):
                axis_idx = _AXIS[surface["axis"]]
                positions = list(dict.fromkeys(surface.get("positions") or []))
                if not positions:
                    continue
                a0, a1 = surface["planeAxes"]
                corners = [
                    {a0: point[0] + minC[_AXIS[a0]], a1: point[1] + minC[_AXIS[a1]]}
                    for point in surface["polygon"]
                ]
                for pos in positions:
                    regions.append(
                        _polygon_slab_region(
                            axis_idx,
                            float(pos) + minC[axis_idx],
                            half_band,
                            surface["planeAxes"],
                            corners,
                        )
                    )
            return regions

        blocks = params.get("customLayers") or []
        if not blocks and params.get("customDefinition"):
            blocks = parse_custom_interlayer(params["customDefinition"])
        for block in blocks:
            axis_idx = _AXIS[block["axis"]]
            positions = list(dict.fromkeys(block.get("positions") or []))
            if not positions:
                continue
            corners = [
                {a: c[a] + minC[_AXIS[a]] for a in block["planeAxes"]}
                for c in block["corners"]
            ]
            for pos in positions:
                regions.append(
                    _footprint_band_bbox(
                        axis_idx,
                        pos + minC[axis_idx],
                        half_band,
                        block["planeAxes"],
                        corners,
                    )
                )
        return regions

    if interlayer_type in ("Fused Surfaces", "Interlayer at Fused Surfaces"):
        path_type = int(params.get("fusePathType", 0))
        if path_type not in (0, 1, 2, 3, 6):
            return regions

        enable_x = bool(params.get("fuseInterfaceX", False))
        enable_y = bool(params.get("fuseInterfaceY", False))
        enable_z = bool(params.get("fuseInterfaceZ", True))
        layer_width = float(params.get("layerWidth", 0.0))
        layer_height = float(params.get("layerHeight", 0.0))
        num_layers = max(1, int(params.get("numLayers", 1)))

        if enable_z:
            if path_type == 3:
                positions = _raster_z_positions(minC, layer_height, num_layers)
            else:
                positions = _fused_line_z_positions(minC, layer_height, num_layers)
            for pos in positions:
                regions.append(_band_bbox(2, pos, half_band))

        if path_type == 3:
            _side_contacts, side_regions = _raster_side_contacts(
                None,
                params,
                minC,
                half_band,
                enable_x,
                enable_y,
                int(params.get("xMf", 2)),
                int(params.get("yMf", 3)),
                int(params.get("overlapMf", 5)),
            )
            regions.extend(side_regions)
            return regions

        if path_type == 1:
            regions.extend(
                _square_corner_regions(
                    float(params.get("pathDistance", 0.0)),
                    layer_width,
                    half_band,
                    enable_x,
                    enable_y,
                )
            )
        elif path_type == 2:
            regions.extend(
                _sketch_corner_regions(
                    params.get("fuseSketchName", "") or "",
                    layer_width,
                    half_band,
                    enable_x,
                    enable_y,
                )
            )
        elif path_type == 6:
            _side_contacts, side_regions = _circular_seam_contacts(
                None,
                params,
                minC,
                half_band,
                enable_x,
                enable_y,
                int(params.get("xMf", 2)),
                int(params.get("yMf", 3)),
                int(params.get("overlapMf", 5)),
            )
            regions.extend(side_regions)
        return regions

    return regions


def _segment_intersects_aabb(p1, p2, mins, maxs):
    d = p2 - p1
    t0 = 0.0
    t1 = 1.0
    for i in range(3):
        if abs(d[i]) < 1e-15:
            if p1[i] < mins[i] or p1[i] > maxs[i]:
                return False
            continue
        inv = 1.0 / d[i]
        ta = (mins[i] - p1[i]) * inv
        tb = (maxs[i] - p1[i]) * inv
        if ta > tb:
            ta, tb = tb, ta
        if ta > t0:
            t0 = ta
        if tb < t1:
            t1 = tb
        if t0 > t1:
            return False
    return True


def custom_surface_preview_triangles(minC, params):

    if not params or not params.get("enabled", False):
        return []
    if params.get("interlayerType") != "Custom":
        return []
    mode = str(params.get("customMode", "fourPoint")).strip()
    if mode not in ("pathRibbon", "dxfImport"):
        return []

    minC = np.asarray(minC, dtype=float).reshape(3)
    triangles = []
    for surface in _custom_surfaces(params):
        surface = _shift_surface(surface, minC)
        a0, a1 = surface["planeAxes"]
        normal = _AXIS[surface["axis"]]
        i0 = _AXIS[a0]
        i1 = _AXIS[a1]
        polygon = surface.get("polygon") or []
        if len(polygon) < 3:
            continue
        for pos in surface.get("positions") or []:
            points = []
            for coord in polygon:
                point = [0.0, 0.0, 0.0]
                point[i0] = float(coord[0])
                point[i1] = float(coord[1])
                point[normal] = float(pos)
                points.append(point)
            poly_2d = [[float(coord[0]), float(coord[1])] for coord in polygon]
            for i0, i1, i2 in _triangulate_polygon_2d(poly_2d):
                triangles.append([points[i0], points[i1], points[i2]])
    return triangles


def fiber_crosses_interface(p1, p2, regions):
    if not regions:
        return False
    p1 = np.asarray(p1, dtype=float).reshape(3)
    p2 = np.asarray(p2, dtype=float).reshape(3)
    for region in regions:
        if isinstance(region, dict) and region.get("type") == "polygon_slab":
            if _segment_intersects_polygon_slab(p1, p2, region):
                return True
            continue
        mins, maxs = region
        if _segment_intersects_aabb(p1, p2, mins, maxs):
            return True
    return False
