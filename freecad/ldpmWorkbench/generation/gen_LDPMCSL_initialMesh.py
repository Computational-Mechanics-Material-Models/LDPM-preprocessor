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
## Generate initial mesh using Gmsh and extract the meshVertices,  
## and tetrahedra information from the mesh.
##
## ===========================================================================

import os
import re
from contextlib import contextmanager

from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs import is_mesh_geometry_file

import FreeCAD as App #type: ignore
import ImportGui
import Fem
import ObjectsFem #type: ignore
import numpy as np
from femmesh.gmshtools import GmshTools as gmsh #type: ignore
import femmesh.femmesh2mesh as mesh2mesh #type: ignore
import Mesh #type: ignore


@contextmanager
def _quiet_freecad_console():
    console = App.Console

    def _noop(*args, **kwargs):
        return None

    saved = {}
    for name in ("PrintMessage", "PrintLog", "PrintWarning"):
        if hasattr(console, name):
            saved[name] = getattr(console, name)
            setattr(console, name, _noop)
    try:
        yield
    finally:
        for name, fn in saved.items():
            setattr(console, name, fn)


def gen_LDPMCSL_initialMesh(cadFile,analysisName, geoName, meshName, minPar, geo_obj=None):

    """
    Variable List:
    --------------------------------------------------------------------------
    ### Inputs ###
    analysisName: Name of the analysis object in the FreeCAD document.
    geoName:      Name of the geometry object in the FreeCAD document.
    meshName:     Name of the mesh object to be created in the document.
    minPar:       Minimum characteristic length parameter for the mesh.
    maxPar:       Maximum characteristic length parameter for the mesh.
    --------------------------------------------------------------------------
    ### Outputs ###
    meshVertices:     Array of vertex coordinates (shape: (num_meshVertices, 3))
    meshTets:         Array of tetrahedron node indices (shape: (num_meshTets, 4))
    surfaceNodes:     Array of surface mesh vertices
    surfaceFaces:     Array of surface triangular faces
    --------------------------------------------------------------------------
    """

    mesh_geo = None

    # Check if filetype is CAD (needing meshing) or mesh (already meshed)
    if is_mesh_geometry_file(cadFile):

    # If the file is a mesh file, import the mesh

        Fem.insert(cadFile,App.ActiveDocument.Name)
        filename = os.path.basename(cadFile)
        filename, file_extension = os.path.splitext(filename)
        filename = re.sub("\.", "_", filename)
        filename = re.sub("/.", "_", filename)
        filename = re.sub("-", "_", filename)
        # If filename starts with a number, resub it with an underscore
        filename = re.sub("^\d", "_", filename)
        meshObj = App.getDocument(App.ActiveDocument.Name).getObject(filename)
        meshObj.Label = meshName  


    # If the file is a CAD file, mesh the geometry
    # Or if building the mesh from scratch, create the mesh
    else:

        # Set up Gmsh
        femmesh_obj = ObjectsFem.makeMeshGmsh(App.ActiveDocument, meshName)
        # Set minimum and maximum characteristic lengths for the mesh
        App.ActiveDocument.getObject(meshName).CharacteristicLengthMin = minPar
        App.ActiveDocument.getObject(meshName).CharacteristicLengthMax = 2 * minPar
        App.ActiveDocument.getObject(meshName).MeshSizeFromCurvature = 0
        App.ActiveDocument.getObject(meshName).ElementOrder = u"1st"
        App.ActiveDocument.getObject(meshName).Algorithm2D = u"Delaunay"
        App.ActiveDocument.getObject(meshName).Algorithm3D = u"Delaunay"
        App.ActiveDocument.getObject(meshName).ElementDimension = u"3D"
        App.ActiveDocument.getObject(meshName).CoherenceMesh = True
        mesh_geo = App.getDocument(App.ActiveDocument.Name).getObject(geoName)
        if mesh_geo is None:
            geo_by_label = App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)
            mesh_geo = geo_by_label[0] if geo_by_label else None
        if mesh_geo is None and geo_obj is not None:
            mesh_geo = geo_obj
        if mesh_geo is None:
            raise IndexError(f"Could not find geometry object '{geoName}' for meshing")
        # Assign the geometry object to the mesh object.  FreeCAD 0.20 used a
        # `Part` property on the Gmsh mesher while 1.0 renamed it to `Shape`.
        # Support both so the workbench runs on legacy and current releases.
        if hasattr(femmesh_obj, "Part"):
            femmesh_obj.Part = mesh_geo
        elif hasattr(femmesh_obj, "Shape"):
            femmesh_obj.Shape = mesh_geo
        else:
            raise AttributeError("Gmsh mesh object missing 'Part'/'Shape' attribute")
        App.ActiveDocument.recompute()
        # External generation skips FEM analysis objects
        analysis_obj = App.ActiveDocument.getObject(analysisName)
        mesh_obj = App.ActiveDocument.getObject(meshName)
        if analysis_obj is not None and mesh_obj is not None:
            mesh_obj.adjustRelativeLinks(analysis_obj)
            analysis_obj.addObject(mesh_obj)

        # Run Gmsh to create the mesh
        gmsh_mesh = gmsh(femmesh_obj)
        with _quiet_freecad_console():
            error = gmsh_mesh.create_mesh()
        if error:
            print(error)






    App.ActiveDocument.recompute()

    # Get mesh and initialize lists
    femmesh = App.ActiveDocument.getObjectsByLabel(meshName)[0].FemMesh
    meshVertices = []
    meshTets = []

    # Get the vertex coordinates from the mesh  
    for v in femmesh.Nodes:
        meshVertices.append(femmesh.Nodes[v])
    meshVertices = np.asarray(meshVertices)

    # Get the tetrahedra information from the mesh
    for v in femmesh.Volumes:
        meshTets.append(femmesh.getElementNodes(v))
    meshTets = np.asarray(meshTets)
    meshTets = (meshTets).astype(int)



    with _quiet_freecad_console():
        out_mesh = mesh2mesh.femmesh_2_mesh(App.ActiveDocument.getObjectsByLabel(meshName)[0].FemMesh)
    out_mesh = Mesh.Mesh(out_mesh)


    # Get mesh and initialize lists
    surfaceNodes = []
    surfaceFaces = []


    # Get the vertex coordinates from the mesh  
    for v in range(len(out_mesh.getPoints(0)[0])):
        surfaceNodes.append(out_mesh.getFaces(0)[0][v])
    surfaceNodes = np.asarray(surfaceNodes)

    # Get the faces information from the mesh
    for v in range(len(out_mesh.getFaces(0)[1])):
        surfaceFaces.append(out_mesh.getFaces(0)[1][v])
    surfaceFaces = np.asarray(surfaceFaces)

    return meshVertices, meshTets, surfaceNodes, surfaceFaces
