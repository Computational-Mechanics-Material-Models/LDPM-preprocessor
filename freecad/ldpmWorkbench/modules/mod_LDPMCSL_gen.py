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
## LDPMCSL generation
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
        self._bundle = None

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_LDPMCSL_importBundle.ui"))
        self.form.append(cwloadUIfile("ui_LDPMCSL_writeSimInfo.ui"))
        self.form.append(cwloadUIfile("ui_LDPMCSL_writeSimFiles.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Import Mesh Bundle")
        self.form[1].setWindowTitle("Confirm Output")
        self.form[2].setWindowTitle("Write File")

        cwloadUIicon(self.form[0],"ldpmOutput.svg")
        cwloadUIicon(self.form[1],"ldpmOutput.svg")
        cwloadUIicon(self.form[2],"ldpmOutput.svg")


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
        self.form[2].outputDir.setText(str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench')))

        # Try to see if there is a material object in the document
        try:
            test = App.ActiveDocument.getObject("LDPMmaterial")
            self.elementType = "LDPM"
        except:
            try:
                test = App.ActiveDocument.getObject("CSLmaterial")
                self.elementType = "CSL"
            except:
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
                try:
                    femesh=App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(meshName)[0]
                    numNodes = femesh.FemMesh.NodeCount
                    numElements = femesh.FemMesh.TetraCount
                except Exception:
                    continue
                modelInfo.append("Part " + str(i))
                modelInfo.append("Number of Nodes: " + str(numNodes))
                modelInfo.append("Number of Tets: " + str(numElements))
        elif self.elementType == "CSL":
            for i in range(self.numPartsCSL):
                meshName = self.elementType + "mesh" + str(i).zfill(3)
                try:
                    femesh=App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(meshName)[0]
                    numNodes = femesh.FemMesh.NodeCount
                    numElements = femesh.FemMesh.TetraCount
                except Exception:
                    continue
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
        self._documentInfo = modelInfoStr
        self.form[1].statusWindow.setText(modelInfoStr)

        QtCore.QObject.connect(self.form[0].bundleButton, QtCore.SIGNAL("clicked()"), self.importBundle)
        QtCore.QObject.connect(self.form[2].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)
        QtCore.QObject.connect(self.form[2].writeChrono, QtCore.SIGNAL("clicked()"), self.chronoGeneration)
        QtCore.QObject.connect(self.form[2].writeAbaqus, QtCore.SIGNAL("clicked()"), self.abaqusGeneration)


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
            self.form[2].outputDir.setText(OpenName)

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
        outDir =  self.form[2].outputDir.text()
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



    def _find_bundle_file(self, folder, suffix):
        matches = sorted(Path(folder).glob("*" + suffix))
        if not matches:
            return None
        return str(matches[0])

    def _scan_bundle(self, folder):
        names = (
            ("nodes", "-data-nodes.dat"),
            ("tets", "-data-tets.dat"),
            ("facets", "-data-facets.dat"),
            ("facetsVertices", "-data-facetsVertices.dat"),
            ("faceFacets", "-data-faceFacets.dat"),
            ("reinforcement", "-data-reinforcement.dat"),
            ("fiber", "-data-fiberfacet.dat"),
        )
        found = {}
        for key, suffix in names:
            path = self._find_bundle_file(folder, suffix)
            if path:
                found[key] = path
        return found

    def _count_rows(self, path):
        count = 0
        if not path or not os.path.isfile(path):
            return 0
        with open(path) as handle:
            for line in handle:
                text = line.strip()
                if text == "" or text.startswith("//") or text.startswith("#"):
                    continue
                count += 1
        return count

    def importBundle(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Import mesh bundle", App.ConfigGet("UserHomePath"), QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder == "":
            App.Console.PrintMessage("Process aborted\n")
            return
        found = self._scan_bundle(folder)
        if "nodes" not in found or "tets" not in found:
            App.Console.PrintError("Mesh bundle needs a nodes file and a tets file.\n")
            return
        self._bundle = {"folder": folder, "files": found}
        self.form[0].bundlePath.setText(folder)
        self.form[1].statusWindow.setText(self._bundle_report(found))
        App.Console.PrintMessage("Mesh bundle imported: %s\n" % folder)
        for note in self._bundle_notes(found):
            App.Console.PrintMessage(note + "\n")

    def _bundle_notes(self, found):
        notes = []
        if "facets" in found and self._facet_flag_count(found["facets"]) > 1:
            notes.append("Interfaces included")
        if "reinforcement" in found:
            notes.append("Reinforcement included")
        if "fiber" in found:
            notes.append("Fibers included")
        return notes

    def _facet_flag_count(self, path):
        flags = set()
        with open(path) as handle:
            for line in handle:
                text = line.strip()
                if text == "" or text.startswith("//") or text.startswith("#"):
                    continue
                parts = text.split()
                if len(parts) < 19:
                    continue
                mf_col = 23 if len(parts) in (24, 27) else 18
                if mf_col >= len(parts):
                    continue
                try:
                    flags.add(int(round(float(parts[mf_col]))))
                except ValueError:
                    continue
                if len(flags) > 1:
                    return len(flags)
        return len(flags)

    def _bundle_report(self, found):
        lines = ["Imported mesh bundle"]
        lines.append("Nodes: %d" % self._count_rows(found.get("nodes")))
        lines.append("Tets: %d" % self._count_rows(found.get("tets")))
        if "facets" in found:
            lines.append("Facets: %d" % self._count_rows(found.get("facets")))
        return "".join("<p>%s</p>" % line for line in lines)

    def _set_write_status(self, text, progress):
        message = "Status: " + str(text)
        try:
            self.form[2].statusWindow.setText(message)
            self.form[2].progressBar.setValue(int(progress))
        except Exception:
            pass
        App.Console.PrintMessage(message + "\n")
        try:
            Gui.updateGui()
        except Exception:
            pass

    def abaqusGeneration(self):
        bundle = self._bundle
        if bundle is None and self.elementType != "LDPM":
            self._set_write_status("No LDPM material found, and no mesh bundle is imported.", 0)
            return
        if bundle is None and self.elementType == "CSL":
            self._set_write_status("CSL element not yet supported for Abaqus.", 0)
            return

        self._set_write_status("Writing Abaqus input.", 15)
        partName = 'LDPMgeo000'
        elementType = "LDPM" if bundle is not None else self.elementType
        nodesFilename = partName + "-data-nodes.dat"
        tetsFilename = partName + "-data-tets.dat"
        facetsFilename = partName + "-data-facets.dat"
        outDir = self.form[2].outputDir.text()
        try:
            os.mkdir(outDir)
        except Exception:
            pass

        i = 0
        outName = '/' + "abaqusPackage" + elementType + str(i).zfill(3)
        while os.path.isdir(Path(outDir + outName)):
            i = i + 1
            outName = '/' + "abaqusPackage" + elementType + str(i).zfill(3)
        try:
            os.mkdir(outDir + outName)
        except Exception:
            pass

        analysisName = elementType + "analysis"
        geoName = elementType + "geo" + str(0).zfill(3)
        package = Path(outDir + outName)

        if bundle is not None:
            sources = bundle["files"]
        else:
            doc = App.getDocument(App.ActiveDocument.Name)
            sources = {
                "nodes": str(doc.getObject("LDPMnodesData").Location),
                "tets": str(doc.getObject("LDPMtetsData").Location),
                "facets": str(doc.getObject("LDPMfacetsData").Location),
            }
            vertices = doc.getObject("LDPMfacetsVerticesData")
            faces = doc.getObject("LDPMfaceFacetsData")
            reinf = doc.getObject("LDPMreinfData")
            if vertices is not None:
                sources["facetsVertices"] = str(vertices.Location)
            if faces is not None:
                sources["faceFacets"] = str(faces.Location)
            if reinf is not None:
                sources["reinforcement"] = str(reinf.Location)
            fiber = self._find_bundle_file(Path(sources["nodes"]).parent, "-data-fiberfacet.dat")
            if fiber:
                sources["fiber"] = fiber

        copy_names = {
            "nodes": nodesFilename,
            "tets": tetsFilename,
            "facets": facetsFilename,
            "facetsVertices": partName + "-data-facetsVertices.dat",
            "faceFacets": partName + "-data-faceFacets.dat",
            "reinforcement": partName + "-data-reinforcement.dat",
            "fiber": partName + "-data-fiberfacet.dat",
        }
        copied = {}
        for key, dest_name in copy_names.items():
            src = sources.get(key)
            if not src or not os.path.isfile(src):
                continue
            dest = package / dest_name
            shutil.copyfile(src, str(dest))
            copied[key] = str(dest)

        self._set_write_status("Mesh files copied.", 55)
        materialProps = []
        materialPropsDesc = []
        materialPropsValues = []
        simProps = []
        simPropsValues = []

        try:
            mkAbaqusInput(
                elementType, analysisName, materialProps, materialPropsDesc, materialPropsValues,
                simProps, simPropsValues, nodesFilename, tetsFilename, facetsFilename, geoName, outDir, outName,
                facetPath=copied.get("facets"),
                reinforcementPath=copied.get("reinforcement"),
                fiberPath=copied.get("fiber"),
            )
        except Exception as exc:
            self._set_write_status("ERROR - %s" % exc, 0)
            App.Console.PrintError("Abaqus input failed: %s\n" % exc)
            return
        inp_path = str(package / (geoName + "-mesh.inp"))
        notes = []
        if "facets" in copied and self._facet_flag_count(copied["facets"]) > 1:
            notes.append("Interfaces included")
        if "reinforcement" in copied:
            notes.append("Reinforcement included")
        if "fiber" in copied:
            notes.append("Fibers included")
        for note in notes:
            App.Console.PrintMessage(note + "\n")
        done = "Abaqus input written: " + inp_path
        if notes:
            done = done + " (" + ", ".join(notes) + ")"
        self._set_write_status(done, 100)

        
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
