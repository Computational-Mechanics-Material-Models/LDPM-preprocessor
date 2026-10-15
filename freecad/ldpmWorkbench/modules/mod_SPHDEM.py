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
## SPHDEM module for SPHDEM model generation
##
##
## ===========================================================================

# pyright: reportMissingImports=false

import ast
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


def _parameter_entries(para_file):
    entries = {}
    with open(Path(para_file), "r") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            entries[key.strip()] = value
    return entries


def _parameter_dimensions(raw_value):
    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, (list, tuple)):
        return []
    dimensions = []
    for item in parsed:
        text = str(item).strip().strip("'").strip('"')
        number = text.split()[0] if text else ""
        try:
            dimensions.append(float(number))
        except ValueError:
            dimensions.append(text)
    return dimensions



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

        if hasattr(self.form[1], "geometryType"):
            dogbone_idx = self.form[1].geometryType.findText("Dogbone")
            if dogbone_idx >= 0:
                self.form[1].geometryType.setItemIcon(
                    dogbone_idx,
                    QtGui.QIcon(os.path.join(ICONPATH, "Part_Dogbone.svg")),
                )

        # Connect Open File Buttons
        QtCore.QObject.connect(self.form[0].readFileButton, QtCore.SIGNAL("clicked()"), self.openFilePara)
        QtCore.QObject.connect(self.form[1].readFileButton, QtCore.SIGNAL("clicked()"), self.openFileGeo)
        QtCore.QObject.connect(self.form[4].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)

        # Run generation for LDPM or CSL
        QtCore.QObject.connect(self.form[4].generate, QtCore.SIGNAL("clicked()"), self.generationDriver)
        QtCore.QObject.connect(self.form[4].externalGenerate, QtCore.SIGNAL("clicked()"), self.generationDriverExternal)
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
            self.readParameters()

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
            self.form[1].cadFile.setPlainText(OpenName)

    def openDir(self):

        path = App.ConfigGet('UserHomePath')

        OpenName = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Open Directory', path, QtWidgets.QFileDialog.ShowDirsOnly
        )

        if OpenName == '':  # if not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[4].outputDir.setText(OpenName)

        return OpenName

    def _runGeneration(self, runMode):

        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        try:
            mkParameters(self,"SPHDEM",tempPath)
            driver_SPHDEM(self, runMode, tempPath)
        except Exception as error:
            App.Console.PrintError("Generation failed: " + str(error) + "\n")
            self.form[4].statusWindow.setText("Status: ERROR - " + str(error))
            self.form[4].progressBar.setValue(0)

    def generationDriver(self):

        self._runGeneration(True)

    def generationDriverExternal(self):

        self._runGeneration("external")

    def writeParameters(self):

        mkParameters(self,"SPHDEM","writeOnly")

    # Read parameters from file and write to input panel in FreeCAD
    def readParameters(self):

        paraFile = self.form[0].setupFile.text()
        if not paraFile or not os.path.isfile(paraFile):
            App.Console.PrintError("Parameter file was not found.\n")
            return

        params = _parameter_entries(paraFile)

        def _as_int(val, default=0):
            try:
                return int(float(str(val).strip()))
            except (TypeError, ValueError):
                return default

        def _as_float(val, default=0.0):
            try:
                return float(str(val).strip())
            except (TypeError, ValueError):
                return default

        numCPU = _as_int(params.get("numCPU", self.form[0].numCPUbox.value()), default=self.form[0].numCPUbox.value())
        numIncrements = _as_int(params.get("numIncrements", self.form[0].numPIncBox.value()), default=self.form[0].numPIncBox.value())
        maxIter = _as_int(params.get("maxIter", self.form[0].numIncBox.value()), default=self.form[0].numIncBox.value())
        placementAlg = params.get("placementAlg", self.form[0].placementAlg.currentText())
        geoType = params.get("geoType", self.form[1].geometryType.currentText())
        if geoType == "Prism":
            geoType = "Arbitrary Prism"
        elif geoType == "Import CAD or Mesh":
            geoType = "Import CAD"
        dimensions = _parameter_dimensions(params.get("dimensions", "[]"))
        cadFile = params.get("cadFile", "")
        modelType = params.get("modelType", self.form[4].modelType.currentText())
        minPar = _as_float(params.get("minPar", self.form[2].minPar.value()))
        maxPar = _as_float(params.get("maxPar", self.form[2].maxPar.value()))
        fullerCoef = _as_float(params.get("fullerCoef", self.form[2].fullerCoef.value()))
        sieveCurveDiameter = params.get("sieveCurveDiameter", self.form[2].sieveDiameters.text())
        sieveCurvePassing = params.get("sieveCurvePassing", self.form[2].sievePassing.text())
        minDistCoef = _as_float(params.get("particleOffsetCoef", params.get("minDistCoef", self.form[2].minDistCoef.value())))
        wcRatio = _as_float(params.get("wcRatio", self.form[3].wcRatio.value()))
        densityWater = _as_float(params.get("densityWater", self.form[3].waterDensity.text() or 0))
        cementC = _as_float(params.get("cementC", self.form[3].cementContent.text() or 0))
        flyashC = _as_float(params.get("flyashC", self.form[3].flyashContent.text() or 0))
        silicaC = _as_float(params.get("silicaC", self.form[3].silicaContent.text() or 0))
        scmC = _as_float(params.get("scmC", self.form[3].scmContent.text() or 0))
        cementDensity = _as_float(params.get("cementDensity", self.form[3].cementDensity.text() or 0))
        flyashDensity = _as_float(params.get("flyashDensity", self.form[3].flyashDensity.text() or 0))
        silicaDensity = _as_float(params.get("silicaDensity", self.form[3].silicaDensity.text() or 0))
        scmDensity = _as_float(params.get("scmDensity", self.form[3].scmDensity.text() or 0))
        airFrac1 = _as_float(params.get("airFrac1", self.form[3].airFrac.value()))
        outputDir = params.get("outputDir", self.form[4].outputDir.text())

        self.form[0].numCPUbox.setValue(numCPU)
        self.form[0].numPIncBox.setValue(numIncrements)
        self.form[0].numIncBox.setValue(maxIter)
        self.form[0].placementAlg.setCurrentText(placementAlg)
        self.form[1].geometryType.setCurrentText(geoType)
        geoIndex = self.form[1].geometryType.currentIndex()
        if geoIndex >= 0 and hasattr(self.form[1], "widgetStack2"):
            self.form[1].widgetStack2.setCurrentIndex(geoIndex)
        if geoType == "Box" and len(dimensions) >= 3:
            self.form[1].boxLength.setProperty('rawValue',(dimensions[0]))
            self.form[1].boxWidth.setProperty('rawValue',(dimensions[1]))
            self.form[1].boxHeight.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cylinder" and len(dimensions) >= 2:
            self.form[1].cylinderHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].cylinderRadius.setProperty('rawValue',(dimensions[1]))
        elif geoType == "Truncated Cone" and len(dimensions) >= 3:
            self.form[1].truncConeHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].truncConeRadBot.setProperty('rawValue',(dimensions[1]))
            self.form[1].truncConeRadTop.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cone" and len(dimensions) >= 2:
            self.form[1].coneHeight.setProperty('rawValue',(dimensions[0]))
            self.form[1].coneRadius1.setProperty('rawValue',(dimensions[1]))
        elif geoType == "Arbitrary Prism" and len(dimensions) >= 3:
            self.form[1].prismCircumradius.setProperty('rawValue',(dimensions[0]))
            self.form[1].prismHeight.setProperty('rawValue',(dimensions[1]))
            self.form[1].prismPolygon.setValue(int(dimensions[2]))
        elif geoType == "Dogbone" and len(dimensions) >= 6:
            self.form[1].dogboneLength.setProperty('rawValue',(dimensions[0]))
            self.form[1].dogboneWidth.setProperty('rawValue',(dimensions[1]))
            self.form[1].dogboneThickness.setProperty('rawValue',(dimensions[2]))
            self.form[1].gaugeLength.setProperty('rawValue',(dimensions[3]))
            self.form[1].gaugeWidth.setProperty('rawValue',(dimensions[4]))
            self.form[1].dogboneType.setCurrentText(str(dimensions[5]))
        self.form[1].cadFile.setPlainText(cadFile)
        self.form[4].modelType.setCurrentText(modelType)
        self.form[2].minPar.setValue(minPar)
        self.form[2].maxPar.setValue(maxPar)
        self.form[2].fullerCoef.setValue(fullerCoef)
        self.form[2].sieveDiameters.setText(sieveCurveDiameter)
        self.form[2].sievePassing.setText(sieveCurvePassing)
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
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return True

Gui.addCommand("mod_SPHDEM", input_SPHDEM_Class())