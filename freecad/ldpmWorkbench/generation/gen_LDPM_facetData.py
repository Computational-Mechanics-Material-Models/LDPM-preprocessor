## ================================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be found
## in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ================================================================================
## Developed by Northwestern University
## For U.S. Army ERDC Contract No. W9132T22C0015
## Primary Authors: Matthew Troemner
## ================================================================================
##
## This file contains the function to generate the facet data
##
## ================================================================================

import numpy as np


def _normalize_phase_mode(phaseMode):
    if phaseMode is None:
        return 3
    if isinstance(phaseMode, str):
        text = phaseMode.strip().lower().replace(" ", "")
        if text.startswith("2"):
            return 2
        if text.startswith("3"):
            return 3
        raise ValueError(f"Unknown phaseMode string: {phaseMode!r}")
    mode = int(phaseMode)
    if mode not in (2, 3):
        raise ValueError(f"phaseMode must be 2 or 3; got {phaseMode!r}")
    return mode


def _rule_interface_materials(materialRule, phaseMode):
    tables = {
        1: (3, 3, 1),
        2: (3, 3, 2),
        3: (3, 2, 1),
        4: (3, 2, 2),
        5: (1, 3, 1),
        6: (1, 3, 2),
        7: (1, 2, 1),
        8: (1, 2, 2),
    }
    old_agg_itz, old_agg_binder, old_itz_binder = tables[materialRule]
    if phaseMode == 2:
        remap = {1: 2, 2: 2, 3: 1}
        return remap[old_agg_itz], remap[old_agg_binder], remap[old_itz_binder]
    remap = {1: 2, 2: 3, 3: 1}
    return remap[old_agg_itz], remap[old_agg_binder], remap[old_itz_binder]


def _pick_by_volume(m1, m2, vol1, vol2):
    if vol1 == vol2:
        return m1
    if vol1 > vol2:
        return m1
    return m2


_LARGE_FACET_COUNT = 1000000
_FACET_ROT_CHUNK = 100000
_TET_CHUNK = 8000


def _projected_tangents(facetNormals, pn):
    n = facetNormals.shape[0]
    ptan1 = np.empty((n, 3))
    ptan2 = np.empty((n, 3))
    eye3 = np.eye(3)
    pn = np.asarray(pn).reshape(-1, 3)
    for i0 in range(0, n, _FACET_ROT_CHUNK):
        i1 = min(i0 + _FACET_ROT_CHUNK, n)
        fn = facetNormals[i0:i1]
        pnc = pn[i0:i1]
        m = i1 - i0
        v = np.cross(fn, pnc)
        zeros = np.zeros(m)
        ssc = np.array([
            [zeros, -v[:, 2], v[:, 1]],
            [v[:, 2], zeros, -v[:, 0]],
            [-v[:, 1], v[:, 0], zeros],
        ])
        identity = np.repeat(eye3[:, :, None], m, axis=2)
        mul = np.matmul(np.expand_dims(pnc, 1), np.expand_dims(fn, 2)).T
        numer = (np.matmul(ssc.T, ssc.T).T) * (1 - mul)
        denom = np.matmul(np.expand_dims(v, 1), np.expand_dims(v, 2)).T
        used_for_R = np.zeros_like(numer)
        np.divide(numer, denom, out=used_for_R, where=np.abs(denom) > 1e-15)
        rot = np.transpose((identity + ssc + used_for_R).T, (0, 2, 1))
        rand_vec = np.random.rand(m, 3)
        tan1 = np.cross(fn, rand_vec)
        tan1 = tan1 / np.linalg.norm(tan1, axis=1, keepdims=True)
        t1 = np.matmul(rot, np.expand_dims(tan1, 2)).reshape(m, 3)
        t1 = t1 / np.linalg.norm(t1, axis=1, keepdims=True)
        t2 = np.cross(pnc, t1)
        t2 = t2 / np.linalg.norm(t2, axis=1, keepdims=True)
        ptan1[i0:i1] = t1
        ptan2[i0:i1] = t2
    return ptan1, ptan2


def _orient_facets(facets, normals, pn):
    flip = np.sum(pn * normals, axis=1) < 0.0
    oriented = np.array(normals, copy=True)
    oriented[flip] *= -1.0
    coords = facets.reshape(-1, 3, 3).copy()
    if np.any(flip):
        swapped = coords[flip].copy()
        swapped[:, 1, :] = coords[flip, 2, :]
        swapped[:, 2, :] = coords[flip, 1, :]
        coords[flip] = swapped
    return oriented, coords.reshape(-1, 9)


def _subtet_volumes(facets, p1, p2):
    c1 = facets[:, 0:3]
    c2 = facets[:, 3:6]
    c3 = facets[:, 6:9]
    vol1 = np.abs(np.sum((c1 - p1) * np.cross(c2 - p1, c3 - p1), axis=1)) / 6.0
    vol2 = np.abs(np.sum((c1 - p2) * np.cross(c2 - p2, c3 - p2), axis=1)) / 6.0
    return vol1, vol2, vol1 + vol2


def _projected_area(normals, pn, areas):
    area1 = np.sum(normals * pn, axis=1)
    area2 = np.linalg.norm(normals, axis=1) * np.linalg.norm(pn, axis=1)
    return np.abs(area1 / area2 * areas)


def _flat_facets(tetFacets, n_tets, i0, i1):
    arr = np.asarray(tetFacets)
    if arr.ndim == 2 and arr.shape[0] == n_tets and arr.shape[1] == 108:
        return np.ascontiguousarray(arr[i0:i1]).reshape(-1, 9)
    return np.ascontiguousarray(arr.reshape(n_tets, 12, 9)[i0:i1]).reshape(-1, 9)


def _flat_vectors(values, n_tets, i0, i1):
    arr = np.asarray(values)
    if arr.ndim == 2 and arr.shape == (n_tets * 12, 3):
        return arr[i0 * 12:i1 * 12]
    if arr.ndim == 2 and arr.shape == (n_tets, 36):
        return np.ascontiguousarray(arr[i0:i1]).reshape(-1, 3)
    return np.ascontiguousarray(arr.reshape(n_tets, 12, 3)[i0:i1]).reshape(-1, 3)


def _flat_scalars(values, n_tets, i0, i1):
    return np.asarray(values).reshape(-1)[i0 * 12:i1 * 12]


def _assign_facet_materials(facetData, facetMaterial, particleMaterial, f0, f1,
        materialRule, multiMaterial, mode, m1, m2, vol1, vol2, pid1, pid2):
    off = multiMaterial in ['off', 'Off', 'N', 'n', 'No', 'no']
    if off:
        facetData[f0:f1, 18] = 0
        facetMaterial[f0:f1] = 0
        return
    for local in range(f1 - f0):
        row = f0 + local
        a = int(m1[local])
        b = int(m2[local])
        v1 = vol1[local]
        v2 = vol2[local]
        id1 = int(pid1[local])
        id2 = int(pid2[local])
        if materialRule == 9 or materialRule == 10:
            if (id1 != id2) and (id1 > 0) and (id2 > 0):
                facet_mat = 2
            elif a == b:
                facet_mat = a
            else:
                facet_mat = _pick_by_volume(a, b, v1, v2)
        elif materialRule > 0 and materialRule <= 8:
            aggITZ, aggBinder, itzBinder = _rule_interface_materials(materialRule, mode)
            if a == b:
                facet_mat = a
            elif mode == 2:
                pair = {a, b}
                if pair == {1, 2}:
                    facet_mat = aggBinder
                else:
                    facet_mat = _pick_by_volume(a, b, v1, v2)
            else:
                pair = {a, b}
                if pair == {1, 2}:
                    facet_mat = aggITZ
                elif pair == {1, 3}:
                    facet_mat = aggBinder
                elif pair == {2, 3}:
                    facet_mat = itzBinder
                else:
                    facet_mat = _pick_by_volume(a, b, v1, v2)
        else:
            facet_mat = 0
        facetData[row, 18] = facet_mat
        facetMaterial[row] = facet_mat
        particleMaterial[row, 0] = a
        particleMaterial[row, 1] = b


def _gen_LDPM_facetData_chunked(allNodes, allTets, tetFacets, facetCenters,
        facetAreas, facetNormals, tetn1, tetn2, materialList, materialRule,
        multiMaterial, mode, particleID):
    n_tets = len(allTets)
    n_facets = n_tets * 12
    facetData = np.empty((n_facets, 19))
    facetMaterial = np.empty(n_facets)
    particleMaterial = np.empty((n_facets, 2))
    subtetVol = np.empty(n_facets)
    facetVol1 = np.empty(n_facets)
    facetVol2 = np.empty(n_facets)
    tetn1 = np.asarray(tetn1)
    tetn2 = np.asarray(tetn2)
    materialList = np.asarray(materialList)
    particleID = np.asarray(particleID)
    off = multiMaterial in ['off', 'Off', 'N', 'n', 'No', 'no']

    for i0 in range(0, n_tets, _TET_CHUNK):
        i1 = min(i0 + _TET_CHUNK, n_tets)
        local_tets = allTets[i0:i1]
        facets = _flat_facets(tetFacets, n_tets, i0, i1)
        normals = _flat_vectors(facetNormals, n_tets, i0, i1)
        centers = _flat_vectors(facetCenters, n_tets, i0, i1)
        areas = _flat_scalars(facetAreas, n_tets, i0, i1)
        p1 = allNodes[(local_tets[:, tetn1] - 1).astype(int)].reshape(-1, 3)
        p2 = allNodes[(local_tets[:, tetn2] - 1).astype(int)].reshape(-1, 3)
        pn = (p2 - p1) / np.linalg.norm(p2 - p1, axis=1).reshape(-1, 1)
        oriented, flipped = _orient_facets(facets, normals, pn)
        ptan1, ptan2 = _projected_tangents(oriented, pn)
        vol1, vol2, vol = _subtet_volumes(flipped, p1, p2)
        pArea = _projected_area(oriented, pn, areas)
        f0 = i0 * 12
        f1 = i1 * 12
        rows = np.arange(f0, f1)
        facetData[f0:f1, 0] = np.repeat(np.arange(i0, i1), 12)
        facetData[f0:f1, 1] = 3 * rows
        facetData[f0:f1, 2] = 3 * rows + 1
        facetData[f0:f1, 3] = 3 * rows + 2
        facetData[f0:f1, 4] = vol
        facetData[f0:f1, 5] = pArea
        facetData[f0:f1, 6:9] = centers
        facetData[f0:f1, 9:12] = pn
        facetData[f0:f1, 12:15] = ptan1
        facetData[f0:f1, 15:18] = ptan2
        subtetVol[f0:f1] = vol
        facetVol1[f0:f1] = vol1
        facetVol2[f0:f1] = vol2
        n1 = (local_tets[:, tetn1].astype(int) - 1)
        n2 = (local_tets[:, tetn2].astype(int) - 1)
        m1 = materialList[n1].astype(int).reshape(-1)
        m2 = materialList[n2].astype(int).reshape(-1)
        particleMaterial[f0:f1, 0] = m1
        particleMaterial[f0:f1, 1] = m2
        if off:
            facetData[f0:f1, 18] = 0
            facetMaterial[f0:f1] = 0
        else:
            pid1 = particleID[n1].astype(int).reshape(-1)
            pid2 = particleID[n2].astype(int).reshape(-1)
            _assign_facet_materials(
                facetData, facetMaterial, particleMaterial, f0, f1,
                materialRule, multiMaterial, mode, m1, m2, vol1, vol2, pid1, pid2,
            )
    return facetData, facetMaterial, subtetVol, facetVol1, facetVol2, particleMaterial


def gen_LDPM_facetData(allNodes,allTets,tetFacets,facetCenters,\
    facetAreas,facetNormals,tetn1,tetn2,materialList,materialRule,\
    multiMaterial,cementStructure,edgeMaterialList,facetCellData,particleID,
    phaseMode=3):

    mode = _normalize_phase_mode(phaseMode)
    if len(allTets) * 12 > _LARGE_FACET_COUNT:
        return _gen_LDPM_facetData_chunked(
            allNodes, allTets, tetFacets, facetCenters, facetAreas, facetNormals,
            tetn1, tetn2, materialList, materialRule, multiMaterial, mode, particleID,
        )

    facets = tetFacets.reshape(-1, 9)
    p1 = allNodes[(allTets[:, tetn1] - 1).astype(int), :].reshape(-1, 3)
    p2 = allNodes[(allTets[:, tetn2] - 1).astype(int), :].reshape(-1, 3)

    # Projected facet normal
    pn = (p2 - p1) / np.linalg.norm(p2 - p1, axis=1).reshape(-1, 1)

    InitialNormal = np.empty((len(allTets) * 12, 3))
    coords = np.empty((len(allTets) * 12, 3, 3))

    k = 0
    for i in range(len(allTets)):
        for j in range(12):
            Check = np.dot(pn[12 * i + j], facetNormals[12 * i + j])
            if Check < 0:
                InitialNormal[k] = -1 * facetNormals[12 * i + j]
                coords[k, 0] = facets[12 * i + j, 0:3]
                coords[k, 1] = facets[12 * i + j, 6:9]
                coords[k, 2] = facets[12 * i + j, 3:6]
            else:
                InitialNormal[k] = facetNormals[12 * i + j]
                coords[k, 0] = facets[12 * i + j, 0:3]
                coords[k, 1] = facets[12 * i + j, 3:6]
                coords[k, 2] = facets[12 * i + j, 6:9]
            k += 1

    InitialNormal = InitialNormal.reshape(-1, 3)
    coords = coords.reshape(-1, 9)
    facetNormals=InitialNormal
    facets = coords.reshape(-1,9)

    n = facetNormals.shape[0]
    pn = pn.reshape(-1, 3)
    if n > 1000000:
        ptan1 = np.empty((n, 3))
        ptan2 = np.empty((n, 3))
        I3 = np.eye(3)
        for i0 in range(0, n, 100000):
            i1 = min(i0 + 100000, n)
            fn = facetNormals[i0:i1]
            pnc = pn[i0:i1]
            m = i1 - i0
            v = np.cross(fn, pnc)
            zeros = np.zeros(m)
            ssc = np.array([[zeros, -v[:, 2], v[:, 1]],
                            [v[:, 2], zeros, -v[:, 0]],
                            [-v[:, 1], v[:, 0], zeros]])
            identity = np.repeat(I3[:, :, None], m, axis=2)
            mul = np.matmul(np.expand_dims(pnc, 1), np.expand_dims(fn, 2)).T
            numer = (np.matmul(ssc.T, ssc.T).T) * (1 - mul)
            denom = np.matmul(np.expand_dims(v, 1), np.expand_dims(v, 2)).T
            used_for_R = np.zeros_like(numer)
            np.divide(numer, denom, out=used_for_R, where=np.abs(denom) > 1e-15)
            R = identity + ssc + used_for_R
            r = np.random.rand(m, 3)
            tan1 = np.cross(fn, r)
            tan1 = tan1 / np.linalg.norm(tan1, axis=1, keepdims=True)
            tan1 = np.expand_dims(tan1, axis=2)
            t1 = np.squeeze(np.matmul(np.transpose(R.T, (0, 2, 1)), tan1))
            t1 = t1 / np.linalg.norm(t1, axis=1, keepdims=True)
            t2 = np.cross(pnc, t1)
            t2 = t2 / np.linalg.norm(t2, axis=1, keepdims=True)
            ptan1[i0:i1] = t1
            ptan2[i0:i1] = t2
    else:
        v = np.cross(facetNormals,pn.reshape(-1,3))
        zeros = np.zeros(len(v),)
        ssc = np.array(([[zeros, -v[:,2], v[:,1]],[ v[:,2], zeros, -v[:,0]],\
            [ -v[:,1], v[:,0], zeros]]))
        identity = np.dstack([np.eye(3)]*len(v))
        mulNormalsPn = np.matmul(np.expand_dims(pn.reshape(-1,3), axis=1),np.expand_dims(facetNormals, axis=2)).T
        numer = (np.matmul(ssc.T,ssc.T).T)*(1-mulNormalsPn)
        denom = (np.matmul(np.expand_dims(v.reshape(-1,3), axis=1),np.expand_dims(v, axis=2)).T)
        used_for_R = np.zeros_like(numer)
        np.divide(numer, denom, out=used_for_R, where=np.abs(denom) > 1e-15)

        R = identity + ssc + used_for_R

        del Check
        del v
        del zeros
        del identity
        del mulNormalsPn
        del ssc

        r = np.random.rand(facetNormals.shape[0], 3)

        tan1 = np.cross(facetNormals,r)/np.array([np.linalg.norm(np.cross(facetNormals,r),axis=1),]*3).T
        tan1 = np.expand_dims(tan1, axis=2)

        ptan1 = np.squeeze(np.matmul(np.transpose(R.T,(0, 2, 1)),tan1))/\
            np.array([np.linalg.norm(np.squeeze(np.matmul(np.transpose(R.T,\
                (0, 2, 1)),tan1)),axis=1),]*3).T

        ptan2 = np.cross(pn,ptan1)/np.array([np.linalg.norm(np.cross(pn,ptan1),\
            axis=1),]*3).T


    # Sub-tet Volume
    coord1 = facets[:,0:3]
    coord2 = facets[:,3:6]
    coord3 = facets[:,6:9]
    volCalc1 = np.expand_dims(np.transpose(coord1-p1).T, axis=1)
    volCalc2 = np.expand_dims(np.transpose(np.cross((coord2-p1),\
        (coord3-p1))).T, axis=2)
    volCalc3 = np.expand_dims(np.transpose(coord1-p2).T, axis=1)
    volCalc4 = np.expand_dims(np.transpose(np.cross((coord2-p2),\
        (coord3-p2))).T, axis=2)
    facetVol1 = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6)
    facetVol2 = np.squeeze(abs(np.matmul(volCalc3,volCalc4))/6)
    subtetVol = np.squeeze(abs(np.matmul(volCalc1,volCalc2))/6 \
        + abs(np.matmul(volCalc3,volCalc4))/6)




    if n <= 1000000:
        del R
        del tan1
    del coord1
    del coord2
    del coord3
    del p1
    del p2
    del volCalc1
    del volCalc2
    del volCalc3
    del volCalc4

    # Projected Area
    areaCalc1 = np.squeeze(np.matmul(np.expand_dims(facetNormals, axis=1),\
        np.expand_dims(pn, axis=2)))
    areaCalc2 = np.linalg.norm(facetNormals, axis=1)\
        *np.linalg.norm(pn, axis=1)
    pArea = abs(areaCalc1/areaCalc2*facetAreas)

    # Initialize a data matrix for all facet data
    facetData = np.empty([len(allTets)*12,19])

    # Initialize a matrix for facet material information
    facetMaterial = np.empty([len(allTets)*12,])

    # Initialize a matrix for particle material information
    particleMaterial = np.empty([len(allTets)*12,2])

    # Initialize a matrix for particle material ID information
    particleIDs = np.empty([len(allTets)*12,2]) 

    facetCellData = (facetCellData.reshape(-1,3)).astype(int)

    for x in range(0,len(allTets)):

        for y in range(0,12):

            # [Tet Nodes:(IDx IDy IDz) Vol pArea Centers:(cx cy cz) pNormals:(px py pz) pTan1:(qx qy qz) pTan2:(sx sy sz) mF]
            # Note that the order of the facets is Tet 1 (Facet 1-12),Tet 2 (Facet 1-12),...,Tet N (Facet 1-12)
            facetData[12*x+y,0]     = x                       # Tet ID      
            facetData[12*x+y,1:4]   = np.array([3*(12*x+y), 3*(12*x+y)+1, 3*(12*x+y)+2]) # Global Facet Vertex ID
            facetData[12*x+y,4]     = subtetVol[12*x+y]       # Subtet Volume
            facetData[12*x+y,5]     = pArea[12*x+y]           # Projected Facet Area
            facetData[12*x+y,6:9]   = facetCenters[12*x+y,:]  # Facet Centroid
            facetData[12*x+y,9:12]  = pn[12*x+y,:]            # Projected Facet Normal
            facetData[12*x+y,12:15] = ptan1[12*x+y,:]         # Projected Tangent 1
            facetData[12*x+y,15:18] = ptan2[12*x+y,:]         # Projected Tangent 2

            # Store particle materials
            particleMaterial[12*x+y,0] = materialList[allTets[x,tetn1[y]].astype(int)-1].astype(int)
            particleMaterial[12*x+y,1] = materialList[allTets[x,tetn2[y]].astype(int)-1].astype(int)

            particleIDs[12*x+y,0] = particleID[allTets[x,tetn1[y]].astype(int)-1].astype(int)
            particleIDs[12*x+y,1] = particleID[allTets[x,tetn2[y]].astype(int)-1].astype(int)

            m1 = int(particleMaterial[12*x+y,0])
            m2 = int(particleMaterial[12*x+y,1])
            vol1 = facetVol1[12*x+y]
            vol2 = facetVol2[12*x+y]
            pid1 = int(particleIDs[12*x+y,0])
            pid2 = int(particleIDs[12*x+y,1])

            # Material Flag           
            if multiMaterial in ['off','Off','N','n','No','no']:
                facetData[12*x+y,18]    = 0                       # Material Flag 
                facetMaterial[12*x+y]   = 0                       # Material Flag

            else:

                if materialRule == 9 or materialRule == 10:
                    if (pid1 != pid2) and (pid1 > 0) and (pid2 > 0):
                        facet_mat = 2
                    elif m1 == m2:
                        facet_mat = m1
                    else:
                        facet_mat = _pick_by_volume(m1, m2, vol1, vol2)
                    facetData[12*x+y,18] = facet_mat
                    facetMaterial[12*x+y] = facet_mat

                elif materialRule > 0 and materialRule <= 8:

                    aggITZ, aggBinder, itzBinder = _rule_interface_materials(materialRule, mode)

                    if m1 == m2:
                        facet_mat = m1
                    elif mode == 2:
                        pair = {m1, m2}
                        if pair == {1, 2}:
                            facet_mat = aggBinder
                        else:
                            facet_mat = _pick_by_volume(m1, m2, vol1, vol2)
                    else:
                        pair = {m1, m2}
                        if pair == {1, 2}:
                            facet_mat = aggITZ
                        elif pair == {1, 3}:
                            facet_mat = aggBinder
                        elif pair == {2, 3}:
                            facet_mat = itzBinder
                        else:
                            facet_mat = _pick_by_volume(m1, m2, vol1, vol2)

                    facetData[12*x+y,18] = facet_mat
                    facetMaterial[12*x+y] = facet_mat

                else:

                    facetData[12*x+y,18] = 0
                    facetMaterial[12*x+y] = 0              

    return facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial
