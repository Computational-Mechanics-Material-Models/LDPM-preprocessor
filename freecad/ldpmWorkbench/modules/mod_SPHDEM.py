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

# pyright: reportMissingImports=false

import os
import sys
import time
import tempfile
import numpy as np
from pathlib import Path
import multiprocessing
import functools
import math

import FreeCADGui as Gui
import FreeCAD as App
import Part
import Part,PartGui
import Mesh
import MeshPartGui, FreeCADGui
import MeshPart
import Mesh, Part, PartGui
import MaterialEditor
import ObjectsFem
import FemGui
import Fem
import femmesh.femmesh2mesh


try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtCore, QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore

# Importing: paths
from freecad.ldpmWorkbench                                              import ICONPATH

# Importing: util
from freecad.ldpmWorkbench.util.cwloadUIfile                            import cwloadUIfile
from freecad.ldpmWorkbench.util.cwloadUIicon                            import cwloadUIicon

# Importing: generation
from freecad.ldpmWorkbench.generation.driver_SPHDEM                     import driver_SPHDEM

# Importing: output
from freecad.ldpmWorkbench.output.mkParameters                          import mkParameters
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs                    import CAD_FILE_DIALOG_FILTER


# Turn off error for divide by zero and invalid operations
np.seterr(divide='ignore', invalid='ignore')



#sys.executable = str(Path(App.ConfigGet('AppHomePath') + '/bin/python.exe'))
multiprocessing.set_executable(sys.executable)



class inputWindow_SPHDEM:
    def __init__(self):

        self.form = []

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_SPHDEM_modelProps.ui"))
        self.form.append(cwloadUIfile("ui_SPHDEM_geometry.ui"))
        self.form.append(cwloadUIfile("ui_SPHDEM_particles.ui"))
        self.form.append(cwloadUIfile("ui_SPHDEM_mixDesign.ui"))
        self.form.append(cwloadUIfile("ui_SPHDEM_generation.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Model Settings")
        self.form[1].setWindowTitle("Geometry")
        self.form[2].setWindowTitle("Particles")        
        self.form[3].setWindowTitle("Mix Design")
        self.form[4].setWindowTitle("Model Generation") 

        cwloadUIicon(self.form[0],"FEM_MaterialMechanicalNonlinear.svg")
        cwloadUIicon(self.form[1],"PartDesign_AdditiveBox.svg")
        cwloadUIicon(self.form[2],"Arch_Material_Group.svg")
        cwloadUIicon(self.form[3],"FEM_ConstraintFlowVelocity.svg")
        cwloadUIicon(self.form[4],"ldpm.svg")

        # Set initial output directory
        self.form[4].outputDir.setText(str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench')))

        # Connect Open File Buttons
        QtCore.QObject.connect(self.form[0].readFileButton, QtCore.SIGNAL("clicked()"), self.openFilePara)
        #QtCore.QObject.connect(self.form[0].readFileButton, QtCore.SIGNAL("clicked()"), self.openFileGeo)
        QtCore.QObject.connect(self.form[4].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)

        # Run generation for LDPM or CSL
        QtCore.QObject.connect(self.form[4].generate, QtCore.SIGNAL("clicked()"), self.generationDriver)
        QtCore.QObject.connect(self.form[4].generateFast, QtCore.SIGNAL("clicked()"), self.generationDriverFast)
        QtCore.QObject.connect(self.form[4].writePara, QtCore.SIGNAL("clicked()"), self.writeParameters)



    def getStandardButtons(self):

        # Only show a close button (PySide2 int vs PySide6 enum)
        btn = QtWidgets.QDialogButtonBox.Close
        return btn.value if hasattr(btn, "value") else int(btn)

    def openFilePara(self):

        path = App.ConfigGet("UserHomePath")
        filetype = "CC Parameter input format (*.cwPar)"

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a file parameter file", path, filetype
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[0].setupFile.setText(OpenName)

    def openFileGeo(self):

        path = App.ConfigGet("UserHomePath")
        filetype = CAD_FILE_DIALOG_FILTER

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a geometry file", path, filetype
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].cadName.setText("Import geometry listed below")
            self.form[1].cadFile.setText(OpenName)

    def openDir(self):

        path = App.ConfigGet('UserHomePath')

        OpenName = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Open Directory', path, QtWidgets.QFileDialog.ShowDirsOnly
        )

        if OpenName == '':  # if not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[5].outputDir.setText(OpenName)

        return OpenName

    def generationDriver(self):

        # Make a temporary path location
        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = False
        mkParameters(self,"SPHDEM",tempPath)
        driver_SPHDEM(self,fastGen,tempPath)

    def generationDriverFast(self):

        # Make a temporary path location
        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = True
        mkParameters(self,"SPHDEM",tempPath)
        driver_SPHDEM(self,fastGen,tempPath)


    def writeParameters(self):

        mkParameters(self,"SPHDEM","writeOnly")

    # Read parameters from file and write to input panel in FreeCAD
    def readParameters(self):

        paraFile = self.form[0].setupFile.text()

        # Read parameters from file
        with open(Path(paraFile), "r") as f:
            for line in f:
                if "numCPU" in line:
                    numCPU = int(line.split("=")[1].strip())
                elif "numIncrements" in line:
                    numIncrements = int(line.split("=")[1].strip())
                elif "maxIter" in line:
                    maxIter = int(line.split("=")[1].strip())
                elif "placementAlg" in line:
                    placementAlg = line.split("=")[1].strip()
                elif "geoType" in line:
                    geoType = line.split("=")[1].strip()
                elif "dimensions" in line:
                    if line != []:
                        # Change from format  ['17.00 mm', '2.00 mm', '5.00 mm'] to [17.00, 2.00, 5.00]
                        dimensions = [float(x.split()[0].strip("'")) for x in line.split("=")[1].strip().strip("[").strip("]").split(",")]
                elif "cadFile" in line:
                    cadFile = line.split("=")[1].strip()
                elif "minPar" in line:
                    minPar = float(line.split("=")[1].strip())
                elif "maxPar" in line:
                    maxPar = float(line.split("=")[1].strip())
                elif "fullerCoef" in line:
                    fullerCoef = float(line.split("=")[1].strip())
                elif "sieveCurveDiameter" in line:
                    sieveCurveDiameter = line.split("=")[1].strip()
                elif "sieveCurvePassing" in line:
                    sieveCurvePassing = line.split("=")[1].strip()
                elif "particleOffsetCoef" in line or "minDistCoef" in line:
                    minDistCoef = float(line.split("=")[1].strip())
                elif "wcRatio" in line:
                    wcRatio = float(line.split("=")[1].strip())
                elif "densityWater" in line:
                    densityWater = float(line.split("=")[1].strip())
                elif "cementC" in line:
                    cementC = float(line.split("=")[1].strip())
                elif "flyashC" in line:
                    flyashC = float(line.split("=")[1].strip())
                elif "silicaC" in line:
                    silicaC = float(line.split("=")[1].strip())
                elif "scmC" in line:
                    scmC = float(line.split("=")[1].strip())
                elif "cementDensity" in line:
                    cementDensity = float(line.split("=")[1].strip())
                elif "flyashDensity" in line:
                    flyashDensity = float(line.split("=")[1].strip())
                elif "silicaDensity" in line:
                    silicaDensity = float(line.split("=")[1].strip())
                elif "scmDensity" in line:
                    scmDensity = float(line.split("=")[1].strip())
                elif "airFrac1" in line:
                    airFrac1 = float(line.split("=")[1].strip())
                elif "outputDir" in line:
                    outputDir = line.split("=")[1].strip()

        if "minDistCoef" not in locals():
            minDistCoef = 0.0
        # Write parameters to input panel
        self.form[0].numCPUbox.setValue(numCPU)
        self.form[0].numPIncBox.setValue(numIncrements)
        self.form[0].numIncBox.setValue(maxIter)
        self.form[0].placementAlg.setCurrentText(placementAlg)
        self.form[1].geometryType.setCurrentText(geoType)
        if geoType == "Box":
            self.form[1].boxLength.setProperty('rawValue',(dimensions[0]))
            self.form[1].boxWidth.setProperty('rawValue',(dimensions[1]))
            self.form[1].boxHeight.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cylinder":
            self.form[1].cylinderHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].cylinderRadius.setProperty('rawValue',(dimensions[1]))
        elif geoType == "Truncated Cone":
            self.form[1].coneHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].coneRadius1.setProperty('rawValue',(dimensions[1]))
            self.form[1].coneRadius2.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cone":
            self.form[1].coneHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].coneRadius1.setProperty('rawValue',(dimensions[1]))
            self.form[1].coneRadius2.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Arbitrary Prism":
            self.form[1].prismCircumradius.setProperty('rawValue',(dimensions[0]))
            self.form[1].prismHeight.setProperty('rawValue',(dimensions[1]))
            self.form[1].prismPolygon.setProperty('rawValue',(dimensions[2]))
        self.form[1].cadFile.setText(cadFile)
        self.form[2].minPar.setValue(minPar)
        self.form[2].maxPar.setValue(maxPar)
        self.form[2].fullerCoef.setValue(fullerCoef)
        self.form[2].sieveDiameters.setText(str(sieveCurveDiameter))
        self.form[2].sievePassing.setText(str(sieveCurvePassing))
        self.form[2].minDistCoef.setValue(minDistCoef)
        self.form[3].wcRatio.setValue(wcRatio)
        self.form[3].waterDensity.setText(str(densityWater))
        self.form[3].cementContent.setText(str(cementC))
        self.form[3].flyashContent.setText(str(flyashC))
        self.form[3].silicaContent.setText(str(silicaC))
        self.form[3].scmContent.setText(str(scmC))
        self.form[3].cementDensity.setText(str(cementDensity))
        self.form[3].flyashDensity.setText(str(flyashDensity))
        self.form[3].silicaDensity.setText(str(silicaDensity))
        self.form[3].scmDensity.setText(str(scmDensity))
        self.form[3].airFrac.setValue(airFrac1)
        self.form[4].outputDir.setText(outputDir)


    # What to do when "Close" Button Clicked
    def reject(self):
         try:
             Gui.ActiveDocument.resetEdit()
             Gui.Control.closeDialog()
         except:
             Gui.Control.closeDialog()

        
class IconViewProviderToFile:                                       # Class ViewProvider create Property view of object
    def __init__( self, obj, icon):
        self.icone = icon
        
    def getIcon(self):                                              # GetIcon
        return self.icone        


class input_SPHDEM_Class():
    """My new command"""

    def GetResources(self):
        return {"Pixmap"  : os.path.join(ICONPATH, "Arch_Material_Group.svg"), # the name of a svg file available in the resources
                "MenuText": "SPH/DEM Generation",
                "ToolTip" : "Generation of an SPH or DEM simulation"}

    def Activated(self):

        Gui.Control.showDialog(inputWindow_SPHDEM())

        return

    def IsActive(self):

        return True

Gui.addCommand("mod_SPHDEM", input_SPHDEM_Class())
