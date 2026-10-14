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
## Fiber Domain Decomposition
##
## ===========================================================================


import numpy as np

from freecad.ldpmWorkbench.generation.domain_decomposition import (
    _assign_points_to_blocks,
    _factorize_grid,
    _tet_volumes,
)


class FiberDecomposition:

    def __init__(self, counts, tet_rank_id, grid_dims=None, neighbors=None,
                 halo_layers=1):
        self.counts = np.asarray(counts, dtype=int)
        self.tet_rank_id = np.asarray(tet_rank_id, dtype=int)
        self.grid_dims = grid_dims
        self._neighbors = neighbors or [[] for _ in range(len(self.counts))]
        self.halo_layers = int(halo_layers)

    def tets_for_rank(self, rank):
        return self.tet_rank_id == int(rank)

    def neighbors_of(self, rank):
        return list(self._neighbors[int(rank)])

    def halo_mask_for_rank(self, rank):
        rank = int(rank)
        allowed = set(self._neighbors[rank])
        allowed.add(rank)
        return np.isin(self.tet_rank_id, list(allowed))


def assign_fiber_counts(nFibers, nRanks, fractions=None):

    nFibers = int(nFibers)
    nRanks = int(nRanks)
    if nRanks <= 0:
        raise ValueError("nRanks must be > 0")
    if nFibers <= 0:
        return np.zeros(nRanks, dtype=int)

    if fractions is None:
        fractions = np.full(nRanks, 1.0 / nRanks, dtype=float)
    else:
        fractions = np.asarray(fractions, dtype=float)
        s = fractions.sum()
        if s <= 0:
            fractions = np.full(nRanks, 1.0 / nRanks, dtype=float)
        else:
            fractions = fractions / s

    counts = np.maximum(np.round(fractions * nFibers).astype(int), 0)
    if counts.sum() == 0:
        counts[:min(nFibers, nRanks)] = 1

    diff = nFibers - counts.sum()
    i = 0
    guard = 0
    while diff != 0 and guard < nFibers + nRanks + 2:
        r = i % nRanks
        if diff > 0:
            counts[r] += 1
            diff -= 1
        elif counts[r] > 0:
            counts[r] -= 1
            diff += 1
        i += 1
        guard += 1

    return counts.astype(int)


def _tet_rank_assignment(meshVertices, meshTets, nRanks, minC=None, maxC=None):
    meshVertices = np.asarray(meshVertices, dtype=float)
    meshTets = np.asarray(meshTets)
    if minC is None:
        minC = meshVertices.min(axis=0)
    if maxC is None:
        maxC = meshVertices.max(axis=0)
    minC = np.asarray(minC, dtype=float)
    maxC = np.asarray(maxC, dtype=float)
    extents = np.maximum(maxC - minC, 1e-12)

    nx, ny, nz = _factorize_grid(nRanks, extents)
    step = extents / np.array([nx, ny, nz], dtype=float)

    ijk_to_rank = {}
    rank = 0
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                ijk_to_rank[(i, j, k)] = rank
                rank += 1

    v0 = meshVertices[meshTets[:, 0] - 1]
    v1 = meshVertices[meshTets[:, 1] - 1]
    v2 = meshVertices[meshTets[:, 2] - 1]
    v3 = meshVertices[meshTets[:, 3] - 1]
    centroids = (v0 + v1 + v2 + v3) / 4.0
    tet_rank_id = _assign_points_to_blocks(
        centroids, ijk_to_rank, minC, step, (nx, ny, nz))

    tetVol = _tet_volumes(v0, v1, v2, v3)
    vol_per_rank = np.zeros(nRanks)
    for r in range(nRanks):
        vol_per_rank[r] = tetVol[tet_rank_id == r].sum()

    total = vol_per_rank.sum()
    if total <= 0:
        fractions = np.full(nRanks, 1.0 / nRanks)
    else:
        fractions = vol_per_rank / total

    return tet_rank_id, fractions, (nx, ny, nz), step, ijk_to_rank


def _neighbor_lists_layers(grid_dims, ijk_to_rank, layers=1):
    nx, ny, nz = grid_dims
    layers = max(1, int(layers))
    nRanks = nx * ny * nz
    neighbors = [[] for _ in range(nRanks)]
    for (i, j, k), rank in ijk_to_rank.items():
        neigh = []
        for di in range(-layers, layers + 1):
            for dj in range(-layers, layers + 1):
                for dk in range(-layers, layers + 1):
                    if di == 0 and dj == 0 and dk == 0:
                        continue
                    ii, jj, kk = i + di, j + dj, k + dk
                    if 0 <= ii < nx and 0 <= jj < ny and 0 <= kk < nz:
                        neigh.append(ijk_to_rank[(ii, jj, kk)])
        neighbors[rank] = neigh
    return neighbors


def volume_fractions_from_mesh(meshVertices, meshTets, nRanks, minC=None, maxC=None):
    _tet_rank_id, fractions, _dims, _step, _ijk = _tet_rank_assignment(
        meshVertices, meshTets, nRanks, minC=minC, maxC=maxC)
    return fractions


def decompose_fiber_counts(nFibers, nRanks, meshVertices=None, meshTets=None,
                           minC=None, maxC=None, by_volume=True):

    fractions = None
    if by_volume and meshVertices is not None and meshTets is not None:
        fractions = volume_fractions_from_mesh(
            meshVertices, meshTets, nRanks, minC=minC, maxC=maxC)
    return assign_fiber_counts(nFibers, nRanks, fractions=fractions)


def decompose_fiber_domain(nFibers, nRanks, meshVertices, meshTets,
                           minC=None, maxC=None, fiberLength=0.0):
    tet_rank_id, fractions, grid_dims, step, ijk_to_rank = _tet_rank_assignment(
        meshVertices, meshTets, nRanks, minC=minC, maxC=maxC)
    counts = assign_fiber_counts(nFibers, nRanks, fractions=fractions)

    empty = np.array([
        not np.any(tet_rank_id == r) for r in range(nRanks)
    ], dtype=bool)
    if empty.any() and counts.sum() > 0:
        spill = int(counts[empty].sum())
        counts[empty] = 0
        alive = np.flatnonzero(~empty)
        if len(alive) and spill > 0:
            for i in range(spill):
                counts[alive[i % len(alive)]] += 1

    min_step = float(np.min(step))
    if fiberLength and min_step > 0:
        layers = max(1, int(np.ceil(float(fiberLength) / min_step)))
    else:
        layers = 1
    layers = min(layers, max(grid_dims) - 1) if max(grid_dims) > 1 else 1
    neighbors = _neighbor_lists_layers(grid_dims, ijk_to_rank, layers=layers)

    return FiberDecomposition(
        counts, tet_rank_id, grid_dims=grid_dims,
        neighbors=neighbors, halo_layers=layers,
    )
