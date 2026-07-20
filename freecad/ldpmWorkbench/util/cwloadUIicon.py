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
## Function to assign icons from the 'icon' directory to modules in the left
## pane window of FreeCAD.
##
## ===========================================================================

# pyright: reportMissingImports=false
import os
from PySide import QtCore, QtGui
from freecad.ldpmWorkbench import ICONPATH


def cwloadUIicon(form,icon):

    """
    Variables:
    --------------------------------------------------------------------------
    ### Inputs ###
    - form: The form that the icon will be assigned to
    - icon: The name of the icon file
    --------------------------------------------------------------------------
    ### Outputs ###
    - An icon that is assigned to the form
    --------------------------------------------------------------------------
    """

    # Assign the icon to the form
    form.setWindowIcon(QtGui.QIcon.fromTheme("",QtGui.QIcon(os.path.join(ICONPATH, icon))))