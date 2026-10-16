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
## Description coming soon...
##
## ===========================================================================

# pyright: reportMissingImports=false
from pathlib import Path
from femtools import membertools
import numpy as np

def _numeric_rows(path):
    rows = []
    if not path:
        return rows
    with open(path) as handle:
        for line in handle:
            text = line.strip()
            if text == "" or text.startswith("//") or text.startswith("#") or text.startswith("*"):
                continue
            parts = text.replace(",", " ").split()
            try:
                rows.append([float(part) for part in parts])
            except ValueError:
                continue
    return rows


def _facet_columns(width):
    if width in (24, 27):
        tet_col = 1
        mf_col = 23
    else:
        tet_col = 0
        mf_col = 18 if width >= 19 else width - 1
    fiber_cols = None
    if width in (22, 27):
        fiber_cols = (width - 3, width - 2, width - 1)
    return tet_col, mf_col, fiber_cols


def _facet_sets(path):
    rows = _numeric_rows(path)
    if not rows:
        return {}
    width = len(rows[0])
    tet_col, mf_col, fiber_cols = _facet_columns(width)
    by_flag = {}
    fiber_tets = set()
    counts = {}
    for row in rows:
        if len(row) <= max(tet_col, mf_col):
            continue
        tet_id = int(row[tet_col]) + 1
        flag = int(round(row[mf_col]))
        by_flag.setdefault(flag, set()).add(tet_id)
        counts[flag] = counts.get(flag, 0) + 1
        if fiber_cols and len(row) > fiber_cols[2]:
            if abs(row[fiber_cols[0]]) + abs(row[fiber_cols[1]]) + abs(row[fiber_cols[2]]) > 0.0:
                fiber_tets.add(tet_id)
    if not counts:
        return {}
    bulk = max(counts, key=counts.get)
    sets = {}
    for flag, tets in by_flag.items():
        sets["mF_%d" % flag] = sorted(tets)
    interface = set()
    for flag, tets in by_flag.items():
        if flag != bulk:
            interface.update(tets)
    if interface:
        sets["interface"] = sorted(interface)
    if fiber_tets:
        sets["fiber"] = sorted(fiber_tets)
    return sets


def _write_elsets(handle, sets):
    for name in sorted(sets):
        ids = sets[name]
        if not ids:
            continue
        handle.write('*Elset, elset=%s\n' % name)
        line = []
        for index, elem_id in enumerate(ids):
            line.append(str(elem_id))
            if len(line) == 16 or index == len(ids) - 1:
                handle.write(", ".join(line) + "\n")
                line = []


def _fiber_intersection_count(path):
    count = 0
    if not path:
        return 0
    with open(path) as handle:
        for line in handle:
            text = line.strip().lower()
            if text.startswith("intersection:") or text.startswith("intersection "):
                count += 1
    return count


def _reinforcement(path):
    nodes = []
    elements = []
    for row in _numeric_rows(path):
        if len(row) >= 4:
            nodes.append((row[1], row[2], row[3]))
        elif len(row) == 3:
            elements.append((int(row[1]), int(row[2])))
    return nodes, elements


def mkAbaqusInput(elementType, analysisName, materialProps, materialPropsDesc, materialPropsVals, simProps, simPropsValues, \
    nodesFilename, elemFilename, facetsFilename, geoName, outDir, outName, facetPath=None, reinforcementPath=None, fiberPath=None):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - elementType:      The type of element that will be used
    - analysisName:     The name of the analysis
    - materialProps:    The names of the material properties
    - materialPropsVals:The values of the material properties
    - simProps:         The names of the simulation properties
    - simPropsValues:   The values of the simulation properties
    - nodesFilename:    The name of the file containing the nodes
    - elemFilename:     The name of the file containing the tets
    - facetsFilename:   The name of the file containing the facets
    - geoName:          The name of the geometry
    - outDir:           The output directory
    - outName:          The output name
    --------------------------------------------------------------------------
    ### Outputs ###
    - An input file for Abaqus
    --------------------------------------------------------------------------
    """


    # Read in the nodes from the nodes file and store in a numpy array
    # Assume that the file has the following format:
    #// ================================================================================
    #// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/LDPM-preprocessor
    #//
    #// Copyright (c) 2023 
    #// All rights reserved. 
    #//
    #// Use of the code that generated this file is governed by a BSD-style license that
    #// can be found in the LICENSE file at the top level of the distribution and at
    #// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
    #//
    #// ================================================================================
    #// Node Data File
    #// ================================================================================
    #//
    #// Data Structure:
    #// X Y Z 
    #//
    #// ================================================================================
    #0 25 44.98529816
    #0 22.22222137 50
    #0 27.77777863 50
    #0 50 22.22222137
    #0 45.12414169 25.00591087
    with open(Path(outDir + outName + '/' + nodesFilename)) as f:
        allNodes = np.loadtxt(f, skiprows=18)

    # Read in the tets from the tets file and store in a numpy array
    # Assume that the file has the following format:
    #// ================================================================================
    #// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/LDPM-preprocessor
    #//
    #// Copyright (c) 2023 
    #// All rights reserved. 
    #//
    #// Use of the code that generated this file is governed by a BSD-style license that
    #// can be found in the LICENSE file at the top level of the distribution and at
    #// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
    #//
    #// ================================================================================
    #// Tetrahedra Data File
    #// ================================================================================
    #//
    #// Data Structure:
    #// Node 1 Node 2 Node 3 Node 4
    #// Note: Node numbers are zero-indexed
    #//
    #// ================================================================================
    #66 90 92 785
    #707 585 1080 992    
    with open(Path(outDir + outName + '/' + elemFilename)) as f:
        allTets = np.loadtxt(f, skiprows=19)

    # Increase all tet indices by 1 to account for the fact that Abaqus is 1-indexed
    allTets = allTets + 1

    facet_sets = _facet_sets(facetPath)
    fiber_count = _fiber_intersection_count(fiberPath)
    reinf_nodes, reinf_elems = _reinforcement(reinforcementPath)

    with open(Path(outDir + outName + '/' + geoName + '-mesh.inp'),"w") as f:

        f.write('*Heading\n')
        f.write('** Job name: ' + geoName + ' Model name: Model-' + geoName + '\n')
        f.write('** Generated by: Abaqus/CAE 2019\n')
        f.write('**\n')
        f.write('** PARTS\n')
        f.write('**\n')
        f.write('*Part, name=' + geoName + '\n')
        f.write('*Node\n')
        for x in range(0,len(allNodes)):
                f.write(str(x+1) + ', ' + str(allNodes[x,0]) + ', ' \
                    + str(allNodes[x,1]) + ', '  + str(allNodes[x,2]) \
                    + '\n')
        f.write('*Element, type=C3D4\n')
        for x in range(0,len(allTets)):
                f.write(str(x+1) + ', ' + str(allTets[x,0].astype(int)) \
                    + ', ' \
                    + str(allTets[x,1].astype(int)) + ', '  \
                    + str(allTets[x,2].astype(int)) \
                    + ', '  + str(allTets[x,3].astype(int)) +'\n')
        _write_elsets(f, facet_sets)
        f.write('*End Part\n')
        if reinf_nodes and reinf_elems:
            f.write('**\n')
            f.write('*Part, name=Reinforcement\n')
            f.write('*Node\n')
            for index, point in enumerate(reinf_nodes):
                f.write('%d, %s, %s, %s\n' % (index + 1, point[0], point[1], point[2]))
            f.write('*Element, type=T3D2\n')
            for index, element in enumerate(reinf_elems):
                f.write('%d, %d, %d\n' % (index + 1, element[0] + 1, element[1] + 1))
            f.write('*End Part\n')
        f.write('**\n')
        f.write('**\n')
        f.write('** ASSEMBLY\n')
        f.write('**\n')
        f.write('*Assembly, name=Assembly\n')
        f.write('**\n')
        f.write('*Instance, name=' + geoName + '-1, part=' + geoName + '\n')
        f.write('*End Instance\n')
        if reinf_nodes and reinf_elems:
            f.write('*Instance, name=Reinforcement-1, part=Reinforcement\n')
            f.write('*End Instance\n')
        f.write('**\n')
        f.write('*End Assembly\n')
        if fiber_count:
            f.write('** Fiber-facet intersections: %d\n' % fiber_count)
