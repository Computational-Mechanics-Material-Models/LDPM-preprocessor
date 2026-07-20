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
## Function to generate a Python script for visualizing the labels of a single
## tetrahedron in Paraview
##
## ===========================================================================

from pathlib import Path


def mkPy_LDPM_singleParaviewLabels(geoName, tempPath):


    
    # Generate VTK file for visualizing particles
    with open(Path(tempPath + geoName + \
        '-paraviewLabels.py'),"w") as output_file:                                       


        output_file.write("""
#import paraview
#paraview.compatibility.major = 5
#paraview.compatibility.minor = 11

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# get active source.
lDPMgeo000parasingleTetFacets000vtk = FindSource('LDPMgeo000-para-singleTetFacets.000.vtk')
SetActiveSource(lDPMgeo000parasingleTetFacets000vtk)

# create a query selection
QuerySelect(QueryString='(id >= 0)', FieldType='CELL', InsideOut=0)

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# get display properties
lDPMgeo000parasingleTetFacets000vtkDisplay = GetDisplayProperties(lDPMgeo000parasingleTetFacets000vtk, view=renderView1)

# Properties modified on lDPMgeo000parasingleTetFacets000vtkDisplay
lDPMgeo000parasingleTetFacets000vtkDisplay.SelectionCellLabelVisibility = 1

# Properties modified on lDPMgeo000parasingleTetFacets000vtkDisplay
lDPMgeo000parasingleTetFacets000vtkDisplay.SelectionCellLabelColor = [0.0, 0.0, 0.0]
lDPMgeo000parasingleTetFacets000vtkDisplay.SelectionCellLabelFontSize = 14
lDPMgeo000parasingleTetFacets000vtkDisplay.SelectionPointLabelFontSize = 14


#--------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).
        \n""")