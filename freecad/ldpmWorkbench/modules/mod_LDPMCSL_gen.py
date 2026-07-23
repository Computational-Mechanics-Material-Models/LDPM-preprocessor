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
import functools
import math
import shutil

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
import Spreadsheet

try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtCore, QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore

from freecad.ldpmWorkbench                                     import ICONPATH
from freecad.ldpmWorkbench                                     import GUIPATH

from freecad.ldpmWorkbench.util.cwloadUIfile                    import cwloadUIfile
from freecad.ldpmWorkbench.util.cwloadUIicon                    import cwloadUIicon

from freecad.ldpmWorkbench.output.mkChronoInput                  import mkChronoInput
from freecad.ldpmWorkbench.output.mkAbaqusInput                  import mkAbaqusInput



class genWindow_LDPMCSL:
    def __init__(self):

        self.form = []

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_LDPMCSL_writeSimInfo.ui"))
        self.form.append(cwloadUIfile("ui_LDPMCSL_writeSimFiles.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Confirm Output")
        self.form[1].setWindowTitle("Write File")

        cwloadUIicon(self.form[0],"ldpmOutput.svg")
        cwloadUIicon(self.form[1],"ldpmOutput.svg")


        materialProps = [\
            "Density",\
            "CompressiveStrength",\
            "ShearNormalCoupling",\
            "InitialHardeningModulusRatio",\
            "FinalHardeningModulusRatio",\
            "DensificationRatio",\
            "TransitionalStrainRatio",\
            "ShearTensileStrengthRatio",\
            "InitialInternalFrictionCoefficient",\
            "SofteningExponent",\
            "DeviatoricStrainRatio",\
            "DeviatoricDamage",\
            "FinalInternalFrictionCoefficient",\
            "TransitionalNormalStress",\
            "TensileStrength",\
            "TensileCharacteristicLength",\
            "NormalModulus",\
            ]



        # Set initial output directory
        self.form[1].outputDir.setText(str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench')))

        # Try to see if there is a material object in the document
        try:
            test = App.ActiveDocument.getObject("LDPMmaterial")
            self.elementType = "LDPM"
        except:
            try:
                test = App.ActiveDocument.getObject("CSLmaterial")
                self.elementType = "CSL"
            except:
                App.Console.PrintMessage("No LDPM or CSL material found. Please create a material object and try again."+"\n")
                self.elementType = "None"
                self.numPartsLDPM,self.numPartsCSL = 0,0
                modelInfo = []


        # Get number of LDPM or CSL components
        # Check for number of LDPM components
        if self.elementType == "LDPM":
            geoName = self.elementType + "geo" + str(0).zfill(3)
            i = 0
            count = 0
            try:
                test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
            except:
                count = count+1
            try:
                test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])
            except:
                count = count+1
            if count == 2:
                test = False
            
            while test == True:
                i = i+1
                geoName = self.elementType + "geo" + str(i).zfill(3)
                try:
                    test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
                except:
                    count = count+1
                try:
                    test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])
                except:
                    count = count+1
                if count == 2:
                    test = False
            self.numPartsLDPM = i
            self.numPartsCSL = 0

       # Check for number of CSL components
        elif self.elementType == "CSL":
            geoName = self.elementType + "geo" + str(0).zfill(3)
            i = 0
            count = 0
            try:
                test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
            except:
                count = count+1
            try:
                test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])
            except:
                count = count+1
            if count == 2:
                test = False
            
            while test == True:
                i = i+1
                geoName = self.elementType + "geo" + str(i).zfill(3)
                try:
                    test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0] != None)
                except:
                    count = count+1
                try:
                    test = (App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName) != [])
                except:
                    count = count+1
                if count == 2:
                    test = False
            self.numPartsCSL = i
            self.numPartsLDPM = 0



        # Store information about the LDPM/CSL components
        modelInfo = []
        modelInfo.append("Element Type: " + self.elementType)
        modelInfo.append("Number of Components: " + str(max(self.numPartsLDPM,self.numPartsCSL)))

        # Get number of nodes and elements
        if self.elementType == "LDPM":
            for i in range(self.numPartsLDPM):
                meshName = self.elementType + "mesh" + str(i).zfill(3)
                femesh=App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(meshName)[0]
                numNodes = femesh.FemMesh.NodeCount
                numElements = femesh.FemMesh.TetraCount
            modelInfo.append("Part " + str(i))
            modelInfo.append("Number of Nodes: " + str(numNodes))
            modelInfo.append("Number of Tets: " + str(numElements))
        elif self.elementType == "CSL":
            for i in range(self.numPartsCSL):
                meshName = self.elementType + "mesh" + str(i).zfill(3)
                femesh=App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(meshName)[0]
                numNodes = femesh.FemMesh.NodeCount
                numElements = femesh.FemMesh.TetraCount
            modelInfo.append("Part " + str(i))
            modelInfo.append("Number of Nodes: " + str(numNodes))
            modelInfo.append("Number of Tets: " + str(numElements))


        # Get Material Properties
        if self.elementType == "LDPM":
            mat = App.ActiveDocument.LDPMmaterial
            modelInfo.append("Material Properties")
            for i in range(len(materialProps)):
                modelInfo.append(materialProps[i] + ": " + str(mat.getPropertyByName(materialProps[i])))

        elif self.elementType == "CSL":
            mat = App.ActiveDocument.CSLmaterial
            modelInfo.append("Material Properties")
            for i in range(len(materialProps)):
                modelInfo.append(materialProps[i] + ": " + str(mat.getPropertyByName(materialProps[i])))


        # Change modelinfo to a string with newlines
        modelInfoStr = ""
        for i in range(len(modelInfo)):
            modelInfoStr = modelInfoStr + "<p>" + modelInfo[i] + "</p>"

        
        # Display all LDPM/CSL input data in the side panel "Confirm Output"
        self.form[0].statusWindow.setText(modelInfoStr)
            


        # Connect Open File Buttons
        QtCore.QObject.connect(self.form[1].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)

        # Run Project Chrono generation for LDPM or CSL
        QtCore.QObject.connect(self.form[1].writeChrono, QtCore.SIGNAL("clicked()"), self.chronoGeneration)

        # Run Abaqus generation for LDPM
        QtCore.QObject.connect(self.form[1].writeAbaqus, QtCore.SIGNAL("clicked()"), self.abaqusGeneration)


    def getStandardButtons(self):

        # Close button only (PySide2 int vs PySide6 enum)
        btn = QtWidgets.QDialogButtonBox.Close
        return btn.value if hasattr(btn, "value") else int(btn)



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

    def chronoGeneration(self):

        # Print error and exit if no LDPM or CSL material found
        if self.elementType != "LDPM" and self.elementType != "CSL":
            App.Console.PrintMessage("No LDPM or CSL material found. Please create a material object and try again."+"\n")
            return

        print('Writing files.')

        # Set element type and number of parts
        elementType = self.elementType
        numParts = max(self.numPartsLDPM,self.numPartsCSL)

        partName = "LDPMgeo000"

        # Set filenames
        nodesFilename = partName + "-data-nodes.dat"
        tetsFilename = partName + "-data-tets.dat"
        facetsFilename = partName + "-data-facets.dat"

        # Make output directory if does not exist
        outDir =  self.form[1].outputDir.text()
        try:
            os.mkdir(outDir)
        except:
            pass

        i = 0
        outName = '/' + "chronoPackage" + elementType + str(i).zfill(3)
        while os.path.isdir(Path(outDir + outName)):
            i = i+1
            outName = '/' + "chronoPackage" + elementType + str(i).zfill(3)

        try:
            os.mkdir(outDir + outName)
        except:
            pass

        # Set analysis and material names
        analysisName = elementType + "analysis"
        materialName = elementType + "material"

        # Get locations of data files
        geoName = elementType + "geo" + str(0).zfill(3)
        LDPMnodesDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMnodesData").getPropertyByName("Location"))
        LDPMtetsDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMtetsData").getPropertyByName("Location"))
        LDPMfacetsDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMfacetsData").getPropertyByName("Location"))

        # Copy files to output directory
        shutil.copyfile(LDPMnodesDataLoc, outDir + outName + "/" + partName + "-data-nodes.dat")
        shutil.copyfile(LDPMtetsDataLoc, outDir + outName + "/" + partName + "-data-tets.dat")
        shutil.copyfile(LDPMfacetsDataLoc, outDir + outName + "/" + partName + "-data-facets.dat")
        shutil.copyfile(LDPMfacetsDataLoc, outDir + outName + "/" + partName + "-data-facetsVertices.dat")
        shutil.copyfile(LDPMfacetsDataLoc, outDir + outName + "/" + partName + "-data-faceFacets.dat")

        materialProps = [\
            "Density",\
            "CompressiveStrength",\
            "ShearNormalCoupling",\
            "InitialHardeningModulusRatio",\
            "FinalHardeningModulusRatio",\
            "DensificationRatio",\
            "TransitionalStrainRatio",\
            "ShearTensileStrengthRatio",\
            "InitialInternalFrictionCoefficient",\
            "SofteningExponent",\
            "DeviatoricStrainRatio",\
            "DeviatoricDamage",\
            "FinalInternalFrictionCoefficient",\
            "TransitionalNormalStress",\
            "TensileStrength",\
            "TensileCharacteristicLength",\
            "NormalModulus",\
            ]
                
        materialPropsDesc = []
        
        materialPropsValues = []

        simProps = [\
            "TotalTime",\
            "TimestepSize",\
            "NumberOfThreads",\
            "NumberOutputSteps",\
            ]

        simPropsValues = []

        # Read material properties from model
        for x in range(len(materialProps)):
            materialPropsValues.append(App.getDocument(App.ActiveDocument.Name).getObject(materialName).getPropertyByName(materialProps[x]))


        # Read simulation properties from model
        for x in range(len(simProps)):
            simPropsValues.append(App.getDocument(App.ActiveDocument.Name).getObject(analysisName).getPropertyByName(simProps[x]))



        # Make Project Chrono input file
        mkChronoInput(elementType, analysisName, materialProps, materialPropsDesc, materialPropsValues, simProps, simPropsValues, \
            nodesFilename, tetsFilename, facetsFilename, geoName, outDir, outName)


        print("Chrono data package written to: " + outDir + outName)



    def abaqusGeneration(self):
        
        # Print error and exit if no LDPM or CSL material found
        if self.elementType != "LDPM" and self.elementType != "CSL":
            App.Console.PrintMessage("No LDPM or CSL material found. Please create a material object and try again."+"\n")
            return
        
        # Print error and exit if CSL material found
        if self.elementType == "CSL":
            App.Console.PrintMessage("CSL element not yet supported for Abaqus."+"\n")
            return

        print('Writing files.')

        partName = 'LDPMgeo000'

        # Set element type and number of parts
        elementType = self.elementType
        numParts = max(self.numPartsLDPM,self.numPartsCSL)

        # Set filenames
        nodesFilename = partName + "-data-nodes.dat"
        tetsFilename = partName + "-data-tets.dat"
        facetsFilename = partName + "-data-facets.dat"

        # Make output directory if does not exist
        outDir =  self.form[1].outputDir.text()
        try:
            os.mkdir(outDir)
        except:
            pass


        i = 0
        outName = '/' + "abaqusPackage" + elementType + str(i).zfill(3)
        while os.path.isdir(Path(outDir + outName)):
            i = i+1
            outName = '/' + "abaqusPackage" + elementType + str(i).zfill(3)

        try:
            os.mkdir(outDir + outName)
        except:
            pass

        # Set analysis and material names
        analysisName = elementType + "analysis"
        materialName = elementType + "material"

        # Get locations of data files
        geoName = elementType + "geo" + str(0).zfill(3)
        LDPMnodesDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMnodesData").getPropertyByName("Location"))
        LDPMtetsDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMtetsData").getPropertyByName("Location"))
        LDPMfacetsDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMfacetsData").getPropertyByName("Location"))
        LDPMfacetsVerticesDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMfacetsVerticesData").getPropertyByName("Location"))
        LDPMfaceFacetsDataLoc = Path(App.getDocument(App.ActiveDocument.Name).getObject("LDPMfaceFacetsData").getPropertyByName("Location"))


        # Copy files to output directory
        shutil.copyfile(LDPMnodesDataLoc, outDir + outName + "/" + partName + "-data-nodes.dat")
        shutil.copyfile(LDPMtetsDataLoc, outDir + outName + "/" + partName + "-data-tets.dat")
        shutil.copyfile(LDPMfacetsDataLoc, outDir + outName + "/" + partName + "-data-facets.dat")
        shutil.copyfile(LDPMfacetsVerticesDataLoc, outDir + outName + "/" + partName + "-data-facetsVertices.dat")
        shutil.copyfile(LDPMfaceFacetsDataLoc, outDir + outName + "/" + partName + "-data-faceFacets.dat")


        materialProps = [\
            "Density",\
            "CompressiveStrength",\
            "ShearNormalCoupling",\
            "InitialHardeningModulusRatio",\
            "FinalHardeningModulusRatio",\
            "DensificationRatio",\
            "TransitionalStrainRatio",\
            "ShearTensileStrengthRatio",\
            "InitialInternalFrictionCoefficient",\
            "SofteningExponent",\
            "DeviatoricStrainRatio",\
            "DeviatoricDamage",\
            "FinalInternalFrictionCoefficient",\
            "TransitionalNormalStress",\
            "TensileStrength",\
            "TensileCharacteristicLength",\
            "NormalModulus",\
            ]
                
        materialPropsDesc = []
        
        materialPropsValues = []

        simProps = [\
            "TotalTime",\
            "TimestepSize",\
            "NumberOfThreads",\
            "NumberOutputSteps",\
            ]

        simPropsValues = []


        # Read material properties from model
        for x in range(len(materialProps)):
            materialPropsValues.append(App.getDocument(App.ActiveDocument.Name).getObject(materialName).getPropertyByName(materialProps[x]))


        # Read simulation properties from model
        for x in range(len(simProps)):
            simPropsValues.append(App.getDocument(App.ActiveDocument.Name).getObject(analysisName).getPropertyByName(simProps[x]))

        # Make Abaqus input file
        mkAbaqusInput(elementType, analysisName, materialProps, materialPropsDesc, materialPropsValues, simProps, simPropsValues, \
            nodesFilename, tetsFilename, facetsFilename, geoName, outDir, outName)

        
    # What to do when "Close" Button Clicked
    def reject(self):
        try:
            Gui.ActiveDocument.resetEdit()
            Gui.Control.closeDialog()
        except:
            Gui.Control.closeDialog()

        



class gen_LDPMCSL_Class():
    """My new command"""

    def GetResources(self):
        return {"Pixmap"  : os.path.join(ICONPATH, "ldpmOutput.svg"), # the name of a svg file available in the resources
                "MenuText": "LDPM Simulation Inputs",
                "ToolTip" : "Generation of LDPM simulation inputs"}

    def Activated(self):

        Gui.Control.showDialog(genWindow_LDPMCSL())

        return

    def IsActive(self):

        return True

Gui.addCommand("mod_LDPMCSL_gen", gen_LDPMCSL_Class())
