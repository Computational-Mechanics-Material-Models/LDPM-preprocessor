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
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ===========================================================================
##
## This function creates a 3D geometric shape using dimensions and parameters 
## passed to it. The function supports several different shapes including 
## boxes, cylinders, cones, spheres, ellipsoids, arbitrary prisms, and notched 
## prisms of square, semi-circle, and semi-ellipse shapes. The 'Dogbone' 
## option creates a special 3D dogbone shape using specific dimensions passed 
## to the function.
##
## ===========================================================================

# pyright: reportMissingImports=false
import os
import random
import re
import math

from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs import file_extension, is_cad_geometry_file

import FreeCAD as App
import ImportGui
import Fem
import JoinFeatures
import BOPTools.JoinFeatures
import Part
import Sketcher
from FreeCAD import Base

try:
    import importDXF
except ImportError:
    try:
        from draftlibs import importDXF
    except ImportError:
        importDXF = None


def raster_qi_centerline(total_length, spacing, eff_w, num_lines, angle_deg, min_len_factor=0.0, detail=False):
    half_w = eff_w / 2.0
    half_outer = total_length / 2.0
    half_span = spacing * (num_lines - 1) / 2.0
    xmin, xmax = -half_outer, half_outer
    ymin, ymax = -(half_span + half_w), half_span + half_w

    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -math.sin(a), math.cos(a)
    if abs(ux) < 1e-12:
        ux = 0.0
    if abs(uy) < 1e-12:
        uy = 0.0
    if abs(nx) < 1e-12:
        nx = 0.0
    if abs(ny) < 1e-12:
        ny = 0.0

    cxmin, cxmax, cymin, cymax = xmin, xmax, ymin, ymax
    if cxmax - cxmin < 1e-9 or cymax - cymin < 1e-9:
        raise ValueError("Raster domain is empty; length/width incompatible.")

    def clip(ox, oy):
        hits = []
        eps = 1e-9

        def add(t):
            x = ox + t * ux
            y = oy + t * uy
            if cxmin - eps <= x <= cxmax + eps and cymin - eps <= y <= cymax + eps:
                hits.append((t, min(max(x, cxmin), cxmax), min(max(y, cymin), cymax)))

        if abs(ux) > 1e-14:
            add((cxmin - ox) / ux)
            add((cxmax - ox) / ux)
        if abs(uy) > 1e-14:
            add((cymin - oy) / uy)
            add((cymax - oy) / uy)
        hits.sort(key=lambda h: h[0])
        if len(hits) < 2 or abs(hits[-1][0] - hits[0][0]) < 1e-9:
            return None
        return (hits[0][1], hits[0][2], hits[-1][1], hits[-1][2])

    def snap(x, y):
        d = [abs(x - cxmin), abs(x - cxmax), abs(y - cymin), abs(y - cymax)]
        m = min(d)
        yy = min(max(y, cymin), cymax)
        xx = min(max(x, cxmin), cxmax)
        if m == d[0]:
            return (cxmin, yy)
        if m == d[1]:
            return (cxmax, yy)
        if m == d[2]:
            return (xx, cymin)
        return (xx, cymax)

    w = cxmax - cxmin
    h = cymax - cymin
    per = 2.0 * (w + h)

    def peri_param(x, y):
        x, y = snap(x, y)
        e = 1e-7
        if abs(y - cymin) <= e:
            return x - cxmin
        if abs(x - cxmax) <= e:
            return w + (y - cymin)
        if abs(y - cymax) <= e:
            return w + h + (cxmax - x)
        return 2.0 * w + h + (cymax - y)

    def peri_point(s):
        s %= per
        if s <= w:
            return (cxmin + s, cymin)
        s -= w
        if s <= h:
            return (cxmax, cymin + s)
        s -= h
        if s <= w:
            return (cxmax - s, cymax)
        s -= w
        return (cxmin, cymax - s)

    def peri_route(x0, y0, x1, y1):
        s0, s1 = peri_param(x0, y0), peri_param(x1, y1)
        d_ccw = (s1 - s0) % per
        d_cw = (s0 - s1) % per
        if min(d_ccw, d_cw) < 1e-12:
            return [(x0, y0), (x1, y1)]
        marks = [0.0, w, w + h, 2.0 * w + h]
        samples = []
        for m in marks:
            d = (m - s0) % per if d_ccw <= d_cw else (s0 - m) % per
            lim = d_ccw if d_ccw <= d_cw else d_cw
            if 1e-12 < d < lim - 1e-12:
                samples.append((d, m))
        samples.sort()
        out = [(x0, y0)] + [peri_point(m) for _d, m in samples] + [(x1, y1)]
        dedup = [out[0]]
        for p in out[1:]:
            if abs(p[0] - dedup[-1][0]) > 1e-7 or abs(p[1] - dedup[-1][1]) > 1e-7:
                dedup.append(p)
        return dedup

    projs = [cx * nx + cy * ny for cx, cy in ((xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax))]
    pmin, pmax = min(projs), max(projs)
    c_lo, c_hi = pmin + half_w, pmax - half_w
    if c_hi < c_lo - 1e-12:
        s_offs = [0.5 * (pmin + pmax)]
    else:
        n = max(1, int(math.floor((c_hi - c_lo) / spacing + 1e-12)) + 1)
        if n == 1:
            s_offs = [0.5 * (c_lo + c_hi)]
        else:
            s0 = 0.5 * (c_lo + c_hi) - 0.5 * spacing * (n - 1)
            s_offs = [s0 + i * spacing for i in range(n)]

    min_len = max(1e-6, float(min_len_factor) * eff_w)
    raw = []
    raw_off = []
    for s_off in s_offs:
        c = clip(nx * s_off, ny * s_off)
        if c is None:
            continue
        if math.hypot(c[2] - c[0], c[3] - c[1]) >= min_len:
            raw.append(c)
            raw_off.append(s_off)
    if not raw:
        raise ValueError("Raster path produced no strips; length too short for width/angle.")

    segs = [c if k % 2 == 0 else (c[2], c[3], c[0], c[1]) for k, c in enumerate(raw)]

    pts = []
    hops = []

    def add_pt(x, y):
        if not pts or math.hypot(pts[-1][0] - x, pts[-1][1] - y) > 1e-7:
            pts.append((float(x), float(y)))

    for i, (x0, y0, x1, y1) in enumerate(segs):
        add_pt(x0, y0)
        add_pt(x1, y1)
        if i < len(segs) - 1:
            xa, ya = snap(x1, y1)
            xb, yb = snap(segs[i + 1][0], segs[i + 1][1])
            route = peri_route(xa, ya, xb, yb)
            tlo = min(raw_off[i], raw_off[i + 1]) - half_w
            thi = max(raw_off[i], raw_off[i + 1]) + half_w
            for (ha, hb) in zip(route[:-1], route[1:]):
                if math.hypot(hb[0] - ha[0], hb[1] - ha[1]) > 1e-9:
                    hops.append((ha[0], ha[1], hb[0], hb[1], tlo, thi))
            for px, py in route:
                add_pt(px, py)
    dom = (xmin, xmax, ymin, ymax)
    if detail:
        return pts, dom, segs, hops, (cxmin, cxmax, cymin, cymax), (nx, ny)
    return pts, dom


def circular_seam_angles(num_layers, radius, layer_width, mode, seam_on):
    count = max(1, int(num_layers))
    if not seam_on:
        return [0.0] * count
    label = str(mode or "Aligned").strip().lower()
    rng = random.Random(1)
    step = float(layer_width) / max(float(radius), 1e-9)
    angles = []
    prev = 0.0
    for index in range(count):
        if label.startswith("rand"):
            ang = rng.random() * 2.0 * math.pi
        elif label.startswith("near"):
            if index == 0:
                ang = 0.0
            else:
                ang = prev + (rng.random() * 2.0 - 1.0) * step
        else:
            ang = 0.0
        angles.append(float(ang))
        prev = ang
    return angles


def _circular_cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _circular_in_triangle(p, a, b, c):
    c1 = _circular_cross(a, b, p)
    c2 = _circular_cross(b, c, p)
    c3 = _circular_cross(c, a, p)
    pos = c1 >= -1e-8 and c2 >= -1e-8 and c3 >= -1e-8
    neg = c1 <= 1e-8 and c2 <= 1e-8 and c3 <= 1e-8
    return pos or neg


def _circular_line_hit(p, q, radius):
    dx = q[0] - p[0]
    dy = q[1] - p[1]
    aa = dx * dx + dy * dy
    if aa < 1e-18:
        return None
    bb = 2.0 * (p[0] * dx + p[1] * dy)
    cc = p[0] * p[0] + p[1] * p[1] - radius * radius
    disc = bb * bb - 4.0 * aa * cc
    if disc < 0.0:
        return None
    root = math.sqrt(disc)
    hits = []
    for sign in (-1.0, 1.0):
        tt = (-bb + sign * root) / (2.0 * aa)
        if -1e-7 <= tt <= 1.0 + 1e-7:
            hits.append(tt)
    inside = [tt for tt in hits if 1e-5 < tt < 1.0 - 1e-5]
    if inside:
        return inside[0]
    if hits:
        return hits[0]
    return None


def _circular_hit_angle(p, q, radius):
    tt = _circular_line_hit(p, q, radius)
    if tt is None:
        return None
    x = p[0] + tt * (q[0] - p[0])
    y = p[1] + tt * (q[1] - p[1])
    return math.atan2(y, x), (x, y)


def circular_path_span(radius, layer_width, gap, theta, seam_on):
    full = 2.0 * math.pi
    radius = float(radius)
    half_w = float(layer_width) / 2.0
    inner_r = radius - half_w
    outer_r = radius + half_w
    if (not seam_on) or gap <= 1e-9 or inner_r <= 1e-9 or outer_r <= inner_r:
        return 0.0, full
    delta = min(float(gap) / outer_r, full * 0.75)
    if delta <= 1e-8:
        return 0.0, full
    theta = float(theta)
    apex = (inner_r * math.cos(theta), inner_r * math.sin(theta))
    left = (outer_r * math.cos(theta - 0.5 * delta), outer_r * math.sin(theta - 0.5 * delta))
    right = (outer_r * math.cos(theta + 0.5 * delta), outer_r * math.sin(theta + 0.5 * delta))
    mid = (radius * math.cos(theta), radius * math.sin(theta))
    if not _circular_in_triangle(mid, apex, left, right):
        return 0.0, full
    hit_l = _circular_hit_angle(apex, left, radius)
    hit_r = _circular_hit_angle(apex, right, radius)
    if hit_l is None or hit_r is None:
        return 0.0, full
    a = hit_l[0]
    b = hit_r[0]

    def _holds(start, end, target):
        span = (end - start) % full
        rel = (target - start) % full
        return rel <= span + 1e-7

    if _holds(a, b, theta):
        g0, g1 = a, b
    else:
        g0, g1 = b, a
    removed = (g1 - g0) % full
    if removed < 1e-6 or removed > full - 1e-6:
        return 0.0, full
    return g1 % full, full - removed


def make_circular_pipe_layer(diameter, layer_width, layer_height, z_center, seam_on, seam_angle, gap, fillet):
    radius = float(diameter) / 2.0
    half_w = float(layer_width) / 2.0
    half_h = float(layer_height) / 2.0
    inner_r = radius - half_w
    outer_r = radius + half_w
    if inner_r <= 1e-6:
        raise Exception("Path diameter must be larger than the layer width.")
    z0 = float(z_center) - half_h
    z1 = float(z_center) + half_h
    ring = [
        App.Vector(inner_r, 0.0, z0),
        App.Vector(outer_r, 0.0, z0),
        App.Vector(outer_r, 0.0, z1),
        App.Vector(inner_r, 0.0, z1),
        App.Vector(inner_r, 0.0, z0),
    ]
    solid = Part.Face(Part.makePolygon(ring)).revolve(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0)
    use_gap = float(gap) if seam_on else 0.0
    angle0, sweep = circular_path_span(radius, layer_width, use_gap, seam_angle, bool(seam_on) and use_gap > 1e-9)
    path_edge = _circular_path_edge(radius, z_center, angle0, sweep)
    if bool(seam_on) and use_gap > 1e-9:
        solid = _cut_circular_seam(
            solid, inner_r, outer_r, z0, z1, float(seam_angle), use_gap, float(fillet), float(layer_width), float(layer_height)
        )
    if solid is None or not solid.isValid() or float(solid.Volume) <= 0.0:
        raise Exception("Circular path solid is empty.")
    return solid, path_edge


def _profile_width_height(face):
    box = face.BoundBox
    width = max(float(box.XLength), float(box.YLength))
    height = float(box.ZLength)
    if width <= 1e-6 or height <= 1e-6:
        raise Exception("Profile sketch must lie in the XZ or YZ plane.")
    return width, height


def _shape_to_profile_face(shape):
    if shape is None or shape.isNull() or shape.Solids:
        return None
    best = None
    best_area = -1.0
    for face in shape.Faces:
        try:
            if abs(face.Area) > best_area:
                best = face
                best_area = abs(face.Area)
        except Exception:
            continue
    if best is not None:
        return best.copy()
    edges = list(shape.Edges)
    if not edges:
        return None
    groups = [edges]
    try:
        groups = Part.sortEdges(edges) or [edges]
    except Exception:
        groups = [edges]
    for group in groups:
        try:
            wire = Part.Wire(group)
            if wire.isClosed():
                return Part.Face(wire)
        except Exception:
            continue
    return None


def _load_sweep_profile_face(profile_file):
    profile_file = str(profile_file or "").strip()
    if not profile_file:
        raise Exception("Profile CAD file path is required when using CAD.")
    if not os.path.exists(profile_file):
        raise Exception(f"Profile CAD file not found: {profile_file}")
    ext = file_extension(profile_file)
    objects_before = set(App.ActiveDocument.Objects)
    if ext == "dxf":
        if importDXF is None:
            raise Exception("DXF import module not available in FreeCAD.")
        importDXF.insert(profile_file, App.ActiveDocument.Name)
    elif is_cad_geometry_file(profile_file):
        ImportGui.insert(profile_file, App.ActiveDocument.Name)
    else:
        raise Exception(
            f"Unsupported profile file format: .{ext}. Use DXF, STEP, IGES, or BREP."
        )
    App.ActiveDocument.recompute()
    imported = [obj for obj in App.ActiveDocument.Objects if obj not in objects_before]
    if not imported:
        raise Exception(f"Failed to import profile from '{profile_file}'.")
    best = None
    best_area = -1.0
    saw_solid = False
    loose_edges = []
    for obj in imported:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        if shape.Solids:
            saw_solid = True
            continue
        face = _shape_to_profile_face(shape)
        if face is not None and abs(face.Area) > best_area:
            best = face
            best_area = abs(face.Area)
        else:
            loose_edges.extend(shape.Edges)
    if best is None and loose_edges and not saw_solid:
        try:
            groups = Part.sortEdges(loose_edges)
        except Exception:
            groups = [loose_edges]
        for group in groups:
            try:
                wire = Part.Wire(group)
                if wire.isClosed():
                    face = Part.Face(wire)
                    if abs(face.Area) > best_area:
                        best = face
                        best_area = abs(face.Area)
            except Exception:
                continue
    for obj in imported:
        try:
            obj.ViewObject.Visibility = False
        except Exception:
            pass
    if best is None:
        if saw_solid:
            raise Exception("Profile CAD must be a closed planar sketch, not a solid body.")
        raise Exception("Profile must be a closed planar loop in the XZ or YZ plane.")
    try:
        normal = best.normalAt(0, 0)
        normal.normalize()
    except Exception as ex:
        raise Exception(f"Profile must be a closed planar loop in the XZ or YZ plane: {ex}")
    if abs(normal.z) > 0.5:
        raise Exception("Profile sketch must lie in the XZ or YZ plane.")
    _profile_width_height(best)
    return best


def _orient_profile_radial(face):
    placed = face.copy()
    center = placed.BoundBox.Center
    placed.translate(App.Vector(-center.x, -center.y, -center.z))
    normal = placed.normalAt(0, 0)
    normal.normalize()
    target = App.Vector(0, 1, 0)
    dot = max(-1.0, min(1.0, normal.dot(target)))
    if dot < 0.9999:
        axis = normal.cross(target)
        if axis.Length < 1e-8:
            axis = App.Vector(0, 0, 1)
            angle = 180.0
        else:
            axis.normalize()
            angle = math.degrees(math.acos(dot))
        placed.rotate(App.Vector(0, 0, 0), axis, angle)
    return placed


def make_circular_profile_layer(profile_face, diameter, z_center, seam_on, seam_angle, gap, fillet, layer_width, layer_height):
    radius = float(diameter) / 2.0
    if radius - float(layer_width) / 2.0 <= 1e-6:
        raise Exception("Path diameter must be larger than the layer width.")
    face = _orient_profile_radial(profile_face)
    center = face.BoundBox.Center
    face.translate(App.Vector(radius - center.x, -center.y, float(z_center) - center.z))
    box = face.BoundBox
    if box.XMin <= 1e-6:
        raise Exception("Path diameter must be larger than the layer width.")
    try:
        solid = face.revolve(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0)
    except Exception as ex:
        raise Exception(f"Circular path could not revolve the CAD profile: {ex}")
    if len(solid.Solids) == 1:
        solid = solid.Solids[0]
    use_gap = float(gap) if seam_on else 0.0
    angle0, sweep = circular_path_span(radius, layer_width, use_gap, seam_angle, bool(seam_on) and use_gap > 1e-9)
    path_edge = _circular_path_edge(radius, z_center, angle0, sweep)
    if bool(seam_on) and use_gap > 1e-9:
        solid = _cut_circular_seam(
            solid, box.XMin, box.XMax, box.ZMin, box.ZMax,
            float(seam_angle), use_gap, float(fillet), float(layer_width), float(layer_height),
        )
    if solid is None or not solid.isValid() or float(solid.Volume) <= 0.0:
        raise Exception("Circular path solid is empty.")
    return solid, path_edge


def _circular_path_edge(radius, z_center, angle0, sweep):
    z = float(z_center)
    if sweep >= 2.0 * math.pi - 1e-6:
        return Part.Circle(App.Vector(0, 0, z), App.Vector(0, 0, 1), float(radius)).toShape()

    def _pt(ang):
        return App.Vector(float(radius) * math.cos(ang), float(radius) * math.sin(ang), z)

    return Part.Arc(_pt(angle0), _pt(angle0 + 0.5 * sweep), _pt(angle0 + sweep)).toShape()


def _cut_circular_seam(solid, inner_r, outer_r, z0, z1, theta, gap, fillet, layer_width, layer_height):
    delta = min(float(gap) / float(outer_r), 2.0 * math.pi * 0.75)
    if delta <= 1e-8:
        return solid
    base = solid.copy()
    height = (z1 - z0) + 2.0
    chosen = None
    for inset in (0.0, 0.01, 0.05, max(0.1, 0.02 * layer_width)):
        apex_r = inner_r + inset
        reach = outer_r + max(0.5, 0.05 * layer_width)
        apex = App.Vector(apex_r * math.cos(theta), apex_r * math.sin(theta), z0 - 1.0)
        left = App.Vector(reach * math.cos(theta - 0.5 * delta), reach * math.sin(theta - 0.5 * delta), z0 - 1.0)
        right = App.Vector(reach * math.cos(theta + 0.5 * delta), reach * math.sin(theta + 0.5 * delta), z0 - 1.0)
        try:
            tool = Part.Face(Part.makePolygon([apex, left, right, apex])).extrude(App.Vector(0, 0, height))
            cut = base.cut(tool)
        except Exception:
            continue
        if cut is not None and cut.isValid() and float(cut.Volume) > 0.0 and len(cut.Solids) == 1:
            chosen = cut
            break
    if chosen is None:
        raise Exception("Circular seam cut failed.")
    rad = float(fillet)
    if rad <= 1e-9:
        return chosen
    cap = min(0.45 * layer_width, 0.45 * layer_height, 0.45 * max(gap, 1e-6))
    rad = min(rad, cap)
    if rad <= 1e-6:
        return chosen
    targets = [(inner_r * math.cos(theta), inner_r * math.sin(theta))]
    for sign in (-1.0, 1.0):
        hit = _circular_hit_angle(
            (inner_r * math.cos(theta), inner_r * math.sin(theta)),
            (outer_r * math.cos(theta + sign * 0.5 * delta), outer_r * math.sin(theta + sign * 0.5 * delta)),
            outer_r,
        )
        if hit is not None:
            targets.append(hit[1])
    tol = max(0.2, 0.05 * layer_width)
    edges = []
    for edge in chosen.Edges:
        if len(edge.Vertexes) < 2:
            continue
        p0 = edge.Vertexes[0].Point
        p1 = edge.Vertexes[-1].Point
        if abs(p0.x - p1.x) > 1e-5 or abs(p0.y - p1.y) > 1e-5 or abs(p0.z - p1.z) < 1e-5:
            continue
        for px, py in targets:
            if math.hypot(p0.x - px, p0.y - py) <= tol:
                edges.append(edge)
                break
    if not edges:
        App.Console.PrintWarning("Circular seam fillet found no corner edges; left sharp.\n")
        return chosen
    applied = rad
    filleted = None
    while applied > 0.05 and filleted is None and edges:
        try:
            trial = chosen.makeFillet(applied, edges)
            if trial is not None and trial.isValid() and len(trial.Solids) == 1 and float(trial.Volume) > 0.0:
                filleted = trial
                break
        except Exception:
            pass
        applied *= 0.5
    if filleted is None:
        App.Console.PrintWarning("Circular seam fillet failed; left sharp.\n")
        return chosen
    if applied < rad - 1e-9:
        App.Console.PrintWarning(
            "Circular seam fillet clamped from %.4g to %.4g.\n" % (rad, applied)
        )
    return filleted


def _clip_halfplane(poly, nx, ny, c, keep_ge):
    def val(p):
        d = nx * p[0] + ny * p[1] - c
        return d if keep_ge else -d
    out = []
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        va, vb = val(a), val(b)
        if va >= 0:
            out.append(a)
        if (va >= 0) != (vb >= 0):
            t = va / (va - vb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def raster_footprints(total_length, spacing, eff_w, num_lines, angle_deg):
    pts, dom, segs, hops, cdom, (nx, ny) = raster_qi_centerline(
        total_length, spacing, eff_w, num_lines, angle_deg, detail=True)
    xmin, xmax, ymin, ymax = dom
    cxmin, cxmax, cymin, cymax = cdom
    hw = eff_w / 2.0
    ext = 2.0 * eff_w
    polys = []

    def clip_to_domain(poly):
        out = poly
        out = _clip_halfplane(out, 1.0, 0.0, xmin, True)
        if not out:
            return out
        out = _clip_halfplane(out, -1.0, 0.0, -xmax, True)
        if not out:
            return out
        out = _clip_halfplane(out, 0.0, 1.0, ymin, True)
        if not out:
            return out
        out = _clip_halfplane(out, 0.0, -1.0, -ymax, True)
        return out

    for (x0, y0, x1, y1) in segs:
        L = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        px, py = -ty, tx
        ax, ay = x0 - tx * ext, y0 - ty * ext
        bx, by = x1 + tx * ext, y1 + ty * ext
        quad = [(ax + px * hw, ay + py * hw), (bx + px * hw, by + py * hw),
                (bx - px * hw, by - py * hw), (ax - px * hw, ay - py * hw)]
        quad = clip_to_domain(quad)
        if len(quad) >= 3:
            polys.append(quad)

    seen = set()
    for (xa, ya, xb, yb, tlo, thi) in hops:
        if abs(ya - yb) < 1e-7:
            if abs(ya - cymax) <= abs(ya - cymin):
                rect = [(xmin, ymax - eff_w), (xmax, ymax - eff_w), (xmax, ymax), (xmin, ymax)]
                edge = "top"
            else:
                rect = [(xmin, ymin), (xmax, ymin), (xmax, ymin + eff_w), (xmin, ymin + eff_w)]
                edge = "bottom"
        else:
            if abs(xa - cxmax) <= abs(xa - cxmin):
                rect = [(xmax - eff_w, ymin), (xmax, ymin), (xmax, ymax), (xmax - eff_w, ymax)]
                edge = "right"
            else:
                rect = [(xmin, ymin), (xmin + eff_w, ymin), (xmin + eff_w, ymax), (xmin, ymax)]
                edge = "left"
        key = (edge, round(tlo, 6), round(thi, 6))
        if key in seen:
            continue
        seen.add(key)
        band = _clip_halfplane(rect, nx, ny, tlo, True)
        if band:
            band = _clip_halfplane(band, nx, ny, thi, False)
        if band:
            band = clip_to_domain(band)
        if len(band) >= 3:
            polys.append(band)
    return polys, pts, dom


def raster_fillet_radius(fillet, eff_w, spacing):
    if fillet <= 0:
        return 0.0
    cap = 0.5 * eff_w
    gap = spacing - eff_w
    if gap > 1e-6:
        cap = min(cap, 0.45 * gap)
    return max(0.0, min(float(fillet), cap))


def _import_shape_in_global_coords(geo):
    shape = geo.Shape.copy()
    try:
        shape.transformGeometry(geo.Placement.toMatrix())
    except Exception:
        pass
    geo.Placement = App.Placement()
    return shape


def _largest_planar_face_normal(shape):
    best_area = 0.0
    best_normal = None
    for face in shape.Faces:
        try:
            surf = face.Surface
            type_id = str(getattr(surf, "TypeId", "") or "")
            type_name = type(surf).__name__
            if "Plane" not in type_id and type_name != "Plane":
                continue
            area = float(face.Area)
            if area <= best_area:
                continue
            umin, umax, vmin, vmax = face.ParameterRange
            normal = face.normalAt(0.5 * (umin + umax), 0.5 * (vmin + vmax))
            best_area = area
            best_normal = Base.Vector(normal)
        except Exception:
            continue
    if best_normal is None or best_normal.Length <= 1e-12:
        return None
    best_normal.normalize()
    return best_normal


def _rotate_shape_normal_to_z(shape, normal):
    z_axis = Base.Vector(0.0, 0.0, 1.0)
    n = Base.Vector(normal)
    if n.Length <= 1e-12:
        return shape
    n.normalize()
    if n.dot(z_axis) < 0.0:
        n = Base.Vector(-n.x, -n.y, -n.z)
    dot = max(-1.0, min(1.0, n.dot(z_axis)))
    if dot >= 0.999999:
        return shape
    bb = shape.BoundBox
    center = Base.Vector(bb.Center)
    if dot <= -0.999999:
        shape.rotate(center, Base.Vector(1.0, 0.0, 0.0), 180.0)
        return shape
    axis = n.cross(z_axis)
    if axis.Length <= 1e-12:
        return shape
    axis.normalize()
    angle = math.degrees(math.acos(dot))
    shape.rotate(center, axis, angle)
    return shape


def _translate_imported_to_origin(shape, tol=1e-6):
    bb = shape.BoundBox
    cx = 0.5 * (bb.XMin + bb.XMax)
    cy = 0.5 * (bb.YMin + bb.YMax)
    if abs(bb.XMin) <= tol and abs(bb.YMin) <= tol:
        tx = 0.0
        ty = 0.0
    elif abs(cx) <= tol and abs(cy) <= tol:
        tx = 0.0
        ty = 0.0
    else:
        tx = -bb.XMin
        ty = -bb.YMin
    tz = 0.0 if abs(bb.ZMin) <= tol else -bb.ZMin
    if abs(tx) > tol or abs(ty) > tol or abs(tz) > tol:
        shape.translate(Base.Vector(tx, ty, tz))
    return shape


def _normalize_imported_geometry(geo):
    """Sit imported CAD on XY: level largest flat face to +Z, then Zmin=0 and XY origin if needed."""
    if geo is None or not hasattr(geo, "Shape") or geo.Shape is None or geo.Shape.isNull():
        App.Console.PrintWarning(
            "Imported geometry has no usable Part shape for XY normalization.\n"
        )
        return geo

    shape = _import_shape_in_global_coords(geo)
    n_solids = len(getattr(shape, "Solids", []) or [])
    if n_solids == 0:
        App.Console.PrintWarning(
            "Imported geometry has no solid (open shell or surfaces only). Continuing.\n"
        )
    elif n_solids > 1:
        App.Console.PrintWarning(
            "Imported geometry has %d solids (multi-body). Continuing with compound.\n"
            % n_solids
        )

    normal = _largest_planar_face_normal(shape)
    if normal is None:
        App.Console.PrintWarning(
            "No clear flat face found for leveling. Translating only to sit on Z=0.\n"
        )
    else:
        z_dot = abs(normal.dot(Base.Vector(0.0, 0.0, 1.0)))
        if z_dot < 0.999999:
            shape = _rotate_shape_normal_to_z(shape, normal)
            App.Console.PrintMessage(
                "Imported geometry rotated so its largest flat face lies in XY.\n"
            )

    shape = _translate_imported_to_origin(shape)
    geo.Shape = shape
    geo.Placement = App.Placement()
    bb = shape.BoundBox
    App.Console.PrintMessage(
        "Imported geometry normalized: Zmin=0, bbox "
        "[(%.6g, %.6g, %.6g) -> (%.6g, %.6g, %.6g)].\n"
        % (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)
    )
    return geo


def gen_LDPMCSL_geometry(dimensions,geoType,geoName,cadFile):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - dimensions: List of dimensions for the geometry
    - geoType: Type of geometry to be created
    - geoName: Name of the geometry
    - cadFile: Path to the CAD or mesh file to be imported
    --------------------------------------------------------------------------
    ### Outputs ###
    - geo: Geometry object
    --------------------------------------------------------------------------
    """  


    # Check if dimensions are positive (ignore geometries we cannot check)
    if geoType not in ['Ellipsoid', 'Dogbone', 'Custom', 'Import CAD', 'Import CAD or Mesh', 'Sweep-3DP', 'L-shape']:
        if all(float(i.strip(" mm")) > 0 for i in dimensions):
            pass
        else:
            raise Exception("One or more geometry dimensions are less than or equal to zero. Please revise.")




    if geoType == "Box":

        # Create a box and name it
        geo           = App.ActiveDocument.addObject("Part::Box",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Width     = dimensions[1]
        geo.Length    = dimensions[2]


    if geoType == "Cylinder":

        # Create a cylinder and name it
        geo           = App.ActiveDocument.addObject("Part::Cylinder",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius    = dimensions[1]


    if geoType == "L-shape":

        def _lshape_dim(value):
            return float(str(value).strip().split()[0])

        if len(dimensions) < 3:
            raise Exception("L-shape requires Length in X, Length in Y, and Width.")

        length_x = _lshape_dim(dimensions[0])
        length_y = _lshape_dim(dimensions[1])
        if len(dimensions) >= 5:
            leg_width = _lshape_dim(dimensions[2])
            thickness_z = _lshape_dim(dimensions[3])
            inside_fillet = _lshape_dim(dimensions[4])
        else:
            leg_width = _lshape_dim(dimensions[2])
            thickness_z = leg_width
            inside_fillet = _lshape_dim(dimensions[3]) if len(dimensions) >= 4 else 0.0

        if length_x <= 0.0 or length_y <= 0.0 or leg_width <= 0.0 or thickness_z <= 0.0:
            raise Exception(
                "L-shape Length in X, Length in Y, Width, and Thickness (along Z) must be greater than zero."
            )
        if leg_width >= length_x or leg_width >= length_y:
            raise Exception("L-shape Width must be smaller than both Length in X and Length in Y.")
        if inside_fillet < 0.0:
            raise Exception("L-shape Inside Fillet cannot be negative.")

        # XY L profile: legs along +X and +Y with wall width; extrude in +Z by thickness_z.
        # Inside fillet rounds the re-entrant corner where the legs merge.
        max_fillet = min(length_x - leg_width, length_y - leg_width)
        fillet_r = min(inside_fillet, max_fillet) if inside_fillet > 0.0 else 0.0
        if inside_fillet > 0.0 and fillet_r < inside_fillet - 1e-9:
            App.Console.PrintWarning(
                "L-shape inside fillet clamped from %.4g to %.4g.\n" % (inside_fillet, fillet_r)
            )

        t = leg_width
        edges = [
            Part.makeLine(App.Vector(0.0, 0.0, 0.0), App.Vector(length_x, 0.0, 0.0)),
            Part.makeLine(App.Vector(length_x, 0.0, 0.0), App.Vector(length_x, t, 0.0)),
        ]
        if fillet_r > 1e-9:
            p_h = App.Vector(t + fillet_r, t, 0.0)
            p_v = App.Vector(t, t + fillet_r, 0.0)
            p_mid = App.Vector(
                t + fillet_r * (1.0 - math.sqrt(0.5)),
                t + fillet_r * (1.0 - math.sqrt(0.5)),
                0.0,
            )
            edges.append(Part.makeLine(App.Vector(length_x, t, 0.0), p_h))
            edges.append(Part.Arc(p_h, p_mid, p_v).toShape())
            edges.append(Part.makeLine(p_v, App.Vector(t, length_y, 0.0)))
        else:
            edges.append(Part.makeLine(App.Vector(length_x, t, 0.0), App.Vector(t, t, 0.0)))
            edges.append(Part.makeLine(App.Vector(t, t, 0.0), App.Vector(t, length_y, 0.0)))
        edges.extend(
            [
                Part.makeLine(App.Vector(t, length_y, 0.0), App.Vector(0.0, length_y, 0.0)),
                Part.makeLine(App.Vector(0.0, length_y, 0.0), App.Vector(0.0, 0.0, 0.0)),
            ]
        )

        wire = Part.Wire(edges)
        if not wire.isClosed():
            raise Exception("L-shape profile wire is not closed.")
        face = Part.Face(wire)
        if face.isNull() or face.Area <= 0.0:
            raise Exception("L-shape profile face could not be created.")
        solid = face.extrude(App.Vector(0.0, 0.0, thickness_z))
        if solid.isNull() or not solid.Solids:
            raise Exception("L-shape extrusion failed.")

        geo = App.ActiveDocument.addObject("Part::Feature", geoName)
        geo.Shape = solid.Solids[0] if len(solid.Solids) == 1 else solid
        geo.Label = geoName


    if geoType == "Truncated Cone":

        # Create a cone and name it
        geo           = App.ActiveDocument.addObject("Part::Cone",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius1   = dimensions[1]
        geo.Radius2   = dimensions[2]

    if geoType == "Cone":

        # Create a cone and name it
        geo           = App.ActiveDocument.addObject("Part::Cone",geoName)
        geo.Label     = geoName
        geo.Height    = dimensions[0]
        geo.Radius1   = dimensions[1]
        geo.Radius2   = dimensions[2]

    if geoType == "Sphere":

        # Create a sphere and name it
        geo           = App.ActiveDocument.addObject("Part::Sphere",geoName)
        geo.Label     = geoName
        geo.Radius    = dimensions[0]

    if geoType == "Ellipsoid":

        # Create an ellipsoid and name it
        geo           = App.ActiveDocument.addObject("Part::Ellipsoid",geoName)
        geo.Label     = geoName
        geo.Radius1   = dimensions[0]
        geo.Radius2   = dimensions[1]
        geo.Radius3   = dimensions[2]
        geo.Angle1    = dimensions[3]
        geo.Angle2    = dimensions[4]
        geo.Angle3    = dimensions[5]

    if geoType == "Arbitrary Prism":

        # Create a prism and name it
        geo           = App.ActiveDocument.addObject("Part::Prism",geoName)
        geo.Label     = geoName
        geo.Circumradius = dimensions[0]
        geo.Height    = dimensions[1]
        geo.Polygon   = int(dimensions[2])

    if geoType == "Notched Prism - Square":

        # Create a notched prism and name it
        geo           = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length    = dimensions[0]
        geo.Width     = dimensions[1]
        geo.Height    = dimensions[2]
        geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label     = geoName+'Box'

        # Create the notch
        geo           = App.ActiveDocument.addObject("Part::Box",geoName+"Notch")
        geo.Length    = dimensions[3]    # Notch Width
        geo.Width     = dimensions[1]    # Box width
        geo.Height    = dimensions[4]    # Notch Depth
        geo.Placement = App.Placement(App.Vector(0.00, 0.00, 0.00), App.Rotation(App.Vector(0.00, 0.00, 1.00), 0.00))
        geo.Label     = geoName + 'Notch'
        App.getDocument(App.ActiveDocument.Name).getObject(geoName+'Notch').Placement = App.Placement(App.Vector((float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2),0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))

        # Cut out the notch
        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Notch')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        geo = App.ActiveDocument.getObject(geoName)

    if geoType == "Notched Prism - Semi Circle":

        # Create a notched prism and name it
        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length     = dimensions[0]
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[2]
        geo.Placement  = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'Box'

        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"BoxNotch")
        geo.Length     = dimensions[3] # BoxNotch Width
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[4] # BoxNotch Depth
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'BoxNotch'

        geo            = App.ActiveDocument.addObject("Part::Cylinder",geoName+"CylinderNotch")
        geo.Radius     = float(dimensions[3].strip(" mm"))/2
        geo.Height     = float(dimensions[1].strip(" mm"))
        geo.Angle      = 360.00
        geo.FirstAngle = 0.00
        geo.SecondAngle= 0.00
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
        geo.Label      = geoName+'CylinderNotch'

        j = BOPTools.JoinFeatures.makeConnect(name=geoName+'Connect')
        j.Objects = [App.ActiveDocument.getObject(geoName+'BoxNotch'), App.ActiveDocument.getObject(geoName+'CylinderNotch')]
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Connect')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        geo = App.ActiveDocument.getObject(geoName)

    if geoType == "Notched Prism - Semi Ellipse":

        # Create a notched prism and name it
        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"Box")
        geo.Length     = dimensions[0]
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[2]
        geo.Placement  = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'Box'

        geo            = App.ActiveDocument.addObject("Part::Box",geoName+"BoxNotch")
        geo.Length     = dimensions[3] # BoxNotch Width
        geo.Width      = dimensions[1]
        geo.Height     = dimensions[4] # BoxNotch Depth
        geo.Placement  = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2-float(dimensions[3].strip(" mm"))/2,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
        geo.Label      = geoName+'BoxNotch'

        if float(dimensions[5].strip(" mm")) > float(dimensions[3].strip(" mm"))/2:
            geo        = App.ActiveDocument.addObject("Part::Ellipse",geoName+"Ellipse")
            geo.MajorRadius = float(dimensions[5].strip(" mm"))
            geo.MinorRadius = float(dimensions[3].strip(" mm"))/2
            geo.Angle1 = 0.00
            geo.Angle2 = 360.00
            geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
            geo.Label  = geoName+"Ellipse"
        else:
            geo        = App.ActiveDocument.addObject("Part::Ellipse",geoName+"Ellipse")
            geo.MajorRadius = float(dimensions[3].strip(" mm"))/2
            geo.MinorRadius = float(dimensions[5].strip(" mm"))
            geo.Angle1 = 0.00
            geo.Angle2 = 360.00
            geo.Placement = App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(1.00,0.00,0.00),-90.00))
            geo.Label  = geoName+"Ellipse"

        f              = App.ActiveDocument.addObject('Part::Extrusion',geoName+'EllipseNotch')
        f.Base         = App.ActiveDocument.getObject(geoName+'Ellipse')
        f.DirMode      = "Normal"
        f.DirLink      = None
        f.LengthFwd    = float(dimensions[1].strip(" mm"))
        f.LengthRev    = 0.000000000000000
        f.Solid        = True
        f.Reversed     = False
        f.Symmetric    = False
        f.TaperAngle   = 0.000000000000000
        f.TaperAngleRev= 0.000000000000000

        if float(dimensions[5].strip(" mm")) > float(dimensions[3].strip(" mm"))/2:
            App.ActiveDocument.getObject(geoName+'EllipseNotch').Placement = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(0.00,1.00,0.00),90.00))
        else:
            App.ActiveDocument.getObject(geoName+'EllipseNotch').Placement = App.Placement(App.Vector(float(dimensions[0].strip(" mm"))/2,0.00,float(dimensions[4].strip(" mm"))),App.Rotation(App.Vector(0.00,1.00,0.00),0.00))

        App.ActiveDocument.recompute()

        j = BOPTools.JoinFeatures.makeConnect(name=geoName+'Connect')
        j.Objects = [App.ActiveDocument.getObject(geoName+'BoxNotch'), App.ActiveDocument.getObject(geoName+'EllipseNotch')]
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        j = BOPTools.JoinFeatures.makeCutout(name=geoName)
        j.Base = App.ActiveDocument.getObject(geoName+'Box')
        j.Tool = App.ActiveDocument.getObject(geoName+'Connect')
        j.Proxy.execute(j)
        j.purgeTouched()
        for obj in j.ViewObject.Proxy.claimChildren():
            obj.ViewObject.hide()

        App.ActiveDocument.getObject(geoName+'Ellipse').Visibility = False
        App.ActiveDocument.getObject(geoName+'EllipseNotch').Visibility = False
        App.ActiveDocument.getObject(geoName+'BoxNotch').Visibility = False

        geo = App.ActiveDocument.getObject(geoName)





    if geoType == "Dogbone":

        # Define variables
        length = float(dimensions[0].strip(" mm"))  # Length of the part
        width = float(dimensions[1].strip(" mm"))  # Width of the part
        thickness = float(dimensions[2].strip(" mm"))  # Thickness of the part
        gauge_length = float(dimensions[3].strip(" mm"))  # Gauge length of the dogbone
        gauge_width = float(dimensions[4].strip(" mm"))  # Gauge width of the dogbone
        dogbone_type = dimensions[5]  # Type of the dogbone shape

        # Create a rectangular shape
        rectangle = App.ActiveDocument.addObject("Part::Box", geoName+"Rectangle")
        rectangle.Length = width
        rectangle.Width = thickness
        rectangle.Height = length

        # Create a dogbone shape
        if dogbone_type == 'Rounded':
            radius = (width-gauge_width)/2
            dogbone1 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone1")
            dogbone1.Radius = radius
            dogbone1.Height = thickness
            dogbone1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone2 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone2")
            dogbone2.Radius = radius
            dogbone2.Height = thickness
            dogbone2.Placement = App.Placement(App.Vector(width, 0, length/2-gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone3 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone3")
            dogbone3.Radius = radius
            dogbone3.Height = thickness
            dogbone3.Placement = App.Placement(App.Vector(0, 0, length/2+gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            dogbone4 = App.ActiveDocument.addObject("Part::Cylinder", geoName+"Dogbone4")
            dogbone4.Radius = radius
            dogbone4.Height = thickness
            dogbone4.Placement = App.Placement(App.Vector(width, 0, length/2+gauge_length/2),App.Rotation(App.Vector(1,0,0),-90.00))

            side1 = App.ActiveDocument.addObject("Part::Box", geoName+"side1")
            side1.Length = (width-gauge_width)/2
            side1.Width = thickness
            side1.Height = gauge_length
            side1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            side2 = App.ActiveDocument.addObject("Part::Box", geoName+"side2")
            side2.Length = (width-gauge_width)/2
            side2.Width = thickness
            side2.Height = gauge_length
            side2.Placement = App.Placement(App.Vector(width-(width-gauge_width)/2, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            DogboneInsert = App.ActiveDocument.addObject("Part::MultiFuse", geoName+"DogboneInsert")
            DogboneInsert.Shapes = [dogbone1, dogbone2, dogbone3, dogbone4, side1, side2]

        else:
            side1 = App.ActiveDocument.addObject("Part::Box", geoName+"side1")
            side1.Length = (width-gauge_width)/2
            side1.Width = thickness
            side1.Height = gauge_length
            side1.Placement = App.Placement(App.Vector(0, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            side2 = App.ActiveDocument.addObject("Part::Box", geoName+"side2")
            side2.Length = (width-gauge_width)/2
            side2.Width = thickness
            side2.Height = gauge_length
            side2.Placement = App.Placement(App.Vector(width-(width-gauge_width)/2, 0, length/2-gauge_length/2),App.Rotation(App.Vector(0,0,0),0.00))

            DogboneInsert = App.ActiveDocument.addObject("Part::MultiFuse", geoName+"DogboneInsert")
            DogboneInsert.Shapes = [side1, side2]

        # Subtract the dogbone from the rectangle
        part = App.ActiveDocument.addObject("Part::Cut",geoName)
        part.Base = rectangle
        part.Tool = DogboneInsert
        geo = part

    if geoType == "Custom":
        part_name = ""
        if dimensions:
            part_name = str(dimensions[0]).strip()
        if not part_name and cadFile:
            part_name = str(cadFile).strip()
        if not part_name:
            raise Exception(
                "Custom geometry requires a selected FreeCAD body. "
                "Use Select Object on the Geometry tab and choose a solid in the document."
            )
        doc = App.getDocument(App.ActiveDocument.Name)
        part = doc.getObject(part_name)
        if part is None:
            by_label = doc.getObjectsByLabel(part_name)
            part = by_label[0] if by_label else None
        if part is None:
            raise Exception(f"Custom geometry object '{part_name}' was not found in the active document.")
        if not hasattr(part, "Shape") or part.Shape is None or part.Shape.isNull():
            raise Exception(f"Custom geometry object '{part_name}' has no valid solid shape.")
        part.Label = geoName
        geo = part



    if geoType in ("Import CAD or Mesh", "Import CAD"):
        # Check if filetype is CAD (needing meshing) or mesh (already meshed)
        filename = os.path.basename(cadFile)
        filename, _imported_ext = os.path.splitext(filename)
        filename = re.sub("\.", "_", filename)
        filename = re.sub("/.", "_", filename)
        filename = re.sub("-", "_", filename)
        # If filename starts with a number, resub it with an underscore
        filename = re.sub("^\d", "_", filename)
        

        # If the file is a CAD file insert with ImportGui, else insert with Fem
        if is_cad_geometry_file(cadFile):
            ImportGui.insert(cadFile,App.ActiveDocument.Name)
            geo = App.getDocument(App.ActiveDocument.Name).getObject("Part__Feature")
            if geo is None:
                for obj in reversed(App.ActiveDocument.Objects):
                    if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull():
                        geo = obj
                        break
            if geo is None:
                raise Exception("Imported CAD file did not create a Part shape object.")
            geo.Label = geoName
            geo = _normalize_imported_geometry(geo)

        else:
            Fem.insert(cadFile,App.ActiveDocument.Name)
            geo = App.getDocument(App.ActiveDocument.Name).getObject(filename)
            geo.Label = geoName
            if hasattr(geo, "Shape") and geo.Shape is not None and not geo.Shape.isNull():
                geo = _normalize_imported_geometry(geo)
            else:
                App.Console.PrintWarning(
                    "Imported mesh has no Part solid faces; XY leveling skipped "
                    "(translate/rotate apply to CAD solids only).\n"
                )


    if geoType == "Sweep-3DP":

        profile_type = int(dimensions[0])
        path_type = int(dimensions[4])
        path_distance = dimensions[5]
        path_diameter = dimensions[6]
        path_side = dimensions[7]
        path_file = dimensions[8]
        path_sketch_name = dimensions[9] if len(dimensions) > 9 else ""
        num_layers = int(dimensions[10]) if len(dimensions) > 10 else 1
        raster_loops = int(dimensions[11]) if len(dimensions) > 11 and str(dimensions[11]).strip() else 1
        raster_spacing = float(str(dimensions[12]).strip().split()[0]) if len(dimensions) > 12 and str(dimensions[12]).strip() else 5.0
        raster_num_slices = int(dimensions[13]) if len(dimensions) > 13 and str(dimensions[13]).strip() else num_layers
        if path_type == 3:
            num_layers = max(1, min(8, raster_num_slices))
        raster_dirs = []
        for _i in range(num_layers if path_type == 3 else 0):
            _idx = 14 + _i
            if len(dimensions) > _idx and str(dimensions[_idx]).strip():
                raster_dirs.append(float(str(dimensions[_idx]).strip()))
            else:
                raster_dirs.append(0.0 if _i % 2 == 0 else 90.0)
        if path_type == 3 and len(dimensions) >= 24:
            _fillet_idx = 22
            _length_idx = 23
        else:
            _fillet_idx = 14 + num_layers
            _length_idx = 15 + num_layers
        raster_corner_fillet = float(str(dimensions[_fillet_idx]).strip().split()[0]) if len(dimensions) > _fillet_idx and str(dimensions[_fillet_idx]).strip() else 0.0
        raster_path_length = float(str(dimensions[_length_idx]).strip().split()[0]) if len(dimensions) > _length_idx and str(dimensions[_length_idx]).strip() else None

        profile_face_master = None
        if profile_type == 0:
            profile_width = float(str(dimensions[1]).strip().split()[0])
            profile_height = float(str(dimensions[2]).strip().split()[0])
        else:
            profile_face_master = _load_sweep_profile_face(dimensions[3])
            profile_width, profile_height = _profile_width_height(profile_face_master)

        circ_diameter = 0.0
        circ_seam = False
        circ_gap = 0.0
        circ_fillet = 0.0
        circ_angles = []
        if path_type == 6:
            circ_diameter = float(str(path_diameter).strip().split()[0]) if str(path_diameter).strip() else 0.0
            if circ_diameter <= profile_width:
                raise Exception("Path diameter must be larger than the layer width.")
            circ_seam = len(dimensions) > 11 and str(dimensions[11]).strip().lower() in ("yes", "y", "on", "true", "1")
            _circ_mode = str(dimensions[12]).strip() if len(dimensions) > 12 and str(dimensions[12]).strip() else "Aligned"
            circ_gap = float(str(dimensions[13]).strip().split()[0]) if len(dimensions) > 13 and str(dimensions[13]).strip() else 0.0
            circ_fillet = float(str(dimensions[14]).strip().split()[0]) if len(dimensions) > 14 and str(dimensions[14]).strip() else 0.0
            circ_angles = circular_seam_angles(num_layers, circ_diameter / 2.0, profile_width, _circ_mode, circ_seam)

        layer_shapes = []
        
        for layer_idx in range(num_layers):
            if profile_type == 0:
                _lh = float(dimensions[2].strip(" mm"))
            else:
                _lh = profile_height
            if path_type == 3:
                _overlap = min(0.05, max(1e-3, _lh * 0.01))
                _z_step = _lh - _overlap if num_layers > 1 else _lh
                z_offset = layer_idx * _z_step + (_lh / 2.0)
            else:
                z_offset = layer_idx * _lh
            
            current_geoName = geoName if num_layers == 1 else f"{geoName}_Layer{layer_idx}"
            
            if profile_type == 0:
                layer_width = float(dimensions[1].strip(" mm"))
                layer_height = float(dimensions[2].strip(" mm"))
                v1 = App.Vector(0, -layer_width/2, -layer_height/2)
                v2 = App.Vector(0,  layer_width/2, -layer_height/2)
                v3 = App.Vector(0,  layer_width/2,  layer_height/2)
                v4 = App.Vector(0, -layer_width/2,  layer_height/2)
                line1 = Part.LineSegment(v1, v2)
                line2 = Part.LineSegment(v2, v3)
                line3 = Part.LineSegment(v3, v4)
                line4 = Part.LineSegment(v4, v1)
                edge1 = line1.toShape()
                edge2 = line2.toShape()
                edge3 = line3.toShape()
                edge4 = line4.toShape()
                profile_wire = Part.Wire([edge1, edge2, edge3, edge4])
                if not profile_wire.isClosed():
                    raise Exception("Profile wire is not closed!")
                profile_face = Part.Face(profile_wire)
                profile_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + '_Profile')
                profile_obj.Shape = profile_face
                profile_obj.Label = current_geoName + '_Profile'
                profile_obj.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))
            else:
                layer_width = profile_width
                layer_height = profile_height
                profile_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + '_Profile')
                profile_obj.Shape = profile_face_master.copy()
                profile_obj.Label = current_geoName + '_Profile'
                App.ActiveDocument.recompute()

            if isinstance(profile_obj.Shape, Part.Face):
                profile_wire = profile_obj.Shape.Wires[0] if profile_obj.Shape.Wires else None
                profile_face = profile_obj.Shape
            elif isinstance(profile_obj.Shape, Part.Wire):
                profile_wire = profile_obj.Shape
                profile_face = Part.Face(profile_obj.Shape)
            elif hasattr(profile_obj.Shape, 'Wires') and profile_obj.Shape.Wires:
                profile_wire = profile_obj.Shape.Wires[0]
                profile_face = Part.Face(profile_obj.Shape.Wires[0])
            elif hasattr(profile_obj.Shape, 'Edges') and profile_obj.Shape.Edges:
                profile_wire = Part.Wire(profile_obj.Shape.Edges)
                profile_face = Part.Face(Part.Wire(profile_obj.Shape.Edges))
            else:
                raise Exception("Profile must be a valid wire or face.")

            if path_type == 0:
                if not path_distance or path_distance.strip() == "":
                    raise Exception("Path distance is required for straight line path.")
                distance = float(path_distance.strip(" mm"))
                if distance <= 0:
                    raise Exception("Path distance must be > 0.")
                start_point = App.Vector(0, 0, z_offset)
                end_point = App.Vector(distance, 0, z_offset)
                edge = Part.LineSegment(start_point, end_point).toShape()
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = edge
                path_obj.Label = current_geoName + "_Path"

            elif path_type == 1:
                if not path_side or path_side.strip() == "":
                    raise Exception("Square side is required for square path.")
                try:
                    side = float(path_side.strip(" mm"))
                except:
                    raise Exception(f"Invalid square side value: '{path_side}'.")
                if side <= 0:
                    raise Exception(f"Square side must be > 0 (got {side}mm).")
                p1 = App.Vector(0, 0, z_offset)
                p2 = App.Vector(side, 0, z_offset)
                p3 = App.Vector(side, side, z_offset)
                p4 = App.Vector(0, side, z_offset)
                e1 = Part.LineSegment(p1, p2).toShape()
                e2 = Part.LineSegment(p2, p3).toShape()
                e3 = Part.LineSegment(p3, p4).toShape()
                e4 = Part.LineSegment(p4, p1).toShape()
                square_wire = Part.Wire([e1, e2, e3, e4])
                if not square_wire.isClosed():
                    raise Exception("Square wire is not closed!")
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = square_wire
                path_obj.Label = current_geoName + "_Path"
                App.ActiveDocument.recompute()

            elif path_type == 2:
                if not path_sketch_name or path_sketch_name.strip() == "":
                    raise Exception("Path sketch is required when using FreeCAD Sketch option.")
                
                try:
                    sketch_obj = App.ActiveDocument.getObject(path_sketch_name)
                    if sketch_obj is None:
                        raise Exception(f"Sketch object '{path_sketch_name}' not found in document.")
                    
                    if not hasattr(sketch_obj, 'TypeId') or 'Sketch' not in sketch_obj.TypeId:
                        raise Exception(f"Object '{path_sketch_name}' is not a sketch object.")
                    
                    if not sketch_obj.Shape or sketch_obj.Shape.isNull():
                        raise Exception(f"Sketch '{path_sketch_name}' has no valid geometry.")
                    
                    edges = sketch_obj.Shape.Edges
                    if not edges:
                        raise Exception(f"Sketch '{path_sketch_name}' contains no edges.")
                    
                    try:
                        spine_wire = Part.Wire(edges)
                    except:
                        spine_wire = Part.Compound(edges)
                    
                    path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                    path_obj.Shape = spine_wire
                    path_obj.Label = current_geoName + "_Path"
                    path_obj.Placement = App.Placement(App.Vector(0, 0, z_offset), App.Rotation(App.Vector(0, 0, 1), 0))
                    App.ActiveDocument.recompute()
                    
                except Exception as e:
                    raise Exception(f"Failed to use sketch '{path_sketch_name}' as path: {str(e)}")
            elif path_type == 3:
                num_lines = max(1, int(raster_loops))
                spacing = max(1e-6, float(raster_spacing))

                if profile_type == 0:
                    eff_w = max(1e-6, float(dimensions[1].strip(" mm")))
                    eff_h = max(1e-6, float(dimensions[2].strip(" mm")))
                else:
                    try:
                        bb = profile_face.BoundBox
                        eff_w = max(1e-6, max(bb.XLength, bb.YLength))
                        eff_h = max(1e-6, bb.ZLength if bb.ZLength > 1e-9 else max(bb.XLength, bb.YLength))
                    except Exception:
                        eff_w = 1.0
                        eff_h = 1.0

                if spacing < eff_w:
                    spacing = eff_w
                if spacing < eff_w * 1.001:
                    App.Console.PrintWarning(
                        "Raster spacing is (almost) equal to the strip width: neighbouring "
                        "lines touch and can leave sliver voids at oblique angles. "
                        "Use spacing > width.\n"
                    )

                total_length = float(raster_path_length) if raster_path_length is not None else max(spacing * 4.0, spacing * (num_lines + 2))
                if total_length <= 2.0 * eff_w:
                    total_length = 2.0 * eff_w + 1.0

                half_w = eff_w / 2.0
                half_h = eff_h / 2.0
                angle_deg = raster_dirs[layer_idx] if layer_idx < len(raster_dirs) else 0.0

                r_eff = raster_fillet_radius(raster_corner_fillet, eff_w, spacing)
                if raster_corner_fillet > r_eff + 1e-9:
                    App.Console.PrintWarning(
                        f"Raster corner fillet clamped from {float(raster_corner_fillet):.4g} to {r_eff:.4g} "
                        f"(max 0.5*width and 0.45*gap between strips).\n"
                    )

                App.Console.PrintMessage(
                    f"Raster slice {layer_idx + 1}: angle={float(angle_deg):.4g} deg\n"
                )

                raster_quads, raster_pts2d, (xmin, xmax, ymin, ymax) = raster_footprints(
                    total_length, spacing, eff_w, num_lines, angle_deg
                )
                if not raster_quads:
                    raise Exception("Raster path produced no segments.")

                segments = [
                    Part.LineSegment(
                        App.Vector(a[0], a[1], z_offset), App.Vector(b[0], b[1], z_offset)
                    ).toShape()
                    for a, b in zip(raster_pts2d[:-1], raster_pts2d[1:])
                    if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9
                ]
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                try:
                    path_obj.Shape = Part.Wire(segments)
                except Exception:
                    path_obj.Shape = Part.Compound(segments)
                path_obj.Label = current_geoName + "_Path"
                App.ActiveDocument.recompute()
            elif path_type == 6:
                _seam_angle = circ_angles[layer_idx] if layer_idx < len(circ_angles) else 0.0
                if profile_type == 0:
                    circular_solid, path_edge = make_circular_pipe_layer(
                        circ_diameter,
                        layer_width,
                        layer_height,
                        z_offset,
                        circ_seam,
                        _seam_angle,
                        circ_gap,
                        circ_fillet,
                    )
                else:
                    circular_solid, path_edge = make_circular_profile_layer(
                        profile_face,
                        circ_diameter,
                        z_offset,
                        circ_seam,
                        _seam_angle,
                        circ_gap,
                        circ_fillet,
                        layer_width,
                        layer_height,
                    )
                path_obj = App.ActiveDocument.addObject("Part::Feature", current_geoName + "_Path")
                path_obj.Shape = path_edge
                path_obj.Label = current_geoName + "_Path"
                App.Console.PrintMessage(
                    "Circular layer %d: diameter=%.4g mm, seam=%s, angle=%.4g deg\n"
                    % (layer_idx + 1, circ_diameter, "on" if circ_seam else "off", math.degrees(_seam_angle))
                )
            else:
                raise Exception(f"Unsupported Sweep-3DP path type index: {path_type}")

            if path_type == 6:
                layer_geo = App.ActiveDocument.addObject("Part::Feature", current_geoName)
                layer_geo.Shape = circular_solid
                layer_geo.Label = current_geoName
                App.ActiveDocument.recompute()
                layer_shapes.append(layer_geo)
                try:
                    profile_obj.ViewObject.Visibility = False
                except Exception:
                    pass
                try:
                    path_obj.ViewObject.Visibility = False
                except Exception:
                    pass
                continue

            App.ActiveDocument.recompute()
            
            def find_connected_edges(edges):
                if not edges:
                    return []
                
                groups = []
                remaining = list(edges)
                
                while remaining:
                    current_group = [remaining.pop(0)]
                    changed = True
                    
                    while changed:
                        changed = False
                        for edge in remaining[:]:
                            for group_edge in current_group:
                                v1_start = edge.Vertexes[0].Point
                                v1_end = edge.Vertexes[-1].Point
                                v2_start = group_edge.Vertexes[0].Point
                                v2_end = group_edge.Vertexes[-1].Point
                                
                                if (v1_start.distanceToPoint(v2_start) < 1e-6 or
                                    v1_start.distanceToPoint(v2_end) < 1e-6 or
                                    v1_end.distanceToPoint(v2_start) < 1e-6 or
                                    v1_end.distanceToPoint(v2_end) < 1e-6):
                                    current_group.append(edge)
                                    remaining.remove(edge)
                                    changed = True
                                    break
                            if changed:
                                break
                    
                    groups.append(current_group)
                
                return groups
            
            spine_wires = []
            if path_type != 3:
                if isinstance(path_obj.Shape, Part.Wire):
                    spine_wires = [path_obj.Shape]
                elif hasattr(path_obj.Shape, 'Wires') and path_obj.Shape.Wires:
                    spine_wires = list(path_obj.Shape.Wires)
                elif hasattr(path_obj.Shape, 'Edges') and path_obj.Shape.Edges:
                    try:
                        spine_wires = [Part.Wire(path_obj.Shape.Edges)]
                    except Exception:
                        if len(path_obj.Shape.Edges) == 1:
                            spine_wires = [Part.Wire([path_obj.Shape.Edges[0]])]
                        else:
                            edge_groups = find_connected_edges(path_obj.Shape.Edges)
                            if edge_groups:
                                for group in edge_groups:
                                    try:
                                        spine_wires.append(Part.Wire(group))
                                    except Exception:
                                        pass
                            if not spine_wires:
                                raise Exception("Path edges are not connected.")
                else:
                    raise Exception("Path must contain a valid wire or edges.")

                if not spine_wires:
                    raise Exception("No valid path wires found.")

                spine_wire = spine_wires[0]

                if path_type == 2 and spine_wire and len(spine_wire.Edges) > 0:
                    segment_edges = []
                    for edge in spine_wire.Edges:
                        try:
                            pts = edge.discretize(Deflection=0.05)
                            for i in range(len(pts) - 1):
                                segment_edges.append(Part.LineSegment(pts[i], pts[i + 1]).toShape())
                        except Exception:
                            segment_edges.append(edge)
                    if segment_edges:
                        try:
                            spine_wire = Part.Wire(segment_edges)
                        except Exception:
                            pass
            else:
                spine_wires = [path_obj.Shape]
            
            import math as _math

            def _get_edge_tangent(edge):
                try:
                    t = edge.tangentAt(edge.FirstParameter)
                    if t.Length > 1e-6:
                        t.normalize()
                        return t
                except Exception:
                    pass
                try:
                    va = edge.Vertexes[0].Point
                    vb = edge.Vertexes[-1].Point
                    d = vb.sub(va)
                    if d.Length > 1e-6:
                        d.normalize()
                        return d
                except Exception:
                    pass
                return None

            def _make_profile_for_edge(base_face, edge_start, tangent):
                profile_center = base_face.BoundBox.Center
                f = base_face.copy()
                f.translate(edge_start.sub(App.Vector(profile_center.x, profile_center.y, profile_center.z)))
                if tangent is not None:
                    try:
                        fn = f.normalAt(0, 0)
                        fn.normalize()
                    except Exception:
                        fn = App.Vector(0, 0, 1)
                    dot = max(-1.0, min(1.0, fn.dot(tangent)))
                    if abs(dot) < 0.9999:
                        ax = fn.cross(tangent)
                        if ax.Length > 1e-6:
                            ax.normalize()
                            ang = _math.degrees(_math.acos(dot))
                            ctr = f.BoundBox.Center
                            f.rotate(App.Vector(ctr.x, ctr.y, ctr.z), ax, ang)
                return f

            def _sweep_single_edge(edge, face):
                seg_wire = Part.Wire([edge])
                wire = face.Wires[0] if face.Wires else Part.Wire(face.Edges)
                try:
                    s = seg_wire.makePipeShell([wire], True, False)
                    if s.isValid():
                        return s
                except Exception:
                    pass
                try:
                    s = seg_wire.makePipeShell([wire], False, False)
                    if s.isValid():
                        return Part.Solid(s)
                except Exception:
                    pass
                return None

            def _make_corner_fill(vertex_pt, t1, t2, half_w, half_h, z_up):
                try:
                    origin = App.Vector(
                        vertex_pt.x - half_w,
                        vertex_pt.y - half_w,
                        vertex_pt.z - half_h
                    )
                    box = Part.makeBox(half_w * 2, half_w * 2, half_h * 2, origin)
                    return box
                except Exception:
                    return None

            def _fuse_solids(solids, tol=1e-5):
                if not solids:
                    return None
                if len(solids) == 1:
                    return solids[0]
                try:
                    try:
                        fused = solids[0].multiFuse(solids[1:], tol)
                    except TypeError:
                        fused = solids[0].multiFuse(solids[1:])
                except Exception as ex:
                    App.Console.PrintWarning(f"multiFuse failed ({ex}); falling back to pairwise fuse\n")
                    fused = solids[0]
                    for k, s in enumerate(solids[1:], 1):
                        try:
                            try:
                                fused = fused.fuse(s, tol)
                            except TypeError:
                                fused = fused.fuse(s)
                        except Exception as ex2:
                            raise Exception(f"Fuse of solid #{k} failed: {ex2}")
                try:
                    fused = fused.removeSplitter()
                except Exception:
                    pass
                n_solids = len(fused.Solids)
                if n_solids != 1:
                    App.Console.PrintWarning(
                        f"Raster fuse produced {n_solids} disconnected solids (expected 1) - path is not continuous.\n"
                    )
                return fused

            def _make_raster_connector(x_inner, x_outer, y_lo, y_hi, sign_x, fillet, half_h, z_c):
                x_lo = min(x_inner, x_outer)
                x_hi = max(x_inner, x_outer)
                depth = x_hi - x_lo
                span = y_hi - y_lo
                if depth <= 1e-9 or span <= 1e-9:
                    return None
                r = min(float(fillet), 0.5 * depth - 1e-6, 0.5 * span - 1e-6) if fillet > 1e-12 else 0.0
                r = max(0.0, r)
                z0 = z_c - half_h
                try:
                    if r <= 1e-12:
                        box = Part.makeBox(depth, span, 2.0 * half_h, App.Vector(x_lo, y_lo, z0))
                        if abs(angle_deg) > 1e-12:
                            box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle_deg)
                        return box

                    if sign_x >= 0.0:
                        pts = [
                            App.Vector(x_lo, y_lo, z_c),
                            App.Vector(x_hi - r, y_lo, z_c),
                            App.Vector(x_hi, y_lo + r, z_c),
                            App.Vector(x_hi, y_hi - r, z_c),
                            App.Vector(x_hi - r, y_hi, z_c),
                            App.Vector(x_lo, y_hi, z_c),
                        ]
                        mid_b = App.Vector(x_hi - r * (1.0 - math.sin(math.pi / 4.0)), y_lo + r * (1.0 - math.cos(math.pi / 4.0)), z_c)
                        mid_t = App.Vector(x_hi - r * (1.0 - math.sin(math.pi / 4.0)), y_hi - r * (1.0 - math.cos(math.pi / 4.0)), z_c)
                        edges = [
                            Part.LineSegment(_rot_xy(pts[0]), _rot_xy(pts[1])).toShape(),
                            Part.Arc(_rot_xy(pts[1]), _rot_xy(mid_b), _rot_xy(pts[2])).toShape(),
                            Part.LineSegment(_rot_xy(pts[2]), _rot_xy(pts[3])).toShape(),
                            Part.Arc(_rot_xy(pts[3]), _rot_xy(mid_t), _rot_xy(pts[4])).toShape(),
                            Part.LineSegment(_rot_xy(pts[4]), _rot_xy(pts[5])).toShape(),
                            Part.LineSegment(_rot_xy(pts[5]), _rot_xy(pts[0])).toShape(),
                        ]
                    else:
                        pts = [
                            App.Vector(x_hi, y_lo, z_c),
                            App.Vector(x_lo + r, y_lo, z_c),
                            App.Vector(x_lo, y_lo + r, z_c),
                            App.Vector(x_lo, y_hi - r, z_c),
                            App.Vector(x_lo + r, y_hi, z_c),
                            App.Vector(x_hi, y_hi, z_c),
                        ]
                        mid_b = App.Vector(x_lo + r * (1.0 - math.sin(math.pi / 4.0)), y_lo + r * (1.0 - math.cos(math.pi / 4.0)), z_c)
                        mid_t = App.Vector(x_lo + r * (1.0 - math.sin(math.pi / 4.0)), y_hi - r * (1.0 - math.cos(math.pi / 4.0)), z_c)
                        edges = [
                            Part.LineSegment(_rot_xy(pts[0]), _rot_xy(pts[1])).toShape(),
                            Part.Arc(_rot_xy(pts[1]), _rot_xy(mid_b), _rot_xy(pts[2])).toShape(),
                            Part.LineSegment(_rot_xy(pts[2]), _rot_xy(pts[3])).toShape(),
                            Part.Arc(_rot_xy(pts[3]), _rot_xy(mid_t), _rot_xy(pts[4])).toShape(),
                            Part.LineSegment(_rot_xy(pts[4]), _rot_xy(pts[5])).toShape(),
                            Part.LineSegment(_rot_xy(pts[5]), _rot_xy(pts[0])).toShape(),
                        ]
                    face = Part.Face(Part.Wire(edges))
                    solid = face.extrude(App.Vector(0, 0, 2.0 * half_h))
                    solid.translate(App.Vector(0, 0, -half_h))
                    if solid.isValid() and float(solid.Volume) > 0.0:
                        return solid
                except Exception:
                    try:
                        box = Part.makeBox(depth, span, 2.0 * half_h, App.Vector(x_lo, y_lo, z0))
                        if abs(angle_deg) > 1e-12:
                            box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle_deg)
                        return box
                    except Exception:
                        return None
                return None

            def _make_qi_connector_box(axis, a0, a1, b0, b1, sign_outer, fillet, half_h, z_c):
                x_lo, x_hi = min(a0, a1), max(a0, a1)
                y_lo, y_hi = min(b0, b1), max(b0, b1)
                depth_x = x_hi - x_lo
                depth_y = y_hi - y_lo
                if depth_x <= 1e-9 or depth_y <= 1e-9:
                    return None
                r = 0.0
                if fillet > 1e-12:
                    r = min(float(fillet), 0.5 * depth_x - 1e-6, 0.5 * depth_y - 1e-6)
                    r = max(0.0, r)
                z0 = z_c - half_h
                try:
                    if r <= 1e-12:
                        box = Part.makeBox(depth_x, depth_y, 2.0 * half_h, App.Vector(x_lo, y_lo, z0))
                        if box.isValid() and float(box.Volume) > 0.0:
                            return box
                        return None

                    if axis == "x":
                        if sign_outer >= 0.0:
                            pts = [
                                App.Vector(x_lo, y_lo, z_c),
                                App.Vector(x_hi - r, y_lo, z_c),
                                App.Vector(x_hi, y_lo + r, z_c),
                                App.Vector(x_hi, y_hi - r, z_c),
                                App.Vector(x_hi - r, y_hi, z_c),
                                App.Vector(x_lo, y_hi, z_c),
                            ]
                            mid_b = App.Vector(
                                x_hi - r * (1.0 - math.sin(math.pi / 4.0)),
                                y_lo + r * (1.0 - math.cos(math.pi / 4.0)),
                                z_c,
                            )
                            mid_t = App.Vector(
                                x_hi - r * (1.0 - math.sin(math.pi / 4.0)),
                                y_hi - r * (1.0 - math.cos(math.pi / 4.0)),
                                z_c,
                            )
                        else:
                            pts = [
                                App.Vector(x_hi, y_lo, z_c),
                                App.Vector(x_lo + r, y_lo, z_c),
                                App.Vector(x_lo, y_lo + r, z_c),
                                App.Vector(x_lo, y_hi - r, z_c),
                                App.Vector(x_lo + r, y_hi, z_c),
                                App.Vector(x_hi, y_hi, z_c),
                            ]
                            mid_b = App.Vector(
                                x_lo + r * (1.0 - math.sin(math.pi / 4.0)),
                                y_lo + r * (1.0 - math.cos(math.pi / 4.0)),
                                z_c,
                            )
                            mid_t = App.Vector(
                                x_lo + r * (1.0 - math.sin(math.pi / 4.0)),
                                y_hi - r * (1.0 - math.cos(math.pi / 4.0)),
                                z_c,
                            )
                        edges = [
                            Part.LineSegment(pts[0], pts[1]).toShape(),
                            Part.Arc(pts[1], mid_b, pts[2]).toShape(),
                            Part.LineSegment(pts[2], pts[3]).toShape(),
                            Part.Arc(pts[3], mid_t, pts[4]).toShape(),
                            Part.LineSegment(pts[4], pts[5]).toShape(),
                            Part.LineSegment(pts[5], pts[0]).toShape(),
                        ]
                    else:
                        if sign_outer >= 0.0:
                            pts = [
                                App.Vector(x_lo, y_lo, z_c),
                                App.Vector(x_hi, y_lo, z_c),
                                App.Vector(x_hi, y_hi - r, z_c),
                                App.Vector(x_hi - r, y_hi, z_c),
                                App.Vector(x_lo + r, y_hi, z_c),
                                App.Vector(x_lo, y_hi - r, z_c),
                            ]
                            mid_r = App.Vector(
                                x_hi - r * (1.0 - math.cos(math.pi / 4.0)),
                                y_hi - r * (1.0 - math.sin(math.pi / 4.0)),
                                z_c,
                            )
                            mid_l = App.Vector(
                                x_lo + r * (1.0 - math.cos(math.pi / 4.0)),
                                y_hi - r * (1.0 - math.sin(math.pi / 4.0)),
                                z_c,
                            )
                            edges = [
                                Part.LineSegment(pts[0], pts[1]).toShape(),
                                Part.LineSegment(pts[1], pts[2]).toShape(),
                                Part.Arc(pts[2], mid_r, pts[3]).toShape(),
                                Part.LineSegment(pts[3], pts[4]).toShape(),
                                Part.Arc(pts[4], mid_l, pts[5]).toShape(),
                                Part.LineSegment(pts[5], pts[0]).toShape(),
                            ]
                        else:
                            pts = [
                                App.Vector(x_lo + r, y_lo, z_c),
                                App.Vector(x_hi - r, y_lo, z_c),
                                App.Vector(x_hi, y_lo + r, z_c),
                                App.Vector(x_hi, y_hi, z_c),
                                App.Vector(x_lo, y_hi, z_c),
                                App.Vector(x_lo, y_lo + r, z_c),
                            ]
                            mid_r = App.Vector(
                                x_hi - r * (1.0 - math.cos(math.pi / 4.0)),
                                y_lo + r * (1.0 - math.sin(math.pi / 4.0)),
                                z_c,
                            )
                            mid_l = App.Vector(
                                x_lo + r * (1.0 - math.cos(math.pi / 4.0)),
                                y_lo + r * (1.0 - math.sin(math.pi / 4.0)),
                                z_c,
                            )
                            edges = [
                                Part.LineSegment(pts[0], pts[1]).toShape(),
                                Part.Arc(pts[1], mid_r, pts[2]).toShape(),
                                Part.LineSegment(pts[2], pts[3]).toShape(),
                                Part.LineSegment(pts[3], pts[4]).toShape(),
                                Part.LineSegment(pts[4], pts[5]).toShape(),
                                Part.Arc(pts[5], mid_l, pts[0]).toShape(),
                            ]
                    face = Part.Face(Part.Wire(edges))
                    solid = face.extrude(App.Vector(0, 0, 2.0 * half_h))
                    solid.translate(App.Vector(0, 0, -half_h))
                    if solid.isValid() and float(solid.Volume) > 0.0:
                        return solid
                except Exception:
                    try:
                        box = Part.makeBox(depth_x, depth_y, 2.0 * half_h, App.Vector(x_lo, y_lo, z0))
                        if box.isValid() and float(box.Volume) > 0.0:
                            return box
                    except Exception:
                        return None
                return None

            all_segment_shapes = []

            for path_idx, active_spine_wire in enumerate(spine_wires):
                path_geoName = current_geoName if len(spine_wires) == 1 else f"{current_geoName}_Path{path_idx}"

                if path_type == 3:
                    z_base = z_offset - half_h
                    prisms = []
                    for quad in raster_quads:
                        poly = [App.Vector(x, y, z_base) for x, y in quad]
                        poly.append(App.Vector(poly[0]))
                        face = Part.Face(Part.makePolygon(poly))
                        prisms.append(face.extrude(App.Vector(0, 0, 2.0 * half_h)))

                    sweep_shape = _fuse_solids(prisms)
                    if sweep_shape is None or not sweep_shape.isValid():
                        raise Exception(f"Raster fuse failed for path {path_idx}.")

                    domain = Part.makeBox(
                        xmax - xmin, ymax - ymin, 2.0 * half_h + 2.0,
                        App.Vector(xmin, ymin, z_base - 1.0),
                    )
                    clipped = sweep_shape.common(domain)
                    if clipped is None or not clipped.isValid() or clipped.Volume <= 0:
                        raise Exception(f"Raster clip to domain failed for path {path_idx}.")
                    sweep_shape = clipped

                    if r_eff > 0:
                        def _vertical_edges(shp):
                            out = []
                            for _e in shp.Edges:
                                _p0 = _e.Vertexes[0].Point
                                _p1 = _e.Vertexes[-1].Point
                                if (abs(_p0.x - _p1.x) < 1e-7 and abs(_p0.y - _p1.y) < 1e-7
                                        and abs(_p0.z - _p1.z) > 1e-7):
                                    out.append(_e)
                            return out

                        def _try_fillet(shp, edges, rad):
                            try:
                                f = shp.makeFillet(rad, edges)
                                if f is not None and f.isValid() and len(f.Solids) == 1:
                                    return f
                            except Exception:
                                pass
                            return None

                        _vedges = _vertical_edges(sweep_shape)
                        _rad = r_eff
                        _filleted = None
                        _skipped = 0
                        while _rad > 0.05 and _filleted is None and _vedges:
                            _filleted = _try_fillet(sweep_shape, _vedges, _rad)
                            if _filleted is None:
                                _good = [e for e in _vedges if _try_fillet(sweep_shape, [e], _rad) is not None]
                                if _good and len(_good) < len(_vedges):
                                    _filleted = _try_fillet(sweep_shape, _good, _rad)
                                    _skipped = len(_vedges) - len(_good)
                            if _filleted is None:
                                _rad *= 0.5
                        if _filleted is not None:
                            sweep_shape = _filleted
                            if _rad < r_eff - 1e-9 or _skipped:
                                App.Console.PrintWarning(
                                    f"Raster slice {layer_idx + 1}: fillet r={_rad:.3g} applied"
                                    f"{f', {_skipped} sliver edge(s) left sharp' if _skipped else ''}.\n"
                                )
                        else:
                            App.Console.PrintWarning(
                                f"Raster slice {layer_idx + 1}: corner fillet failed, left sharp.\n"
                            )
                    if len(sweep_shape.Solids) != 1:
                        App.Console.PrintWarning(
                            f"Raster slice {layer_idx + 1} produced {len(sweep_shape.Solids)} solids (expected 1).\n"
                        )
                else:
                    edges = active_spine_wire.Edges
                    seg_solids = []

                    if profile_type == 0:
                        half_w = layer_width / 2.0
                        half_h = layer_height / 2.0
                        z_up = App.Vector(0, 0, 1)
                    else:
                        bb = profile_face.BoundBox
                        half_w = max(bb.XLength, bb.YLength) / 2.0
                        half_h = bb.ZLength / 2.0
                        z_up = App.Vector(0, 0, 1)

                    for seg_edge in edges:
                        seg_tangent = _get_edge_tangent(seg_edge)
                        seg_start = seg_edge.Vertexes[0].Point
                        placed_face = _make_profile_for_edge(profile_face, seg_start, seg_tangent)
                        seg_solid = _sweep_single_edge(seg_edge, placed_face)
                        if seg_solid is not None:
                            seg_solids.append(seg_solid)

                    ordered_edges = list(edges)
                    for i in range(len(ordered_edges) - 1):
                        e1 = ordered_edges[i]
                        e2 = ordered_edges[i + 1]
                        v1_end = e1.Vertexes[-1].Point
                        v2_start = e2.Vertexes[0].Point
                        if v1_end.distanceToPoint(v2_start) < 1e-4:
                            corner_pt = v1_end
                        else:
                            corner_pt = None

                        if corner_pt is not None:
                            t1 = _get_edge_tangent(e1)
                            t2 = _get_edge_tangent(e2)
                            if t1 is not None and t2 is not None:
                                fill = _make_corner_fill(corner_pt, t1, t2, half_w, half_h, z_up)
                                if fill is not None:
                                    seg_solids.append(fill)

                    if active_spine_wire.isClosed() and len(ordered_edges) > 1:
                        e_last = ordered_edges[-1]
                        e_first = ordered_edges[0]
                        t1 = _get_edge_tangent(e_last)
                        t2 = _get_edge_tangent(e_first)
                        corner_pt = e_last.Vertexes[-1].Point
                        if t1 is not None and t2 is not None:
                            fill = _make_corner_fill(corner_pt, t1, t2, half_w, half_h, z_up)
                            if fill is not None:
                                seg_solids.append(fill)

                    if not seg_solids:
                        raise Exception(f"Segment-by-segment {path_idx}.")

                    if len(seg_solids) == 1:
                        sweep_shape = seg_solids[0]
                    else:
                        combined = seg_solids[0]
                        for s in seg_solids[1:]:
                            try:
                                combined = combined.fuse(s)
                            except Exception:
                                pass
                        try:
                            combined = combined.removeSplitter()
                        except Exception:
                            pass
                        sweep_shape = combined

                layer_geo = App.ActiveDocument.addObject("Part::Feature", path_geoName)
                layer_geo.Shape = sweep_shape
                layer_geo.Label = path_geoName
                App.ActiveDocument.recompute()
                layer_shapes.append(layer_geo)
            
            try:
                profile_obj.ViewObject.Visibility = False
            except Exception:
                pass
            try:
                path_obj.ViewObject.Visibility = False
            except Exception:
                pass

        # Fuse all layer shapes into a single solid
        shapes_to_fuse = all_segment_shapes if all_segment_shapes else [ls.Shape for ls in layer_shapes]
        if not shapes_to_fuse:
            raise Exception(
                "Sweep-3DP generated no geometry "
            )
        if len(shapes_to_fuse) == 1:
            merged_shape = shapes_to_fuse[0]
        else:
            merged_shape = shapes_to_fuse[0]
            for k, s in enumerate(shapes_to_fuse[1:], 1):
                try:
                    merged_shape = merged_shape.fuse(s)
                except Exception as ex:
                    raise Exception(f"Layer fuse #{k} failed: {ex}")
        for _fn in ('removeSplitter', 'refine'):
            try:
                merged_shape = getattr(merged_shape, _fn)()
            except Exception:
                pass
        geo = App.ActiveDocument.addObject("Part::Feature", geoName)
        geo.Shape = merged_shape
        geo.Label = geoName
        App.ActiveDocument.recompute()
        for layer_geo in layer_shapes:
            try:
                App.ActiveDocument.removeObject(layer_geo.Name)
            except Exception:
                pass
        



    App.ActiveDocument.recompute()
    
    try:
        return geo
    except NameError:
        raise Exception(
            f"Geometry type '{geoType}' did not create a geometry object."
        )
