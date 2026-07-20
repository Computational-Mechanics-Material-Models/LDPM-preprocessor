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
## This file contains the function to check if a particle overlaps with 
## another particle or is too close to the surface
##
## ===========================================================================

import numpy as np


def check_LDPMCSL_particleOverlap(nodes, center, parDiameter, facePoints, binMin, binMax,
    minPar, maxEdgeLength, parOffset, parDiameterList):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - nodes:           (x, y, z) coordinates of each node
    - center:          (x, y, z) position of the center of the new particle
    - parDiameter:     Diameter of the new particle
    - facePoints:      (x, y, z) coordinates of each surface point
    - binMin:          (x, y, z) minimum for the bin to be checked
    - binMax:          (x, y, z) maximum for the bin to be checked
    - minPar:          Minimum diameter of a particle
    - maxEdgeLength:   Maximum length of an edge in the mesh
    - parOffset:       Minimum offset coefficient between particles
    - parDiameterList: List of diameters of each particle
    --------------------------------------------------------------------------
    ### Outputs ###
    - A boolean value that is True if the new particle overlaps
    - A boolean value that is True if the new particle is close to the surface
    --------------------------------------------------------------------------
    """

    # Combine the conditions for all particles and store the result in an array
    binTestParticles = np.logical_and.reduce([(nodes[:,0] > binMin[0]),
        (nodes[:,0] < binMax[0]), (nodes[:,1] > binMin[1]),
        (nodes[:,1] < binMax[1]), (nodes[:,2] > binMin[2]),
        (nodes[:,2] < binMax[2])])

    # Store particle nodes that fall inside the bin
    existingNodes = nodes[binTestParticles, :]
    existingParD = parDiameterList[binTestParticles]

    # Combine the conditions for all surface points and store the result in an array
    binTestSurf = np.all([(facePoints[:,0] > binMin[0]),
        (facePoints[:,0] < binMax[0]), (facePoints[:,1] > binMin[1]),
        (facePoints[:,1] < binMax[1]), (facePoints[:,2] > binMin[2]),
        (facePoints[:,2] < binMax[2])], axis=0)

    # Store edge nodes that fall inside the bin
    existingSurf = facePoints[binTestSurf, :]
 
    # Check if the new particle overlaps with any existing particles
    if existingNodes.shape[0] > 0:
        nodalDistance = np.linalg.norm(center - existingNodes, axis=1)
        parOffsetDist = nodalDistance - parDiameter/2 - existingParD/2 - parOffset
        if (parOffsetDist < 0).any():
            return True, "NA"
    else:
        parOffsetDist = np.array([1])

    # Check if the new particle is too close to the surface
    if existingSurf.shape[0] > 0:
        surfNodalDistance = np.linalg.norm(center - existingSurf, axis=1)
        # Check if critically close to surface (within 1.5 particle radii)
        criticalDistance = parDiameter/2 + 1.5 * minPar / 2
        if (surfNodalDistance < criticalDistance).any():
            # Particle is close to surface, needs inside check
            return False, True
        # Check if too close (overlapping)
        if (surfNodalDistance - parDiameter/2 - 1.1 * minPar / 2 < 0).any():
            return True, "NA"
    else:
        parSurfaceDist = np.array([1])

    # Particle is not overlapping and not critically close to surface
    return False, False
