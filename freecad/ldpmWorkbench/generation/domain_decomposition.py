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
## Domain Decomposition for Particles
##
## ===========================================================================


import numpy as np


class SubdomainBlock:

    def __init__(self, rank, ijk, coreMin, coreMax, haloMin, haloMax, closedMax):
        self.rank = rank
        self.ijk = ijk
        self.coreMin = np.asarray(coreMin, dtype=float)
        self.coreMax = np.asarray(coreMax, dtype=float)
        self.haloMin = np.asarray(haloMin, dtype=float)
        self.haloMax = np.asarray(haloMax, dtype=float)
        self.closedMax = np.asarray(closedMax, dtype=bool)

    def contains_point_core(self, point):
        point = np.asarray(point, dtype=float).reshape(-1)
        ge = point >= self.coreMin
        hi = np.where(self.closedMax, point <= self.coreMax, point < self.coreMax)
        return bool(np.all(ge & hi))

    def contains_point_halo(self, point):
        point = np.asarray(point, dtype=float).reshape(-1)
        return bool(np.all(point >= self.haloMin) and np.all(point <= self.haloMax))

    def contains_points_halo(self, points):
        if len(points) == 0:
            return np.zeros(0, dtype=bool)
        pts = np.asarray(points, dtype=float)
        return np.all(pts >= self.haloMin, axis=1) & np.all(pts <= self.haloMax, axis=1)

    def volume(self):
        d = self.coreMax - self.coreMin
        return float(d[0] * d[1] * d[2])

    def __repr__(self):
        return "SubdomainBlock(rank=%d, ijk=%s, core=%s..%s)" % (
            self.rank, self.ijk, self.coreMin.tolist(), self.coreMax.tolist())


class DomainDecomposition:

    def __init__(self, blocks, grid_dims, tet_rank_id, diam_rank_id, neighbors):
        self.blocks = blocks
        self.grid_dims = grid_dims
        self._tet_rank_id = tet_rank_id
        self._diam_rank_id = diam_rank_id
        self._neighbors = neighbors

    def tets_for_rank(self, rank):
        return self._tet_rank_id == rank

    def diameters_for_rank(self, rank):
        return self._diam_rank_id == rank

    def neighbors_of(self, rank):
        return list(self._neighbors[rank])


def _factorize_grid(nRanks, extents):
    extents = np.asarray(extents, dtype=float)
    extents = np.maximum(extents, 1e-12)

    best = None
    for nx in range(1, nRanks + 1):
        if nRanks % nx != 0:
            continue
        rem = nRanks // nx
        for ny in range(1, rem + 1):
            if rem % ny != 0:
                continue
            nz = rem // ny
            block_extents = extents / np.array([nx, ny, nz], dtype=float)
            score = np.std(block_extents) / np.mean(block_extents)
            if best is None or score < best[0]:
                best = (score, (nx, ny, nz))

    return best[1] if best is not None else (nRanks, 1, 1)


def decompose_domain(minC, maxC, nRanks, meshVertices, meshTets,
                     parDiameterList, haloWidth):

    minC = np.asarray(minC, dtype=float)
    maxC = np.asarray(maxC, dtype=float)
    extents = maxC - minC

    nx, ny, nz = _factorize_grid(nRanks, extents)
    step = extents / np.array([nx, ny, nz], dtype=float)

    ijk_to_rank = {}
    blocks = []
    rank = 0
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                coreMin = minC + step * np.array([i, j, k], dtype=float)
                coreMax = minC + step * np.array([i + 1, j + 1, k + 1], dtype=float)
                if i == 0:
                    coreMin[0] = minC[0]
                if j == 0:
                    coreMin[1] = minC[1]
                if k == 0:
                    coreMin[2] = minC[2]
                if i + 1 == nx:
                    coreMax[0] = maxC[0]
                if j + 1 == ny:
                    coreMax[1] = maxC[1]
                if k + 1 == nz:
                    coreMax[2] = maxC[2]

                closedMax = np.array([i + 1 == nx, j + 1 == ny, k + 1 == nz], dtype=bool)
                haloMin = coreMin - haloWidth
                haloMax = coreMax + haloWidth

                ijk_to_rank[(i, j, k)] = rank
                blocks.append(SubdomainBlock(
                    rank, (i, j, k), coreMin, coreMax, haloMin, haloMax, closedMax))
                rank += 1

    grid_dims = (nx, ny, nz)
    neighbors = _neighbor_lists(blocks, grid_dims, ijk_to_rank)

    v0 = meshVertices[meshTets[:, 0] - 1]
    v1 = meshVertices[meshTets[:, 1] - 1]
    v2 = meshVertices[meshTets[:, 2] - 1]
    v3 = meshVertices[meshTets[:, 3] - 1]
    centroids = (v0 + v1 + v2 + v3) / 4.0

    tet_rank_id = _assign_points_to_blocks(centroids, ijk_to_rank, minC, step, grid_dims)

    tetVol = _tet_volumes(v0, v1, v2, v3)
    vol_per_rank = np.zeros(nRanks)
    for r in range(nRanks):
        vol_per_rank[r] = tetVol[tet_rank_id == r].sum()

    total_vol = vol_per_rank.sum()
    if total_vol <= 0:
        fractions = np.full(nRanks, 1.0 / nRanks)
    else:
        fractions = vol_per_rank / total_vol

    diam_rank_id = _assign_diameters_by_fraction(parDiameterList, fractions)

    return DomainDecomposition(blocks, grid_dims, tet_rank_id, diam_rank_id, neighbors)


def _neighbor_lists(blocks, grid_dims, ijk_to_rank):
    nx, ny, nz = grid_dims
    neighbors = [[] for _ in blocks]
    for b in blocks:
        i, j, k = b.ijk
        neigh = []
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for dk in (-1, 0, 1):
                    if di == dj == dk == 0:
                        continue
                    ii, jj, kk = i + di, j + dj, k + dk
                    if 0 <= ii < nx and 0 <= jj < ny and 0 <= kk < nz:
                        neigh.append(ijk_to_rank[(ii, jj, kk)])
        neighbors[b.rank] = neigh
    return neighbors


def _assign_points_to_blocks(points, ijk_to_rank, minC, step, grid_dims):
    nx, ny, nz = grid_dims
    rel = (np.asarray(points, dtype=float) - minC) / step
    idx = np.floor(rel).astype(int)
    idx = np.clip(idx, [0, 0, 0], [nx - 1, ny - 1, nz - 1])

    lookup = np.empty((nx, ny, nz), dtype=int)
    for ijk, r in ijk_to_rank.items():
        lookup[ijk] = r
    return lookup[idx[:, 0], idx[:, 1], idx[:, 2]]


def _tet_volumes(v0, v1, v2, v3):
    a = v1 - v0
    b = v2 - v0
    c = v3 - v0
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    return np.abs(vol)


def _assign_diameters_by_fraction(parDiameterList, fractions):
    n = len(parDiameterList)
    nRanks = len(fractions)
    if n == 0:
        return np.zeros(0, dtype=int)

    order = np.argsort(-np.asarray(parDiameterList))
    counts = np.maximum(np.round(np.asarray(fractions) * n).astype(int), 0)
    if counts.sum() == 0:
        counts[:] = 0
        counts[:min(n, nRanks)] = 1

    diff = n - counts.sum()
    i = 0
    guard = 0
    while diff != 0 and guard < n + nRanks + 2:
        r = i % nRanks
        if diff > 0:
            counts[r] += 1
            diff -= 1
        elif counts[r] > 0:
            counts[r] -= 1
            diff += 1
        i += 1
        guard += 1

    assigned = np.zeros(nRanks, dtype=int)
    rank_id = np.empty(n, dtype=int)
    for idx in order:
        remaining = counts - assigned
        eligible = np.flatnonzero(remaining > 0)
        if len(eligible) == 0:
            r = int(np.argmin(assigned))
        else:
            load = assigned[eligible] / np.maximum(counts[eligible], 1)
            r = int(eligible[np.argmin(load)])
        rank_id[idx] = r
        assigned[r] += 1

    return rank_id
