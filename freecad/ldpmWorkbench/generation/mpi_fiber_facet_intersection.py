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
## MPI Fiber Facet Intersection
##
## ===========================================================================


import numpy as np
from mpi4py import MPI


def _chunk_ranges(n, size):
    base, rem = divmod(int(n), int(size))
    ranges = []
    start = 0
    for r in range(size):
        count = base + (1 if r < rem else 0)
        ranges.append((start, start + count))
        start += count
    return ranges


def _build_tet_cell_grid(tets_min, tets_max):
    tets_min = np.asarray(tets_min, dtype=float)
    tets_max = np.asarray(tets_max, dtype=float)
    origin = np.min(tets_min, axis=0)
    extents = np.maximum(np.max(tets_max, axis=0) - origin, 1e-12)

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
        flat = (
            lo[single_ids, 0]
            + nx * (lo[single_ids, 1] + ny * lo[single_ids, 2])
        )
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


def _query_aabb_tets(fmin, fmax, grid, tets_min, tets_max):
    origin = grid["origin"]
    inv = grid["inv_cell"]
    nx, ny, nz = grid["dims"]
    dim_arr = np.array([nx, ny, nz], dtype=np.int32)
    lo = np.floor((fmin - origin) * inv).astype(np.int32)
    hi = np.floor((fmax - origin) * inv).astype(np.int32)
    lo = np.clip(lo, 0, dim_arr - 1)
    hi = np.clip(hi, 0, dim_arr - 1)

    cand = []
    for ix in range(int(lo[0]), int(hi[0]) + 1):
        for iy in range(int(lo[1]), int(hi[1]) + 1):
            for iz in range(int(lo[2]), int(hi[2]) + 1):
                b = grid["buckets"][ix + nx * (iy + ny * iz)]
                if len(b):
                    cand.append(b)
    if not cand:
        return np.empty(0, dtype=np.int32)
    ids = np.unique(np.concatenate(cand))
    mask = np.all(
        (tets_min[ids] <= fmax) & (tets_max[ids] >= fmin),
        axis=1,
    )
    return ids[mask]


def _build_facet_frames_for_tets(
    tet_ids, allTets, allNodes, tetFacets, facetNormals, facetCenters, tetn1, tetn2
):
    tet_ids = np.asarray(tet_ids, dtype=np.int64)
    if tet_ids.size == 0:
        return {}

    facets_all = tetFacets.reshape(-1, 9)
    if tetFacets.ndim == 2 and tetFacets.shape[1] == 108:
        facets = tetFacets[tet_ids].reshape(-1, 9)
    else:
        idx = (tet_ids[:, None] * 12 + np.arange(12)[None, :]).reshape(-1)
        facets = facets_all[idx]

    fn = facetNormals.reshape(-1, 3)
    fc = facetCenters.reshape(-1, 3)
    if facetNormals.shape[0] == len(allTets) * 12:
        idx = (tet_ids[:, None] * 12 + np.arange(12)[None, :]).reshape(-1)
        normals = fn[idx].copy()
        centers = fc[idx].copy()
    else:
        normals = fn.reshape(len(allTets), 12, 3)[tet_ids].reshape(-1, 3).copy()
        centers = fc.reshape(len(allTets), 12, 3)[tet_ids].reshape(-1, 3).copy()

    p1 = allNodes[(allTets[tet_ids][:, tetn1] - 1).astype(int), :].reshape(-1, 3)
    p2 = allNodes[(allTets[tet_ids][:, tetn2] - 1).astype(int), :].reshape(-1, 3)
    pn = p2 - p1
    pn_norm = np.linalg.norm(pn, axis=1)
    pn_norm[pn_norm == 0] = 1.0
    pn = pn / pn_norm[:, None]

    dot_check = np.einsum("ij,ij->i", pn, normals)
    negative_idx = dot_check < 0
    normals[negative_idx] *= -1
    facets[negative_idx] = facets[negative_idx][:, [0, 1, 2, 6, 7, 8, 3, 4, 5]]

    v = np.cross(normals, pn)
    v_norm_sq = np.sum(v ** 2, axis=1)
    v_norm_sq[v_norm_sq == 0] = 1.0

    ssc = np.zeros((len(v), 3, 3))
    ssc[:, 0, 1] = -v[:, 2]
    ssc[:, 0, 2] = v[:, 1]
    ssc[:, 1, 0] = v[:, 2]
    ssc[:, 1, 2] = -v[:, 0]
    ssc[:, 2, 0] = -v[:, 1]
    ssc[:, 2, 1] = v[:, 0]

    cos_theta = np.einsum("ij,ij->i", normals, pn)[:, None, None]
    I = np.broadcast_to(np.eye(3), (len(v), 3, 3))
    R = I + ssc + np.matmul(ssc, ssc) * (1.0 - cos_theta) / v_norm_sq[:, None, None]
    R_T = R.transpose(0, 2, 1)

    vectorOA = np.expand_dims(centers - facets[:, 0:3], axis=2)
    vectorOB = np.expand_dims(centers - facets[:, 3:6], axis=2)
    vectorOC = np.expand_dims(centers - facets[:, 6:9], axis=2)
    pOA = np.squeeze(np.matmul(R_T, vectorOA), axis=2)
    pOB = np.squeeze(np.matmul(R_T, vectorOB), axis=2)
    pOC = np.squeeze(np.matmul(R_T, vectorOC), axis=2)

    RcoordP1 = centers - pOA
    RcoordP2 = centers - pOB
    RcoordP3 = centers - pOC
    vector12 = RcoordP2 - RcoordP1
    vector23 = RcoordP3 - RcoordP2
    vector31 = RcoordP1 - RcoordP3
    cross_n = np.cross(vector12, RcoordP3 - RcoordP1)
    nrm = np.linalg.norm(cross_n, axis=1)
    nrm[nrm == 0] = 1.0
    Normal = cross_n / nrm[:, None]

    frames = {}
    for li, tid in enumerate(tet_ids):
        s = 12 * li
        e = s + 12
        frames[int(tid)] = (
            Normal[s:e],
            RcoordP1[s:e],
            RcoordP2[s:e],
            RcoordP3[s:e],
            vector12[s:e],
            vector23[s:e],
            vector31[s:e],
        )
    return frames


def _build_projected_facets(
    allTets, allNodes, tetFacets, facetNormals, facetCenters, tetn1, tetn2
):
    tet_ids = np.arange(len(np.asarray(allTets)), dtype=np.int64)
    frames = _build_facet_frames_for_tets(
        tet_ids, allTets, allNodes, tetFacets, facetNormals, facetCenters, tetn1, tetn2
    )
    if not frames:
        return np.zeros((0, 3))
    r1 = np.vstack([frames[int(t)][1] for t in tet_ids])
    r2 = np.vstack([frames[int(t)][2] for t in tet_ids])
    r3 = np.vstack([frames[int(t)][3] for t in tet_ids])
    return np.concatenate((r1, r2, r3))


def _intersect_fiber_tet(p1, p2, orien, dFiber, tet_id, frame, out_rows, hit_fibers, fiber_id):
    Normal, R1, R2, R3, v12, v23, v31 = frame
    p12 = p2 - p1
    for y in range(12):
        nvec = Normal[y]
        denom = np.dot(nvec, p12)
        if abs(denom) <= 0.0:
            continue
        offsetd = -np.dot(nvec, R1[y])
        t = -(offsetd + np.dot(nvec, p1)) / denom
        if t < 0.0 or t > 1.0:
            continue
        P = p1 + t * p12
        if np.dot(nvec, np.cross(v12[y], P - R1[y])) < 0:
            continue
        if np.dot(nvec, np.cross(v23[y], P - R2[y])) < 0:
            continue
        if np.dot(nvec, np.cross(v31[y], P - R3[y])) < 0:
            continue
        dist_p1 = np.linalg.norm(P - p1)
        dist_p2 = np.linalg.norm(P - p2)
        out_rows.append(
            [
                float(tet_id + 1),
                float(y + 1),
                float(orien[0]),
                float(orien[1]),
                float(orien[2]),
                float(min(dist_p1, dist_p2)),
                float(max(dist_p1, dist_p2)),
                float(dFiber),
                1.0,
            ]
        )
        hit_fibers.append(fiber_id)


def run_mpi_fiber_facet_int(
    p1Fiber,
    p2Fiber,
    dFiber,
    lFiber,
    orienFibers,
    allTets,
    allNodes,
    tetFacets,
    tetn1,
    tetn2,
    facetNormals,
    facetCenters,
    verbose=False,
):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    p1Fiber = np.asarray(p1Fiber, dtype=float).reshape(-1, 3)
    p2Fiber = np.asarray(p2Fiber, dtype=float).reshape(-1, 3)
    orienFibers = np.asarray(orienFibers, dtype=float).reshape(-1, 3)
    nF = len(p1Fiber)
    dFiber = float(np.asarray(dFiber).reshape(-1)[0] if np.size(dFiber) else dFiber)

    allTets = np.asarray(allTets)
    allNodes = np.asarray(allNodes, dtype=float)
    tetn1 = np.asarray(tetn1, dtype=int).reshape(-1)
    tetn2 = np.asarray(tetn2, dtype=int).reshape(-1)
    facetNormals = np.asarray(facetNormals, dtype=float)
    facetCenters = np.asarray(facetCenters, dtype=float)
    tetFacets = np.asarray(tetFacets, dtype=float)

    tets_coords = allNodes[allTets.astype(int) - 1]
    tets_min = np.min(tets_coords, axis=1)
    tets_max = np.max(tets_coords, axis=1)
    grid = _build_tet_cell_grid(tets_min, tets_max)

    ranges = _chunk_ranges(nF, size)
    i0, i1 = ranges[rank]
    my_fibers = np.arange(i0, i1, dtype=np.int64)

    if verbose:
        print("rank %d: fiber %d/%d" % (rank, len(my_fibers), nF), flush=True)

    cand_map = {}
    for z in my_fibers:
        fmin = np.minimum(p1Fiber[z], p2Fiber[z])
        fmax = np.maximum(p1Fiber[z], p2Fiber[z])
        ids = _query_aabb_tets(fmin, fmax, grid, tets_min, tets_max)
        cand_map[int(z)] = ids

    needed_tets = (
        np.unique(np.concatenate(list(cand_map.values())))
        if cand_map and any(len(v) for v in cand_map.values())
        else np.empty(0, dtype=np.int64)
    )

    frames = {}
    chunk = 2000
    for s in range(0, len(needed_tets), chunk):
        part = needed_tets[s : s + chunk]
        frames.update(
            _build_facet_frames_for_tets(
                part,
                allTets,
                allNodes,
                tetFacets,
                facetNormals,
                facetCenters,
                tetn1,
                tetn2,
            )
        )
        if verbose and (s // chunk) % 5 == 0:
            print(
                "rank %d: frames %d/%d" % (rank, min(s + chunk, len(needed_tets)), len(needed_tets)),
                flush=True,
            )

    rows = []
    hit_fibers = []
    total_pairs = 0
    report_every = max(1, len(my_fibers) // 10)
    for k, z in enumerate(my_fibers):
        ids = cand_map.get(int(z), np.empty(0, dtype=np.int32))
        total_pairs += len(ids)
        p1 = p1Fiber[z]
        p2 = p2Fiber[z]
        orien = orienFibers[z]
        for tid in ids:
            fr = frames.get(int(tid))
            if fr is None:
                continue
            _intersect_fiber_tet(
                p1, p2, orien, dFiber, int(tid), fr, rows, hit_fibers, int(z)
            )
        if verbose and ((k + 1) % report_every == 0 or (k + 1) == len(my_fibers)):
            print(
                "rank %d: fiber %d/%d, hits %d" % (rank, k + 1, len(my_fibers), len(rows)),
                flush=True,
            )

    local = np.asarray(rows, dtype=float).reshape(-1, 9) if rows else np.zeros((0, 9))
    local_hits = (
        np.unique(np.asarray(hit_fibers, dtype=np.int64))
        if hit_fibers
        else np.empty(0, dtype=np.int64)
    )

    gathered = comm.gather((local, local_hits, total_pairs), root=0)

    if rank != 0:
        return None, None, None, None, None, None, None

    parts = [g[0] for g in gathered if g[0] is not None and len(g[0])]
    hits = [g[1] for g in gathered if g[1] is not None and len(g[1])]
    pair_count = sum(int(g[2]) for g in gathered)

    if parts:
        FiberdataList = np.vstack(parts)
        FiberdataList = FiberdataList[np.lexsort(FiberdataList[:, ::-1].T)]
        for k in range(1, len(FiberdataList)):
            if (
                FiberdataList[k, 0] == FiberdataList[k - 1, 0]
                and FiberdataList[k, 1] == FiberdataList[k - 1, 1]
            ):
                FiberdataList[k, 8] = FiberdataList[k - 1, 8] + 1
        MaxInterPerFacet = float(np.max(FiberdataList[:, 8]))
        TotalIntersections = float(len(FiberdataList))
    else:
        FiberdataList = np.zeros((0, 9))
        MaxInterPerFacet = 0.0
        TotalIntersections = 0.0

    IntersectedFiber = np.unique(np.concatenate(hits)) if hits else np.empty(0, dtype=np.int64)
    TotalFiber = int(IntersectedFiber.size)
    projectedFacet = _build_projected_facets(
        allTets, allNodes, tetFacets, facetNormals, facetCenters, tetn1, tetn2
    )
    TotalTet = float(pair_count)

    if verbose:
        print(
            "Fiber-facet intersections: %d, fibers hit %d" % (int(TotalIntersections), TotalFiber),
            flush=True,
        )

    return (
        FiberdataList,
        TotalIntersections,
        MaxInterPerFacet,
        TotalTet,
        TotalFiber,
        IntersectedFiber,
        projectedFacet,
    )
