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
## MPI Fiber Placement
##
## ===========================================================================



import numpy as np

from freecad.ldpmWorkbench.generation.gen_LDPMCSL_orientationPath import (
    get_zone_from_point,
)
from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer import fiber_crosses_interface


def _toggle_on(value):
    return str(value).strip().lower() in ["on", "y", "yes", "true", "1"]


def point_in_tet(p, A, B, C, D):
    v0, v1, v2 = B - A, C - A, D - A
    vp = p - A
    mat = np.column_stack((v0, v1, v2))
    try:
        bary = np.linalg.solve(mat, vp)
    except np.linalg.LinAlgError:
        return False
    u, v, w = bary
    return (u >= 0) and (v >= 0) and (w >= 0) and (u + v + w <= 1)


def _build_tet_cell_grid(tets_min, tets_max, origin, extents):
    tets_min = np.asarray(tets_min, dtype=float)
    tets_max = np.asarray(tets_max, dtype=float)
    origin = np.asarray(origin, dtype=float)
    extents = np.maximum(np.asarray(extents, dtype=float), 1e-12)

    mean_extent = np.maximum(np.mean(tets_max - tets_min, axis=0), 1e-12)
    raw_dims = np.ceil(extents / (2.0 * mean_extent)).astype(int)
    dims = np.clip(raw_dims, 8, 96)
    cell_size = extents / dims.astype(float)
    nx, ny, nz = int(dims[0]), int(dims[1]), int(dims[2])
    n_cells = nx * ny * nz
    dim_arr = np.array([nx, ny, nz], dtype=np.int32)

    inv = 1.0 / cell_size
    lo = np.floor((tets_min - origin) * inv).astype(np.int32)
    hi = np.floor((tets_max - origin) * inv).astype(np.int32)
    lo = np.clip(lo, 0, dim_arr - 1)
    hi = np.clip(hi, 0, dim_arr - 1)

    buckets = [[] for _ in range(n_cells)]
    single = np.all(lo == hi, axis=1)
    single_ids = np.flatnonzero(single)
    if len(single_ids):
        flat = (lo[single_ids, 0]
                + nx * (lo[single_ids, 1] + ny * lo[single_ids, 2]))
        order = np.argsort(flat, kind="mergesort")
        flat_s = flat[order]
        ids_s = single_ids[order]
        breaks = np.flatnonzero(np.diff(flat_s)) + 1
        starts = np.concatenate(([0], breaks))
        ends = np.concatenate((breaks, [len(flat_s)]))
        for s, e in zip(starts, ends):
            buckets[int(flat_s[s])].extend(ids_s[s:e].tolist())

    multi_ids = np.flatnonzero(~single)
    for i in multi_ids:
        i0, j0, k0 = int(lo[i, 0]), int(lo[i, 1]), int(lo[i, 2])
        i1, j1, k1 = int(hi[i, 0]), int(hi[i, 1]), int(hi[i, 2])
        for ix in range(i0, i1 + 1):
            for iy in range(j0, j1 + 1):
                for iz in range(k0, k1 + 1):
                    buckets[ix + nx * (iy + ny * iz)].append(int(i))

    buckets = [
        np.asarray(b, dtype=np.int32) if b else np.empty(0, dtype=np.int32)
        for b in buckets
    ]

    return {
        "origin": origin,
        "cell_size": cell_size,
        "inv_cell": inv,
        "dims": (nx, ny, nz),
        "buckets": buckets,
    }


def _point_in_grid(p, mesh_cache, grid):
    vertices = mesh_cache["vertices"]
    tets = mesh_cache["tets"]
    tets_min = mesh_cache["tets_min"]
    tets_max = mesh_cache["tets_max"]

    origin = grid["origin"]
    inv = grid["inv_cell"]
    nx, ny, nz = grid["dims"]

    ix = int(np.floor((p[0] - origin[0]) * inv[0]))
    iy = int(np.floor((p[1] - origin[1]) * inv[1]))
    iz = int(np.floor((p[2] - origin[2]) * inv[2]))
    if ix < 0 or iy < 0 or iz < 0 or ix >= nx or iy >= ny or iz >= nz:
        return False

    candidates = grid["buckets"][ix + nx * (iy + ny * iz)]
    for i in candidates:
        if not (tets_min[i, 0] <= p[0] <= tets_max[i, 0]
                and tets_min[i, 1] <= p[1] <= tets_max[i, 1]
                and tets_min[i, 2] <= p[2] <= tets_max[i, 2]):
            continue
        A = vertices[tets[i][0] - 1]
        B = vertices[tets[i][1] - 1]
        C = vertices[tets[i][2] - 1]
        D = vertices[tets[i][3] - 1]
        if point_in_tet(p, A, B, C, D):
            return True
    return False


def point_in_any_tet(p, mesh_cache):
    halo_grid = mesh_cache.get("halo_grid")
    if halo_grid is not None:
        if _point_in_grid(p, mesh_cache, halo_grid):
            return True
    return _point_in_grid(p, mesh_cache, mesh_cache["tet_grid"])


def build_mesh_cache(vertices, tets, surfaceFaces):
    vertices = np.asarray(vertices, dtype=float)
    tets = np.asarray(tets)
    tet_verts = vertices[tets - 1]
    tets_min = np.min(tet_verts, axis=1)
    tets_max = np.max(tet_verts, axis=1)
    tets_min_global = np.min(tet_verts, axis=(0, 1))
    tets_max_global = np.max(tet_verts, axis=(0, 1))
    extents = tets_max_global - tets_min_global

    faces = np.asarray(surfaceFaces, dtype=int)
    coords0 = vertices[faces[:, 0] - 1]
    coords1 = vertices[faces[:, 1] - 1]
    coords2 = vertices[faces[:, 2] - 1]
    averageTriangles = (coords0 + coords1 + coords2) / 3.0

    tet_grid = _build_tet_cell_grid(
        tets_min, tets_max, tets_min_global, extents)

    return {
        "vertices": vertices,
        "tets": tets,
        "tets_min": tets_min,
        "tets_max": tets_max,
        "tets_min_global": tets_min_global,
        "tets_max_global": tets_max_global,
        "surf_coords0": coords0,
        "surf_coords1": coords1,
        "surf_coords2": coords2,
        "averageTriangles": averageTriangles,
        "tet_grid": tet_grid,
        "halo_grid": None,
        "halo_mask": None,
    }


def attach_halo_grid(mesh_cache, halo_mask):
    halo_mask = np.asarray(halo_mask, dtype=bool)
    mesh_cache["halo_mask"] = halo_mask
    if not halo_mask.any():
        mesh_cache["halo_grid"] = None
        return mesh_cache

    full = mesh_cache["tet_grid"]
    origin = full["origin"]
    extents = mesh_cache["tets_max_global"] - mesh_cache["tets_min_global"]
    tets_min = mesh_cache["tets_min"]
    tets_max = mesh_cache["tets_max"]

    halo_ids = np.flatnonzero(halo_mask)
    halo_grid = _build_tet_cell_grid(
        tets_min[halo_ids], tets_max[halo_ids], origin, extents)
    remap = halo_ids.astype(np.int32)
    remapped = []
    for bucket in halo_grid["buckets"]:
        if len(bucket) == 0:
            remapped.append(bucket)
        else:
            remapped.append(remap[bucket])
    halo_grid["buckets"] = remapped
    mesh_cache["halo_grid"] = halo_grid
    return mesh_cache


def _sample_orientation(fiberOrientation, orientationStrength, randomN2, iterReq,
                        pathSegments, p1Fiber):
    if pathSegments is not None and len(pathSegments) > 0:
        zone_id, segment_tangent = get_zone_from_point(p1Fiber, pathSegments)
        if zone_id is None or segment_tangent is None:
            return None
        strength = (6 ** (4 - 4 * orientationStrength) - 1) / 200
        v = np.empty(2)
        j = 0
        while j < 2:
            y = np.random.normal(0, strength, 1)
            if -1 < y < 1:
                v[j] = y
                j += 1
        orienFiber1 = segment_tangent.copy() / np.linalg.norm(segment_tangent)
        orienFiber2 = np.array((
            1,
            np.arctan2(orienFiber1[1], orienFiber1[0]),
            np.arccos(
                orienFiber1[2]
                / (orienFiber1[0] ** 2 + orienFiber1[1] ** 2 + orienFiber1[2] ** 2) ** 0.5
            ),
        ))
        orienFiber3 = np.array((
            1,
            orienFiber2[1] + np.pi * v[0],
            orienFiber2[2] + np.pi / 2 * v[1],
        ))
        orienFiber = np.array((
            np.sin(orienFiber3[2]) * np.cos(orienFiber3[1]),
            np.sin(orienFiber3[2]) * np.sin(orienFiber3[1]),
            np.cos(orienFiber3[2]),
        ))
        if orientationStrength < 1.0:
            sign = -1 if np.random.rand(1) < 0.5 else 1
            orienFiber = sign * orienFiber
        return orienFiber

    if np.allclose(fiberOrientation, 0.0):
        orienFiber1 = np.array((
            1,
            randomN2[iterReq + 1] * 2 * np.pi,
            randomN2[iterReq + 2] * np.pi,
        ))
        orienFiber2 = np.array((
            np.sin(orienFiber1[2]) * np.cos(orienFiber1[1]),
            np.sin(orienFiber1[2]) * np.sin(orienFiber1[1]),
            np.cos(orienFiber1[2]),
        ))
        return orienFiber2 / np.linalg.norm(orienFiber2)

    strength = (6 ** (4 - 4 * orientationStrength) - 1) / 200
    v = np.empty(2)
    j = 0
    while j < 2:
        y = np.random.normal(0, strength, 1)
        if -1 < y < 1:
            v[j] = y
            j += 1
    orienFiber1 = np.asarray(fiberOrientation, dtype=float)
    orienFiber1 = orienFiber1 / np.linalg.norm(orienFiber1)
    orienFiber2 = np.array((
        1,
        np.arctan2(orienFiber1[1], orienFiber1[0]),
        np.arccos(
            orienFiber1[2]
            / (orienFiber1[0] ** 2 + orienFiber1[1] ** 2 + orienFiber1[2] ** 2) ** 0.5
        ),
    ))
    orienFiber3 = np.array((
        1,
        orienFiber2[1] + np.pi * v[0],
        orienFiber2[2] + np.pi / 2 * v[1],
    ))
    orienFiber = np.array((
        np.sin(orienFiber3[2]) * np.cos(orienFiber3[1]),
        np.sin(orienFiber3[2]) * np.sin(orienFiber3[1]),
        np.cos(orienFiber3[2]),
    ))
    sign = -1 if np.random.rand(1) < 0.5 else 1
    return sign * orienFiber


def _try_cut_fiber(p1Fiber, p2Fiber, lFiber, mesh_cache):
    coords0 = mesh_cache["surf_coords0"]
    coords1 = mesh_cache["surf_coords1"]
    coords2 = mesh_cache["surf_coords2"]
    averageTriangles = mesh_cache["averageTriangles"]

    distances = np.linalg.norm(averageTriangles - p2Fiber, axis=1)
    nearest = int(np.argmin(distances))

    p0 = coords0[nearest]
    p1 = coords1[nearest]
    p2 = coords2[nearest]
    p01 = p1 - p0
    p02 = p2 - p0
    fiberVector = p2Fiber - p1Fiber
    denom = np.dot(-fiberVector, np.cross(p01, p02))
    if abs(denom) < 1e-18:
        return None
    t = np.dot(np.cross(p01, p02), (p1Fiber - p0)) / denom
    p2Cut = p1Fiber + fiberVector * t

    if not point_in_any_tet(p2Cut, mesh_cache):
        return None
    cutLen = float(np.linalg.norm(p1Fiber - p2Cut))
    if cutLen >= lFiber or cutLen <= 0:
        return None
    return p2Cut, cutLen


def place_one_fiber(sample_tets, mesh_cache, maxIter, lFiber,
                    fiberOrientation, orientationStrength, cutFiber,
                    pathSegments=None, interfaceRegions=None):
    sample_tets = np.asarray(sample_tets)
    nSample = len(sample_tets)
    if nSample == 0:
        raise RuntimeError("Fiber placement failed: no tets assigned to this rank.")

    vertices = mesh_cache["vertices"]
    allow_cut = _toggle_on(cutFiber)

    randomN1 = np.random.rand(maxIter * 3)
    randomN2 = np.random.rand(maxIter * 3)
    iterReq = 0
    fiberOrientation = np.asarray(fiberOrientation, dtype=float)

    while True:
        iterReq += 3
        if iterReq >= len(randomN1):
            raise RuntimeError(
                "Fiber placement failed: exceeded the %r specified maximum "
                "iterations allowed." % (maxIter,)
            )

        tetIndex = int(randomN1[iterReq] * nSample)
        if tetIndex == nSample:
            tetIndex -= 1

        tetVerts = vertices[sample_tets[tetIndex] - 1]
        weight = np.sort(np.random.rand(3))
        x1 = weight[0]
        x2 = weight[1] - weight[0]
        x3 = weight[2] - weight[1]
        x4 = 1.0 - weight[2]
        p1Fiber = (
            x1 * tetVerts[0]
            + x2 * tetVerts[1]
            + x3 * tetVerts[2]
            + x4 * tetVerts[3]
        )

        orienFiber = _sample_orientation(
            fiberOrientation, orientationStrength, randomN2, iterReq,
            pathSegments, p1Fiber,
        )
        if orienFiber is None:
            continue

        p2Fiber = p1Fiber + orienFiber * lFiber
        if interfaceRegions and fiber_crosses_interface(p1Fiber, p2Fiber, interfaceRegions):
            continue
        inside = point_in_any_tet(p2Fiber, mesh_cache)
        if inside:
            return p1Fiber, p2Fiber, orienFiber, float(lFiber)

        if allow_cut:
            cut = _try_cut_fiber(p1Fiber, p2Fiber, lFiber, mesh_cache)
            if cut is not None:
                p2Cut, cutLen = cut
                return p1Fiber, p2Cut, orienFiber, cutLen
