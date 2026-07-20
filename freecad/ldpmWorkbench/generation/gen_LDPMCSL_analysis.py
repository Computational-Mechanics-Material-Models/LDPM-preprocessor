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
## This file contains the function to generate the analysis object
##
## ================================================================================

# pyright: reportMissingImports=false
import FreeCAD as App
import ObjectsFem



def gen_LDPMCSL_analysis(analysisName,constitutiveEQ):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - analysisName: Name of the analysis
    - constitutiveEQ: Constitutive equation to be used in the analysis
    --------------------------------------------------------------------------
    ### Outputs ###
    - analysis_object: Analysis object
    --------------------------------------------------------------------------
    """  


    # See if analysis already exists
    try:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(analysisName)[0] != None)
    except:
        test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(analysisName) != [])

    if test == False:
        # Analysis
        analysis_object = ObjectsFem.makeAnalysis(App.ActiveDocument,analysisName)

        # Solver 
        #solver_object = ObjectsFem.makeSolverCalculixCcxTools(App.ActiveDocument, "Project Chrono")
        #solver_object.GeometricalNonlinearity = 'linear'
        #solver_object.ThermoMechSteadyState = True
        #solver_object.MatrixSolverType = 'default'
        #solver_object.IterationsControlParameterTimeUse = False
        #analysis_object.addObject(solver_object)

        # Store Material
        material_object = ObjectsFem.makeMaterialSolid(App.ActiveDocument, constitutiveEQ)
        mat = material_object.Material
        mat['Name'] = constitutiveEQ
        material_object.Material = mat
        analysis_object.addObject(material_object)