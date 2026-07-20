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
## Generate initial periodic mesh using Gmsh and extract the meshVertices,  
## and tetrahedra information from the mesh.
##
## ===========================================================================
import os
import re
import subprocess
import shlex  # Import shlex for safe argument quoting
import FreeCAD as App  # type: ignore
import ImportGui
import Fem
import ObjectsFem  # type: ignore
import numpy as np
from femmesh.gmshtools import GmshTools as gmsh  # type: ignore
import femmesh.femmesh2mesh as mesh2mesh  # type: ignore
import Mesh  # type: ignore
from pathlib import Path


def gen_LDPMCSL_periodicMesh(cadFile, analysisName, geoName, meshName, minPar, dimensions, tempPath):
    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    cadFile:      Path to the CAD file.
    analysisName: Name of the analysis object in the FreeCAD document.
    geoName:      Name of the geometry object in the FreeCAD document.
    meshName:     Name of the mesh object to be created in the document.
    minPar:       Minimum characteristic length parameter for the mesh.
    dimensions:   Dimensions of the part [length, width, height]
    tempPath:     Temporary directory path for file operations.
    --------------------------------------------------------------------------
    ### Outputs ###
    cadFile:      Path to the mesh file.
    --------------------------------------------------------------------------
    """

    # Ensure tempPath is a Path object
    tempPath = Path(tempPath)

    # Strip off the " mm" units from the dimensions
    dimensions_parsed = [float(dim[:-3]) for dim in dimensions]

    # Write the geo file to control periodic meshing
    geo_file_path = tempPath / f"{geoName}.geo"
    with open(geo_file_path, "w") as f:
        f.write('SetFactory("OpenCASCADE");\n')
        f.write(f'Box(1) = {{0, 0, 0, {dimensions_parsed[0]}, {dimensions_parsed[1]}, {dimensions_parsed[2]}}};\n')
        f.write(f'MeshSize {{:}} = {2 * minPar};\n')
        f.write(f'MeshSize {{1}} = {minPar};\n')
        f.write(f'Periodic Surface {{2}} = {{1}} Translate {{{dimensions_parsed[0]}, 0, 0}};\n')
        f.write(f'Periodic Surface {{6}} = {{5}} Translate {{0, 0, {dimensions_parsed[2]}}};\n')
        f.write(f'Periodic Surface {{4}} = {{3}} Translate {{0, {dimensions_parsed[1]}, 0}};\n')
        f.write('\n')

    # Define paths
    gmsh_executable = Path(App.ConfigGet('AppHomePath')) / 'bin' / 'gmsh'
    output_mesh_path = tempPath / f"{geoName}.inp"

    # Construct Gmsh command string for 3D meshing
    gmsh_command = (
        f'"{gmsh_executable}" '
        f'"{geo_file_path}" '
        f'-3 '
        f'-o "{output_mesh_path}" '
        f'-format inp '
        f'-v 0'
    )

    # Run Gmsh command for 3D meshing
    result = subprocess.run(gmsh_command, shell=True, capture_output=True, text=True)

    cadFile = str(output_mesh_path)
    cadFile = re.sub("\\\\", "/", cadFile)

    return cadFile

