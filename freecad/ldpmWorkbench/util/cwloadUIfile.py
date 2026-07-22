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
## Function to load a module into the left pane of the FreeCAD gui.
##
## ===========================================================================

import os
import FreeCADGui as Gui #type: ignore
from freecad.ldpmWorkbench import GUIPATH


def cwloadUIfile(filename):

        """
        Variables:
        --------------------------------------------------------------------------
        ### Inputs ###
        - filename: Name of the file to be loaded
        --------------------------------------------------------------------------
        ### Outputs ###
        - A module that is loaded into the left pane of the FreeCAD gui
        --------------------------------------------------------------------------
        """

        # Load the ui file
        ui_file_A = os.path.join(GUIPATH,filename)
        a = Gui.PySideUic.loadUi(ui_file_A)

        return a