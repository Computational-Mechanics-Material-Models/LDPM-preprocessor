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
##
## ===========================================================================

import os
import FreeCADGui as Gui #type: ignore
import FreeCAD as App #type: ignore

try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore
from FreeCADGui import Workbench #type: ignore

# Paths to Import
from freecad.ldpmWorkbench import ICONPATH
from freecad.ldpmWorkbench import GUIPATH

# Scripts to Import
from freecad.ldpmWorkbench.modules import mod_LDPM
from freecad.ldpmWorkbench.modules import mod_PLDPM
from freecad.ldpmWorkbench.modules import mod_3DCPLDPM
from freecad.ldpmWorkbench.modules import mod_RF
from freecad.ldpmWorkbench.modules import mod_LDPMCSL_gen
from freecad.ldpmWorkbench.modules import mod_SPHDEM



class ldpmWorkbench(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = "LDPM Workbench"
    ToolTip = "A workbench for building LDPM, CSL, DEM, and SPH models for Project Chrono"
    Icon = os.path.join(ICONPATH, "ldpm.svg")
    toolbox = ["mod_LDPM","mod_PLDPM","mod_3DCPLDPM","mod_RF","mod_LDPMCSL_gen","mod_SPHDEM"] # a list of command names 


    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        
        App.Console.PrintMessage("Switching to LDPM Workbench\n")
        App.Console.PrintMessage("A workbench for building LDPM, CSL, DEM, and SPH models for Project Chrono and other solvers.\n")

        self.appendToolbar("Tools", self.toolbox) # creates a new toolbar with your commands
        self.appendMenu("Tools", self.toolbox) # creates a new menu
        self.appendMenu(["LDPM Workbench"], self.toolbox) # appends a submenu to an existing menu



    def Activated(self):
        '''
        code which should be computed when a user switch to this workbench
        '''
        self._show_report_view()

    @staticmethod
    def _show_report_view():
        """Keep Report view open so generation status stays visible."""
        try:
            mw = Gui.getMainWindow()
            report = mw.findChild(QtWidgets.QDockWidget, "Report view")
            if report is None:
                for dock in mw.findChildren(QtWidgets.QDockWidget):
                    name = (dock.objectName() or "").lower()
                    title = (dock.windowTitle() or "").lower()
                    if "report" in name or "report" in title:
                        report = dock
                        break
            if report is not None:
                report.setVisible(True)
                report.raise_()
                return
            Gui.runCommand("Std_ReportView")
        except Exception:
            pass

    def Deactivated(self):
        '''
        code which should be computed when this workbench is deactivated
        '''
        pass

    def ContextMenu(self, recipient):
        """This function is executed whenever the user right-clicks on screen"""
        # "recipient" will be either "view" or "tree"
        self.appendContextMenu("My commands", self.list) # add commands to the context menu


    def GetClassName(self): 
        # This function is mandatory if this is a full Python workbench
        # This is not a template, the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"



Gui.addWorkbench(ldpmWorkbench())



