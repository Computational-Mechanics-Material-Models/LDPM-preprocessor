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


def read_orientationPath_sweep3dp(orientationPathType, orientationPathSketchName, geometryPathParams, numSegments):
    
    try:
        if orientationPathType == 0:
            segments = _discretize_line_path(geometryPathParams, numSegments)
        elif orientationPathType == 1:
            segments = _discretize_square_path(geometryPathParams, numSegments)
        elif orientationPathType == 2:
            segments = _discretize_sketch_path(orientationPathSketchName, numSegments)
        else:
            segments = np.array([])
        
        if len(segments) > 0:
            segments = _validate_segments(segments)
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


def get_zone_from_point(p1Fiber, pathSegments):
    if pathSegments is None or len(pathSegments) == 0:
        return None, None
    
    p1Fiber = np.asarray(p1Fiber, dtype=float)
    
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


def _discretize_line_path(params, numSegments):
    distance = params['distance']
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


def _discretize_square_path(params, numSegments):
    side = params['side']
    segments = []
    seg_id = 0
    
    sides_data = [
        (np.array([0, 0, 0]), np.array([side, 0, 0]), np.array([1, 0, 0])),
        (np.array([side, 0, 0]), np.array([side, side, 0]), np.array([0, 1, 0])),
        (np.array([side, side, 0]), np.array([0, side, 0]), np.array([-1, 0, 0])),
        (np.array([0, side, 0]), np.array([0, 0, 0]), np.array([0, -1, 0]))
    ]
    
    segs_per_side = max(1, numSegments // 4)
    
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


def _discretize_sketch_path(sketchName, numSegments):
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
        total_length = sum(e.Length for e in all_edges)
        
        for edge in all_edges:
            edge_length = edge.Length
            
            if edge.Curve.TypeId in ['Part::GeomCircle', 'Part::GeomArcOfCircle']:
                segs_for_edge = max(3, int(numSegments * edge_length / total_length * 1.5))
            elif edge.Curve.TypeId in ['Part::GeomEllipse', 'Part::GeomBSplineCurve']:
                segs_for_edge = max(4, int(numSegments * edge_length / total_length * 2.0))
            else:
                segs_for_edge = max(1, int(numSegments * edge_length / total_length))
            
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

    return geometry_path_params


def build_sweep3dp_path_segments(
    geo_type,
    dimensions,
    orientation_path_type,
    orientation_path_sketch_name,
    num_segments,
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
        num_segments,
    )
    if segments is None or len(segments) == 0:
        return None

    return segments


def _segment_to_dict(seg):

    out = {
        "id": int(seg["id"]),
        "length": float(seg["length"]),
    }
    for key in _VECTOR_KEYS:
        if key in seg:
            out[key] = np.asarray(seg[key], dtype=float).tolist()
    return out


def _dict_to_segment(data):

    seg = {
        "id": int(data["id"]),
        "length": float(data["length"]),
    }
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
