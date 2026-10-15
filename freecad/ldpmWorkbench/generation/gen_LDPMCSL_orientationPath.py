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
## This file contains the function to generate a fiber and outputs the
## location of the fiber as well other fiber properties. 
##
## ===========================================================================

import json
import math
from pathlib import Path

import numpy as np


def _validate_segments(segments):
    if len(segments) == 0:
        return segments
    
    for seg in segments:
        tangent = seg['tangent']
        if not np.all(np.isfinite(tangent)):
            seg['tangent'] = np.array([1.0, 0.0, 0.0])
        else:
            norm = np.linalg.norm(tangent)
            if norm > 1e-12:
                seg['tangent'] = tangent / norm
            else:
                seg['tangent'] = np.array([1.0, 0.0, 0.0])
        
        for key in ['center', 'start', 'end']:
            if not np.all(np.isfinite(seg[key])):
                print(f"Invalid {key} in segment {seg['id']}, using origin")
                seg[key] = np.array([0.0, 0.0, 0.0])
        
        if not np.isfinite(seg['length']) or seg['length'] <= 0:
            seg['length'] = np.linalg.norm(seg['end'] - seg['start'])
    
    return segments


def read_orientationPath_sweep3dp(orientationPathType, orientationPathSketchName, geometryPathParams, segmentLength):
    
    try:
        if orientationPathType == 0:
            segments = _discretize_line_path(geometryPathParams, segmentLength)
        elif orientationPathType == 1:
            segments = _discretize_square_path(geometryPathParams, segmentLength)
        elif orientationPathType == 2:
            segments = _discretize_sketch_path(orientationPathSketchName, segmentLength)
        elif orientationPathType == 3:
            segments = _discretize_raster_path(geometryPathParams, segmentLength)
        elif orientationPathType == 6:
            segments = _discretize_circular_path(geometryPathParams, segmentLength)
        else:
            segments = np.array([])
        
        if len(segments) > 0:
            segments = _validate_segments(segments)
            if orientationPathType in (3, 6):
                half_w = 0.5 * float(geometryPathParams["eff_w"])
                half_h = 0.5 * float(geometryPathParams["eff_h"])
                segments = _compute_raster_segment_bboxes(segments, half_w, half_h)
            else:
                segments = _compute_segment_bboxes(segments)
        try:
            import tempfile
            import os
            log_file = os.path.join(tempfile.gettempdir(), "orientation_segments_debug.txt")
            with open(log_file, 'w') as f:
                f.write(f"Orientation Path Segments (Type {orientationPathType})\n")
                f.write(f"Total segments: {len(segments)}\n\n")
                for seg in segments:
                    f.write(f"Segment {seg['id']}:\n")
                    f.write(f"  Center: {seg['center']}\n")
                    f.write(f"  Tangent: {seg['tangent']}\n")
                    f.write(f"  Start: {seg['start']}\n")
                    f.write(f"  End: {seg['end']}\n")
                    f.write(f"  Length: {seg['length']}\n")
                    f.write(f"  Bbox Min: {seg['bbox_min']}\n")
                    f.write(f"  Bbox Max: {seg['bbox_max']}\n\n")
            print(f"Segment debug info written to: {log_file}")
        except Exception as e:
            print(f"Could not write debug file: {e}")
        
        return segments
    
    except Exception as e:
        print(f"ERROR in read_orientationPath_sweep3dp: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])


def _compute_segment_bboxes(segments):
    if len(segments) == 0:
        return segments
    
    all_starts = np.array([seg['start'] for seg in segments])
    all_ends = np.array([seg['end'] for seg in segments])
    all_centers = np.array([seg['center'] for seg in segments])
    
    all_points = np.vstack((all_starts, all_ends, all_centers))
    
    path_min = np.min(all_points, axis=0)
    path_max = np.max(all_points, axis=0)
    
    path_extent = path_max - path_min
    path_extent_nonzero = path_extent[path_extent > 0]
    
    if len(path_extent_nonzero) > 0:
        max_extent = np.max(path_extent_nonzero)
    else:
        max_extent = 10.0
    
    margin = max_extent * 0.5
    
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        
        bbox_min = np.minimum(start, end) - margin
        bbox_max = np.maximum(start, end) + margin
        
        if i > 0:
            prev_seg = segments[i-1]
            bbox_min = np.minimum(bbox_min, prev_seg['center'] - margin * 0.5)
            bbox_max = np.maximum(bbox_max, prev_seg['center'] + margin * 0.5)
        
        if i < len(segments) - 1:
            next_seg = segments[i+1]
            bbox_min = np.minimum(bbox_min, next_seg['center'] - margin * 0.5)
            bbox_max = np.maximum(bbox_max, next_seg['center'] + margin * 0.5)
        
        seg['bbox_min'] = bbox_min
        seg['bbox_max'] = bbox_max
    
    return segments


def _raster_axes(start, end):
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    d = end - start
    ln = float(np.linalg.norm(d))
    if ln < 1e-12:
        t = np.array([1.0, 0.0, 0.0])
        ln = 0.0
    else:
        t = d / ln
    n = np.array([-t[1], t[0], 0.0])
    nn = float(np.linalg.norm(n))
    if nn < 1e-12:
        n = np.array([0.0, 1.0, 0.0])
    else:
        n = n / nn
    return start, t, n, ln


def _point_in_oriented_box(p, seg):
    start, t, n, ln = _raster_axes(seg["start"], seg["end"])
    half_w = float(seg["half_w"])
    half_h = float(seg["half_h"])
    d = np.asarray(p, dtype=float) - start
    u = float(np.dot(d, t))
    v = float(np.dot(d, n))
    w = float(d[2])
    return (
        -1e-6 <= u <= ln + 1e-6
        and abs(v) <= half_w + 1e-8
        and abs(w) <= half_h + 1e-8
    )


def fiber_inside_layer_boxes(p1, p2, layer_segs):
    if not layer_segs:
        return False
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    span = float(np.linalg.norm(p2 - p1))
    step = max(0.5 * float(layer_segs[0]["half_w"]), 1e-3)
    n = max(2, int(math.ceil(span / step)) + 1)
    for i in range(n):
        a = i / float(n - 1)
        p = (1.0 - a) * p1 + a * p2
        if not any(_point_in_oriented_box(p, seg) for seg in layer_segs):
            return False
    return True


def sample_point_in_oriented_box(seg):
    start, t, n, ln = _raster_axes(seg["start"], seg["end"])
    u = float(np.random.rand()) * ln
    v = (float(np.random.rand()) * 2.0 - 1.0) * float(seg["half_w"])
    w = (float(np.random.rand()) * 2.0 - 1.0) * float(seg["half_h"])
    return start + t * u + n * v + np.array([0.0, 0.0, w])


def _compute_raster_segment_bboxes(segments, half_w, half_h):
    if len(segments) == 0:
        return segments
    margin_xy = max(1e-9, float(half_w))
    margin_z = max(1e-9, float(half_h))
    up = np.array([0.0, 0.0, 1.0])
    for seg in segments:
        start, t, n, ln = _raster_axes(seg["start"], seg["end"])
        corners = []
        for s in (0.0, ln):
            c = start + t * s
            for sn in (-margin_xy, margin_xy):
                for sz in (-margin_z, margin_z):
                    corners.append(c + n * sn + up * sz)
        corners = np.vstack(corners)
        seg["bbox_min"] = np.min(corners, axis=0)
        seg["bbox_max"] = np.max(corners, axis=0)
        seg["half_w"] = margin_xy
        seg["half_h"] = margin_z
        seg["axis_t"] = t
        seg["axis_n"] = n
    return segments


def _distance_point_to_segment(p, start, end, center):
    p = np.asarray(p, dtype=float)
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    center = np.asarray(center, dtype=float)
    
    ab = end - start
    ap = p - start
    ab_sq = np.dot(ab, ab)
    
    if ab_sq <= 1e-12:
        dist_chord = np.linalg.norm(ap)
    else:
        t = np.dot(ap, ab) / ab_sq
        t = max(0.0, min(1.0, t))
        q = start + t * ab
        dist_chord = np.linalg.norm(p - q)
    
    dist_center = np.linalg.norm(p - center)
    
    chord_midpoint = (start + end) / 2.0
    curvature_offset = np.linalg.norm(center - chord_midpoint)
    
    if curvature_offset > 0.01 * np.linalg.norm(ab):
        return min(dist_chord, dist_center)
    else:
        return dist_chord


def _point_in_segment_bbox(p, seg):
    if "half_w" in seg and "half_h" in seg:
        return _point_in_oriented_box(p, seg)
    if "bbox_min" not in seg or "bbox_max" not in seg:
        return True
    bmin = np.asarray(seg["bbox_min"], dtype=float)
    bmax = np.asarray(seg["bbox_max"], dtype=float)
    return bool(
        bmin[0] <= p[0] <= bmax[0]
        and bmin[1] <= p[1] <= bmax[1]
        and bmin[2] <= p[2] <= bmax[2]
    )


def _point_in_segment_z(p, seg):
    if "bbox_min" not in seg or "bbox_max" not in seg:
        return True
    bmin = np.asarray(seg["bbox_min"], dtype=float)
    bmax = np.asarray(seg["bbox_max"], dtype=float)
    return bool(bmin[2] <= p[2] <= bmax[2])


def is_raster_path_segments(pathSegments):
    if pathSegments is None or len(pathSegments) == 0:
        return False
    return any("half_w" in seg for seg in pathSegments)


def group_raster_segments_by_layer(pathSegments):
    layers = {}
    for seg in pathSegments:
        z_key = round(float(np.asarray(seg["center"], dtype=float)[2]), 6)
        layers.setdefault(z_key, []).append(seg)
    return layers


def max_ray_length_in_bbox(p, direction, bmin, bmax):
    p = np.asarray(p, dtype=float)
    d = np.asarray(direction, dtype=float)
    bmin = np.asarray(bmin, dtype=float)
    bmax = np.asarray(bmax, dtype=float)
    if not (
        bmin[0] <= p[0] <= bmax[0]
        and bmin[1] <= p[1] <= bmax[1]
        and bmin[2] <= p[2] <= bmax[2]
    ):
        return 0.0
    t_exit = np.inf
    for i in range(3):
        if d[i] > 1e-14:
            t_exit = min(t_exit, (bmax[i] - p[i]) / d[i])
        elif d[i] < -1e-14:
            t_exit = min(t_exit, (bmin[i] - p[i]) / d[i])
        elif p[i] < bmin[i] - 1e-12 or p[i] > bmax[i] + 1e-12:
            return 0.0
    if not np.isfinite(t_exit) or t_exit <= 0.0:
        return 0.0
    return float(t_exit)


def sample_point_in_bbox(bmin, bmax):
    bmin = np.asarray(bmin, dtype=float)
    bmax = np.asarray(bmax, dtype=float)
    u = np.random.rand(3)
    return bmin + u * (bmax - bmin)


def get_zone_from_point(p1Fiber, pathSegments):
    if pathSegments is None or len(pathSegments) == 0:
        return None, None
    
    p1Fiber = np.asarray(p1Fiber, dtype=float)
    n = len(pathSegments)

    use_raster_bbox = is_raster_path_segments(pathSegments)
    if use_raster_bbox:
        in_bbox = [i for i in range(n) if _point_in_segment_bbox(p1Fiber, pathSegments[i])]
        if not in_bbox:
            return None, None
        pool = in_bbox
        distances = np.full(n, np.inf, dtype=float)
        for i in pool:
            seg = pathSegments[i]
            distances[i] = _distance_point_to_segment(
                p1Fiber, seg["start"], seg["end"], seg["center"]
            )
    else:
        distances = np.array([
            _distance_point_to_segment(p1Fiber, seg['start'], seg['end'], seg['center'])
            for seg in pathSegments
        ])
    
    if not np.any(np.isfinite(distances)):
        return pathSegments[0]['id'], pathSegments[0]['tangent']
    
    nearest_idx = int(np.argmin(distances))
    
    min_dist = distances[nearest_idx]
    tolerance = min_dist * 0.1 + 1e-6
    
    candidates = np.where(distances <= min_dist + tolerance)[0]
    
    if len(candidates) > 1:
        center_distances = np.array([
            np.linalg.norm(p1Fiber - pathSegments[idx]['center'])
            for idx in candidates
        ])
        best_candidate = candidates[np.argmin(center_distances)]
        return pathSegments[best_candidate]['id'], pathSegments[best_candidate]['tangent']
    
    return pathSegments[nearest_idx]['id'], pathSegments[nearest_idx]['tangent']


def _segment_count_from_length(total_len, segment_length):
    sl = max(1e-9, float(segment_length))
    return max(1, int(math.ceil(max(0.0, float(total_len)) / sl - 1e-12)))


def _discretize_line_path(params, segment_length):
    distance = float(params['distance'])
    numSegments = _segment_count_from_length(distance, segment_length)
    segments = []
    
    for i in range(numSegments):
        t0 = i / numSegments
        t1 = (i + 1) / numSegments
        
        p0 = np.array([t0 * distance, 0, 0])
        p1 = np.array([t1 * distance, 0, 0])
        
        tangent = np.array([1, 0, 0])
        length = distance / numSegments
        center = (p0 + p1) / 2
        
        segments.append({
            'id': i,
            'start': p0,
            'end': p1,
            'tangent': tangent,
            'length': length,
            'center': center
        })
    
    return np.array(segments)


def _discretize_raster_path(params, segment_length):
    from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry import raster_qi_centerline

    total_length = float(params["total_length"])
    spacing = max(1e-6, float(params["spacing"]))
    eff_w = max(1e-6, float(params["eff_w"]))
    eff_h = max(1e-6, float(params["eff_h"]))
    num_lines = max(1, int(params["num_lines"]))
    num_layers = max(1, int(params["num_layers"]))
    dirs = list(params.get("dirs", []))
    if spacing < eff_w:
        spacing = eff_w
    if total_length <= 2.0 * eff_w:
        total_length = 2.0 * eff_w + 1.0

    step = max(1e-9, float(segment_length))
    segments = []
    seg_id = 0

    for layer_idx in range(num_layers):
        overlap = min(0.05, max(1e-3, eff_h * 0.01))
        z_step = eff_h - overlap if num_layers > 1 else eff_h
        z_offset = layer_idx * z_step + (eff_h / 2.0)
        if layer_idx < len(dirs):
            angle_deg = float(dirs[layer_idx])
        else:
            angle_deg = 0.0 if layer_idx % 2 == 0 else 90.0

        pts, _dom, _segs, _hops, _cdom, _nn = raster_qi_centerline(
            total_length, spacing, eff_w, num_lines, angle_deg, detail=True)

        edges = []
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            ln = math.hypot(x1 - x0, y1 - y0)
            if ln > 1e-9:
                edges.append((x0, y0, x1, y1, ln))
        if not edges:
            continue

        for x0, y0, x1, y1, ln in edges:
            n = _segment_count_from_length(ln, step)
            for k in range(n):
                t0 = k / float(n)
                t1 = (k + 1) / float(n)
                sx = x0 + t0 * (x1 - x0)
                sy = y0 + t0 * (y1 - y0)
                ex = x0 + t1 * (x1 - x0)
                ey = y0 + t1 * (y1 - y0)
                p0 = np.array([sx, sy, z_offset], dtype=float)
                p1 = np.array([ex, ey, z_offset], dtype=float)
                d = p1 - p0
                length = float(np.linalg.norm(d))
                if length < 1e-12:
                    continue
                tangent = d / length
                center = 0.5 * (p0 + p1)
                segments.append({
                    "id": seg_id,
                    "start": p0,
                    "end": p1,
                    "tangent": tangent,
                    "length": length,
                    "center": center,
                })
                seg_id += 1

    return np.array(segments)


def _discretize_circular_path(params, segment_length):
    from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry import circular_path_span, circular_seam_angles

    diameter = float(params["diameter"])
    radius = diameter / 2.0
    eff_w = max(1e-6, float(params["eff_w"]))
    eff_h = max(1e-6, float(params["eff_h"]))
    num_layers = max(1, int(params["num_layers"]))
    seam_on = bool(params.get("seam_on", False))
    gap = float(params.get("seam_distance", 0.0) or 0.0)
    angles = circular_seam_angles(
        num_layers, radius, eff_w, params.get("seam_mode", "Aligned"), seam_on
    )
    segments = []
    seg_id = 0
    for layer_idx in range(num_layers):
        z_offset = layer_idx * eff_h
        theta = angles[layer_idx] if layer_idx < len(angles) else 0.0
        angle0, sweep = circular_path_span(radius, eff_w, gap, theta, seam_on)
        length = radius * sweep
        if length <= 1e-9:
            continue
        count = _segment_count_from_length(length, segment_length)
        for k in range(count):
            a0 = angle0 + sweep * (k / float(count))
            a1 = angle0 + sweep * ((k + 1) / float(count))
            p0 = np.array([radius * math.cos(a0), radius * math.sin(a0), z_offset], dtype=float)
            p1 = np.array([radius * math.cos(a1), radius * math.sin(a1), z_offset], dtype=float)
            delta = p1 - p0
            seg_len = float(np.linalg.norm(delta))
            if seg_len < 1e-12:
                continue
            segments.append({
                "id": seg_id,
                "start": p0,
                "end": p1,
                "tangent": delta / seg_len,
                "length": seg_len,
                "center": 0.5 * (p0 + p1),
            })
            seg_id += 1
    return np.array(segments)


def _discretize_square_path(params, segment_length):
    side = float(params['side'])
    segments = []
    seg_id = 0
    
    sides_data = [
        (np.array([0, 0, 0]), np.array([side, 0, 0]), np.array([1, 0, 0])),
        (np.array([side, 0, 0]), np.array([side, side, 0]), np.array([0, 1, 0])),
        (np.array([side, side, 0]), np.array([0, side, 0]), np.array([-1, 0, 0])),
        (np.array([0, side, 0]), np.array([0, 0, 0]), np.array([0, -1, 0]))
    ]
    
    segs_per_side = _segment_count_from_length(side, segment_length)
    
    for start_corner, end_corner, tangent in sides_data:
        for i in range(segs_per_side):
            t0 = i / segs_per_side
            t1 = (i + 1) / segs_per_side
            
            p0 = start_corner + t0 * (end_corner - start_corner)
            p1 = start_corner + t1 * (end_corner - start_corner)
            
            length = np.linalg.norm(p1 - p0)
            center = (p0 + p1) / 2
            
            segments.append({
                'id': seg_id,
                'start': p0,
                'end': p1,
                'tangent': tangent,
                'length': length,
                'center': center
            })
            seg_id += 1
    
    return np.array(segments)


def _compute_segment_center(edge, param0, param1, p0, p1):
    try:
        param_mid = (param0 + param1) / 2.0
        p_mid = edge.valueAt(param_mid)
        center = np.array([p_mid.x, p_mid.y, p_mid.z])
        return center
    except:
        return np.array([(p0.x + p1.x)/2, (p0.y + p1.y)/2, (p0.z + p1.z)/2])


def _discretize_sketch_path(sketchName, segment_length):
    try:
        import FreeCAD as App
    except ImportError:
        return np.array([])

    if not sketchName or not App.ActiveDocument:
        return np.array([])
    
    try:
        sketch = App.ActiveDocument.getObject(sketchName)
        if not sketch or not hasattr(sketch, 'Shape'):
            return np.array([])
        
        all_edges = sketch.Shape.Edges
        if not all_edges:
            return np.array([])
        
        pl = sketch.Placement
        base = np.array([pl.Base.x, pl.Base.y, pl.Base.z])
        rot = pl.Rotation
        
        def to_global_point(local_pt):
            v = rot.multVec(App.Vector(local_pt[0], local_pt[1], local_pt[2]))
            return base + np.array([v.x, v.y, v.z])
        
        def to_global_vector(local_vec):
            v = rot.multVec(App.Vector(local_vec[0], local_vec[1], local_vec[2]))
            return np.array([v.x, v.y, v.z])
        
        segments = []
        seg_id = 0
        step = max(1e-9, float(segment_length))
        
        for edge in all_edges:
            edge_length = edge.Length
            
            if edge.Curve.TypeId in ['Part::GeomCircle', 'Part::GeomArcOfCircle']:
                segs_for_edge = max(3, _segment_count_from_length(edge_length, step))
            elif edge.Curve.TypeId in ['Part::GeomEllipse', 'Part::GeomBSplineCurve']:
                segs_for_edge = max(4, _segment_count_from_length(edge_length, step))
            else:
                segs_for_edge = _segment_count_from_length(edge_length, step)
            
            for i in range(segs_for_edge):
                t0 = i / segs_for_edge
                t1 = (i + 1) / segs_for_edge
                
                param0 = edge.FirstParameter + t0 * (edge.LastParameter - edge.FirstParameter)
                param1 = edge.FirstParameter + t1 * (edge.LastParameter - edge.FirstParameter)
                
                p0 = edge.valueAt(param0)
                p1 = edge.valueAt(param1)
                
                param_mid = (param0 + param1) / 2.0
                tangent_vec = edge.tangentAt(param_mid)
                tangent_local = np.array([tangent_vec.x, tangent_vec.y, tangent_vec.z])
                tangent_local_norm = np.linalg.norm(tangent_local)
                
                if tangent_local_norm > 1e-12:
                    tangent_local = tangent_local / tangent_local_norm
                else:
                    chord = np.array([p1.x - p0.x, p1.y - p0.y, p1.z - p0.z])
                    chord_norm = np.linalg.norm(chord)
                    tangent_local = chord / chord_norm if chord_norm > 1e-12 else np.array([1, 0, 0])
                
                tangent = to_global_vector(tangent_local)
                tangent_norm = np.linalg.norm(tangent)
                if tangent_norm > 1e-12:
                    tangent = tangent / tangent_norm
                else:
                    tangent = np.array([1, 0, 0])
                
                start_pt = np.array([p0.x, p0.y, p0.z])
                end_pt = np.array([p1.x, p1.y, p1.z])
                
                try:
                    p_mid = edge.valueAt(param_mid)
                    center_local = np.array([p_mid.x, p_mid.y, p_mid.z])
                except:
                    center_local = (start_pt + end_pt) / 2.0
                
                center = to_global_point(center_local)
                
                start_global = to_global_point(start_pt)
                end_global = to_global_point(end_pt)
                
                length = np.linalg.norm(end_global - start_global)
                
                segments.append({
                    'id': seg_id,
                    'start': start_global,
                    'end': end_global,
                    'tangent': tangent,
                    'length': length,
                    'center': center
                })
                seg_id += 1
        
        return np.array(segments)
        
    except Exception as e:
        print(f"Error discretizing sketch path: {e}")
        return np.array([])


_VECTOR_KEYS = ("start", "end", "tangent", "center", "bbox_min", "bbox_max")


def _dim_float(val, default=None):
    try:
        text = str(val).strip()
        if not text:
            return default
        return float(text.split()[0])
    except Exception:
        return default


def build_sweep3dp_geometry_path_params(orientation_path_type, orientation_path_sketch_name, dimensions):

    geometry_path_params = {}

    if orientation_path_type == 0:
        if len(dimensions) > 5 and str(dimensions[5]).strip():
            geometry_path_params["distance"] = float(str(dimensions[5]).strip().split()[0])
    elif orientation_path_type == 1:
        if len(dimensions) > 7 and str(dimensions[7]).strip():
            geometry_path_params["side"] = float(str(dimensions[7]).strip().split()[0])
    elif orientation_path_type == 2:
        geometry_path_params["sketch"] = orientation_path_sketch_name
    elif orientation_path_type == 3:
        try:
            path_type = int(float(str(dimensions[4]).strip()))
        except Exception:
            path_type = -1
        if path_type != 3:
            return geometry_path_params
        eff_w = _dim_float(dimensions[1] if len(dimensions) > 1 else None, None)
        eff_h = _dim_float(dimensions[2] if len(dimensions) > 2 else None, None)
        if eff_w is None or eff_h is None:
            return geometry_path_params
        num_layers = int(_dim_float(dimensions[10] if len(dimensions) > 10 else 1, 1) or 1)
        num_layers = max(1, min(8, num_layers))
        if len(dimensions) > 13 and str(dimensions[13]).strip():
            num_layers = max(1, min(8, int(_dim_float(dimensions[13], num_layers) or num_layers)))
        num_lines = int(_dim_float(dimensions[11] if len(dimensions) > 11 else 1, 1) or 1)
        spacing = _dim_float(dimensions[12] if len(dimensions) > 12 else None, 5.0)
        dirs = []
        for i in range(num_layers):
            idx = 14 + i
            if len(dimensions) > idx and str(dimensions[idx]).strip():
                dirs.append(float(str(dimensions[idx]).strip()))
            else:
                dirs.append(0.0 if i % 2 == 0 else 90.0)
        if len(dimensions) >= 24:
            length_idx = 23
        else:
            length_idx = 15 + num_layers
        total_length = _dim_float(dimensions[length_idx] if len(dimensions) > length_idx else None, None)
        if total_length is None:
            total_length = max(spacing * 4.0, spacing * (num_lines + 2))
        geometry_path_params = {
            "total_length": float(total_length),
            "spacing": float(spacing),
            "eff_w": float(eff_w),
            "eff_h": float(eff_h),
            "num_lines": max(1, int(num_lines)),
            "num_layers": num_layers,
            "dirs": dirs,
        }
    elif orientation_path_type == 6:
        try:
            path_type = int(float(str(dimensions[4]).strip()))
        except Exception:
            path_type = -1
        if path_type != 6:
            return geometry_path_params
        diameter = _dim_float(dimensions[6] if len(dimensions) > 6 else None, None)
        eff_w = _dim_float(dimensions[1] if len(dimensions) > 1 else None, None)
        eff_h = _dim_float(dimensions[2] if len(dimensions) > 2 else None, None)
        if diameter is None or eff_w is None or eff_h is None or diameter <= eff_w:
            return geometry_path_params
        num_layers = int(_dim_float(dimensions[10] if len(dimensions) > 10 else 1, 1) or 1)
        seam_on = False
        if len(dimensions) > 11:
            seam_on = str(dimensions[11]).strip().lower() in ("yes", "y", "on", "true", "1")
        seam_mode = str(dimensions[12]).strip() if len(dimensions) > 12 and str(dimensions[12]).strip() else "Aligned"
        seam_distance = _dim_float(dimensions[13] if len(dimensions) > 13 else None, 0.0) or 0.0
        geometry_path_params = {
            "diameter": float(diameter),
            "eff_w": float(eff_w),
            "eff_h": float(eff_h),
            "num_layers": max(1, int(num_layers)),
            "seam_on": seam_on,
            "seam_mode": seam_mode,
            "seam_distance": float(seam_distance),
        }

    return geometry_path_params


def build_sweep3dp_path_segments(
    geo_type,
    dimensions,
    orientation_path_type,
    orientation_path_sketch_name,
    segment_length,
):

    if geo_type != "Sweep-3DP" or orientation_path_type < 0:
        return None

    geometry_path_params = build_sweep3dp_geometry_path_params(
        orientation_path_type,
        orientation_path_sketch_name,
        dimensions,
    )
    if not geometry_path_params:
        return None

    segments = read_orientationPath_sweep3dp(
        orientation_path_type,
        orientation_path_sketch_name,
        geometry_path_params,
        segment_length,
    )
    if segments is None or len(segments) == 0:
        return None

    return segments


def _segment_to_dict(seg):

    out = {
        "id": int(seg["id"]),
        "length": float(seg["length"]),
    }
    for key in ("half_w", "half_h"):
        if key in seg:
            out[key] = float(seg[key])
    for key in _VECTOR_KEYS:
        if key in seg:
            out[key] = np.asarray(seg[key], dtype=float).tolist()
    return out


def _dict_to_segment(data):

    seg = {
        "id": int(data["id"]),
        "length": float(data["length"]),
    }
    for key in ("half_w", "half_h"):
        if key in data:
            seg[key] = float(data[key])
    for key in _VECTOR_KEYS:
        if key in data:
            seg[key] = np.asarray(data[key], dtype=float)
    return seg


def save_path_segments_json(path_segments, file_path):

    if path_segments is None or len(path_segments) == 0:
        return False

    data = [_segment_to_dict(seg) for seg in path_segments]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return True


def load_path_segments_json(file_path):

    path = Path(file_path)
    if not path.is_file():
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return None

    return [_dict_to_segment(item) for item in data]
