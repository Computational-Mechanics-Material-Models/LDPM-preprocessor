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
##
## Description coming soon...
##
## ===========================================================================

# pyright: reportMissingImports=false

# Importing: standard
import os
import sys
import time
import tempfile
import numpy as np
from pathlib import Path
import multiprocessing
import functools
import math
import ast

# Importing: FreeCAD
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
from freecad.ldpmWorkbench.generation.driver_LDPMCSL                    import driver_LDPMCSL
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_tesselation           import gen_LDPMCSL_tesselation
from freecad.ldpmWorkbench.generation.gen_LDPM_facetData                import gen_LDPM_facetData
from freecad.ldpmWorkbench.generation.gen_LDPM_debugTet                 import gen_LDPM_debugTet
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_analysis              import gen_LDPMCSL_analysis


# Importing: input
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs                    import read_LDPMCSL_inputs, GEOMETRY_FILE_DIALOG_FILTER

# Importing: output
from freecad.ldpmWorkbench.output.mkVtk_particles                       import mkVtk_particles
from freecad.ldpmWorkbench.output.mkVtk_LDPMCSL_facets                  import mkVtk_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkVtk_LDPM_singleTet                  import mkVtk_LDPM_singleTet
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleDebugParaview         import mkPy_LDPM_singleDebugParaview
from freecad.ldpmWorkbench.output.mkPy_LDPM_singleDebugParaviewLabels   import mkPy_LDPM_singleDebugParaviewLabels
from freecad.ldpmWorkbench.output.mkData_nodes                          import mkData_nodes
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_tets                   import mkData_LDPMCSL_tets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facets                 import mkData_LDPMCSL_facets
from freecad.ldpmWorkbench.output.mkData_LDPMCSL_facetsVertices         import mkData_LDPMCSL_facetsVertices
from freecad.ldpmWorkbench.output.mkData_particles                      import mkData_particles
from freecad.ldpmWorkbench.output.mkParameters                          import mkParameters



# Turn off error for divide by zero and invalid operations
np.seterr(divide='ignore', invalid='ignore')



from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep import configure_multiprocessing_for_freecad
configure_multiprocessing_for_freecad()



class inputWindow_PLDPM:
    def __init__(self):

        self.form = []

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_PLDPM_modelProps.ui"))
        self.form.append(cwloadUIfile("ui_PLDPM_geometry.ui"))
        self.form.append(cwloadUIfile("ui_PLDPM_particles.ui"))        
        self.form.append(cwloadUIfile("ui_PLDPM_mixDesign.ui"))          
        self.form.append(cwloadUIfile("ui_PLDPM_additionalPara.ui"))
        self.form.append(cwloadUIfile("ui_PLDPM_generation.ui"))
        self.form.append(cwloadUIfile("ui_PLDPM_debugging.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Model Settings")
        self.form[1].setWindowTitle("Geometry")
        self.form[2].setWindowTitle("Particles")        
        self.form[3].setWindowTitle("Mix Design")
        self.form[4].setWindowTitle("Multimaterial Parameters")
        self.form[5].setWindowTitle("Model Generation")
        self.form[6].setWindowTitle("Generate Single Tet")

        cwloadUIicon(self.form[0],"FEM_MaterialMechanicalNonlinear.svg")
        cwloadUIicon(self.form[1],"PartDesign_AdditiveBox.svg")
        cwloadUIicon(self.form[2],"Arch_Material_Group.svg")
        cwloadUIicon(self.form[3],"FEM_ConstraintFlowVelocity.svg")
        cwloadUIicon(self.form[4],"PartDesign_MultiTransform.svg")
        cwloadUIicon(self.form[5],"p-ldpm.svg")
        cwloadUIicon(self.form[6],"PartDesign_Sprocket.svg")

        # Set initial output directory
        self.form[5].outputDir.setText(str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench')))
        
        # Initialize sketch list for path
        self.updatePathSketchList()

        # Connect selectObject and deselectObject Button in the Geometry Tab
        QtCore.QObject.connect(self.form[1].selectObjectButton, QtCore.SIGNAL("clicked()"), self.selectGeometry)
        QtCore.QObject.connect(self.form[1].deselectObjectButton, QtCore.SIGNAL("clicked()"), self.deselectGeometry)

        # Connect Open File Buttons
        QtCore.QObject.connect(self.form[0].readFileButton, QtCore.SIGNAL("clicked()"), self.openFilePara)
        QtCore.QObject.connect(self.form[1].readFileButton, QtCore.SIGNAL("clicked()"), self.openFileGeo)
        if hasattr(self.form[1], 'readProfileFileButton'):
            QtCore.QObject.connect(self.form[1].readProfileFileButton, QtCore.SIGNAL("clicked()"), self.openProfileFile)
        if hasattr(self.form[1], 'readPathFileButton'):
            QtCore.QObject.connect(self.form[1].readPathFileButton, QtCore.SIGNAL("clicked()"), self.openPathFile)
        if hasattr(self.form[1], 'createSketchButton'):
            QtCore.QObject.connect(self.form[1].createSketchButton, QtCore.SIGNAL("clicked()"), self.createPathSketch)
        if hasattr(self.form[1], 'selectSketchButton'):
            QtCore.QObject.connect(self.form[1].selectSketchButton, QtCore.SIGNAL("clicked()"), self.selectPathSketch)
        if hasattr(self.form[1], 'sweep3dpPathType'):
            QtCore.QObject.connect(self.form[1].sweep3dpPathType, QtCore.SIGNAL("currentIndexChanged(int)"), self.updatePathSketchList)
        if hasattr(self.form[1], 'sweep3dpPathSketch'):
            QtCore.QObject.connect(self.form[1].sweep3dpPathSketch, QtCore.SIGNAL("currentIndexChanged(int)"), self.onPathSketchSelected)
        if hasattr(self.form[1], 'sweep3dpNumSlicesRaster'):
            QtCore.QObject.connect(self.form[1].sweep3dpNumSlicesRaster, QtCore.SIGNAL("valueChanged(int)"), self.onRasterNumSlicesChanged)
        QtCore.QObject.connect(self.form[5].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)
        if hasattr(self.form[4], 'readMultiMatFile'):
            QtCore.QObject.connect(self.form[4].readMultiMatFile, QtCore.SIGNAL("clicked()"), self.openMultiMatFile)
        if hasattr(self.form[4], 'readAggFile'):
            QtCore.QObject.connect(self.form[4].readAggFile, QtCore.SIGNAL("clicked()"), self.openAggFile)
        if hasattr(self.form[1], 'sweep3dpNumSlicesRaster'):
            self.onRasterNumSlicesChanged(self.form[1].sweep3dpNumSlicesRaster.value())
        if hasattr(self.form[2], 'phaseSelect'):
            QtCore.QObject.connect(self.form[2].phaseSelect, QtCore.SIGNAL("currentIndexChanged(int)"), self.onPhaseSelectChanged)
            self.onPhaseSelectChanged(self.form[2].phaseSelect.currentIndex())
        if hasattr(self.form[4], 'multiMatPhaseSelect'):
            QtCore.QObject.connect(self.form[4].multiMatPhaseSelect, QtCore.SIGNAL("currentIndexChanged(int)"), self.onMultiMatPhaseChanged)
            self.onMultiMatPhaseChanged(self.form[4].multiMatPhaseSelect.currentIndex())
        if hasattr(self.form[3], 'mixPhaseSelect'):
            QtCore.QObject.connect(self.form[3].mixPhaseSelect, QtCore.SIGNAL("currentIndexChanged(int)"), self.onMixPhaseSelectChanged)
            self.onMixPhaseSelectChanged(self.form[3].mixPhaseSelect.currentIndex())

        # Run generation for LDPM or CSL
        QtCore.QObject.connect(self.form[5].generate, QtCore.SIGNAL("clicked()"), self.generationDriver)
        QtCore.QObject.connect(self.form[5].generateFast, QtCore.SIGNAL("clicked()"), self.generationDriverFast)
        QtCore.QObject.connect(self.form[5].externalGenerate, QtCore.SIGNAL("clicked()"), self.generationDriverExternal)
        QtCore.QObject.connect(self.form[5].writePara, QtCore.SIGNAL("clicked()"), self.writeParameters)

        # Run debugging generation of single tetrahedron
        QtCore.QObject.connect(self.form[6].generate_reg, QtCore.SIGNAL("clicked()"), self.debugGenerateRegTet)
        QtCore.QObject.connect(self.form[6].generate_irreg, QtCore.SIGNAL("clicked()"), self.debugGenerateIrregTet)







    def generationDriver(self):

        # Make a temporary path location
        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = False
        mkParameters(self,"LDPMCSL",tempPath,module="PLDPM")
        
        try:
            driver_LDPMCSL(self,fastGen,tempPath)
        except RuntimeError as e:
            # Catch RuntimeError from particle placement failures
            print(f"Generation failed: {e}")
            App.Console.PrintError(f"Generation failed: {e}\n")
            # Update UI to show error
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)
        except Exception as e:
            App.Console.PrintError(f"Generation failed: {e}\n")
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)

    def generationDriverFast(self):

        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = True
        mkParameters(self,"LDPMCSL",tempPath,module="PLDPM")

        try:
            driver_LDPMCSL(self,fastGen,tempPath)
        except RuntimeError as e:
            print(f"Generation failed: {e}")
            App.Console.PrintError(f"Generation failed: {e}\n")
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)
        except Exception as e:
            App.Console.PrintError(f"Generation failed: {e}\n")
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)


    def generationDriverExternal(self):

        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        mkParameters(self,"LDPMCSL",tempPath,module="PLDPM")
        try:
            App.Console.PrintMessage("Parameters written to file\n")
            App.Console.PrintMessage("External generation has started...\n")
            QtWidgets.QApplication.processEvents()
        except Exception:
            pass

        try:
            driver_LDPMCSL(self, "external", tempPath)
        except RuntimeError as e:
            print(f"External generation failed: {e}")
            App.Console.PrintError(f"External generation failed: {e}\n")
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)
        except Exception as e:
            App.Console.PrintError(f"External generation failed: {e}\n")
            self.form[5].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[5].progressBar.setValue(0)


    def getStandardButtons(self):

        # Only show a close button (PySide2 int vs PySide6 enum)
        btn = QtWidgets.QDialogButtonBox.Close
        return btn.value if hasattr(btn, "value") else int(btn)

    def selectGeometry(self):
            
        # Select Geometry
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 0:
            App.Console.PrintMessage("Please select a geometry"+"\n")
        else:
            self.form[1].selectedObject.setText(sel[0].Name)

    def deselectGeometry(self):
                
        # Deselect Geometry
        self.form[1].selectedObject.setText("")


    def openFilePara(self):

        path = App.ConfigGet("UserHomePath")
        filetype = "CW Parameter input format (*.cwPar)"

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
        filetype = GEOMETRY_FILE_DIALOG_FILTER

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a geometry file", path, filetype
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].cadName.setText("Import geometry listed below")
            self.form[1].cadFile.setText(OpenName)

    def openProfileFile(self):

        path = App.ConfigGet("UserHomePath")
        filetype = (
            "DXF format        (*.dxf);;"
            "All Files         (*.*)"
        )

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a profile sketch file (DXF format only - must be closed loop)", path, filetype
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].sweep3dpProfileFileName.setText("Profile sketch file selected")
            self.form[1].sweep3dpProfileFile.setText(OpenName)

    def openPathFile(self):

        path = App.ConfigGet("UserHomePath")
        filetype = (
            "DXF format        (*.dxf);;"
            "All Files         (*.*)"
        )

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a path sketch file (DXF format only)", path, filetype
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].sweep3dpPathFileName.setText("Path sketch file selected")
            self.form[1].sweep3dpPathFile.setText(OpenName)

    def createPathSketch(self):
        try:
            import Sketcher
            Gui.activateWorkbench("SketcherWorkbench")
            sketch = App.ActiveDocument.addObject("Sketcher::SketchObject", "PathSketch")
            sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), 0))
            App.ActiveDocument.recompute()
            Gui.activeDocument().setEdit(sketch.Name)
            self.updatePathSketchList()
            self.form[1].sweep3dpPathSketch.setCurrentIndex(self.form[1].sweep3dpPathSketch.findText(sketch.Label))
            self.form[1].sweep3dpPathSketchName.setText(sketch.Name)
            App.Console.PrintMessage(f"Created new sketch: {sketch.Label}\n")
        except Exception as e:
            App.Console.PrintError(f"Failed to create sketch: {str(e)}\n")

    def selectPathSketch(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 0:
            App.Console.PrintMessage("Please select a sketch object from the document\n")
        else:
            obj = sel[0]
            if hasattr(obj, 'TypeId') and 'Sketch' in obj.TypeId:
                self.form[1].sweep3dpPathSketchName.setText(obj.Name)
                self.updatePathSketchList()
                idx = self.form[1].sweep3dpPathSketch.findText(obj.Label)
                if idx >= 0:
                    self.form[1].sweep3dpPathSketch.setCurrentIndex(idx)
                App.Console.PrintMessage(f"Selected sketch: {obj.Label}\n")
            else:
                App.Console.PrintError("Selected object is not a sketch. Please select a Sketcher sketch object.\n")

    def updatePathSketchList(self):
        if not hasattr(self.form[1], 'sweep3dpPathSketch'):
            return
        self.form[1].sweep3dpPathSketch.clear()
        if App.ActiveDocument:
            for obj in App.ActiveDocument.Objects:
                if hasattr(obj, 'TypeId') and 'Sketch' in obj.TypeId:
                    self.form[1].sweep3dpPathSketch.addItem(obj.Label, obj.Name)
        if self.form[1].sweep3dpPathType.currentIndex() == 4:
            current_name = self.form[1].sweep3dpPathSketchName.text()
            if current_name:
                idx = self.form[1].sweep3dpPathSketch.findData(current_name)
                if idx >= 0:
                    self.form[1].sweep3dpPathSketch.setCurrentIndex(idx)

    def onPathSketchSelected(self, index):
        if index >= 0 and hasattr(self.form[1], 'sweep3dpPathSketch'):
            sketch_name = self.form[1].sweep3dpPathSketch.itemData(index)
            if sketch_name:
                self.form[1].sweep3dpPathSketchName.setText(sketch_name)

    def onRasterNumSlicesChanged(self, value):
        for i in range(1, 9):
            label = getattr(self.form[1], f"sweep3dpSliceDirLabel{i}", None)
            box = getattr(self.form[1], f"sweep3dpSliceDir{i}", None)
            is_visible = i <= int(value)
            if label is not None:
                label.setVisible(is_visible)
            if box is not None:
                box.setVisible(is_visible)

    def onPhaseSelectChanged(self, index):
        if not hasattr(self.form[2], 'phaseContent'):
            return
        phase_map = {
            0: [],
            1: [1, 2],
            2: [1, 2, 3],
        }
        visible_phases = phase_map.get(index, [])
        self.form[2].phaseContent.setVisible(len(visible_phases) > 0)
        for n in range(1, 5):
            widget = getattr(self.form[2], f"phaseWidget{n}", None)
            if widget is not None:
                widget.setVisible(n in visible_phases)

        if hasattr(self.form[3], 'mixPhaseSelect'):
            if self.form[3].mixPhaseSelect.currentIndex() != index:
                self.form[3].mixPhaseSelect.blockSignals(True)
                self.form[3].mixPhaseSelect.setCurrentIndex(index)
                self.form[3].mixPhaseSelect.blockSignals(False)
            self.onMixPhaseSelectChanged(index)

        if hasattr(self.form[4], 'multiMatPhaseSelect') and index in (1, 2):
            mm_idx = {1: 0, 2: 1}[index]
            if self.form[4].multiMatPhaseSelect.currentIndex() != mm_idx:
                self.form[4].multiMatPhaseSelect.blockSignals(True)
                self.form[4].multiMatPhaseSelect.setCurrentIndex(mm_idx)
                self.form[4].multiMatPhaseSelect.blockSignals(False)
            self.onMultiMatPhaseChanged(mm_idx)

    def onMixPhaseSelectChanged(self, index):
        if not hasattr(self.form[3], 'mixPhaseContent'):
            return
        phase_map = {
            0: [],
            1: [1, 2],
            2: [1, 2, 3],
        }
        visible_phases = phase_map.get(index, [])
        self.form[3].mixPhaseContent.setVisible(len(visible_phases) > 0)
        for n in range(1, 5):
            widget = getattr(self.form[3], f"phaseMixWidget{n}", None)
            if widget is not None:
                widget.setVisible(n in visible_phases)

    def onMultiMatPhaseChanged(self, index):
        if not hasattr(self.form[4], 'phaseWidgetAgg'):
            return
        self.form[4].phaseWidgetAgg.setVisible(index in (0, 1))
        self.form[4].phaseWidgetITZ.setVisible(index == 1)
        self.form[4].phaseWidgetBinder.setVisible(index in (0, 1))
        if hasattr(self.form[4], 'label_phaseBinder'):
            if index == 0:
                self.form[4].label_phaseBinder.setText("Phase 2 - Mortar/Binder")
            elif index == 1:
                self.form[4].label_phaseBinder.setText("Phase 3 - Mortar/Binder")

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

    def openMultiMatFile(self):

        path = App.ConfigGet('UserHomePath')
        filetype = 'Voxel Data File (*.img)'

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Read a voxel data file', path, filetype
        )
        if OpenName == '':  # if the name file is not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[4].multiMatFile.setText(OpenName)

    def openAggFile(self):

        path = App.ConfigGet('UserHomePath')
        filetype = 'Voxel Data File (*.pimg)'

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Read a voxel data file', path, filetype
        )
        if OpenName == '':  # if the name file is not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[4].aggFile.setText(OpenName)

    def writeParameters(self):

        mkParameters(self,"LDPMCSL","writeOnly",module="PLDPM")

    # Read parameters from file and write to input panel in FreeCAD
    def readParameters(self):

        paraFile = self.form[0].setupFile.text()

        params = {}
        with open(Path(paraFile), "r") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("//"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                params[k.strip()] = v.strip()

        def _as_int(val, default=0):
            try:
                return int(str(val).strip())
            except Exception:
                return default

        def _as_float(val, default=0.0):
            try:
                return float(str(val).strip())
            except Exception:
                return default

        def _as_bool(val, default=False):
            try:
                s = str(val).strip().lower()
                if s in ["true", "1", "yes", "on"]:
                    return True
                if s in ["false", "0", "no", "off"]:
                    return False
            except Exception:
                pass
            return default

        def _as_list(val, default=None):
            if default is None:
                default = []
            try:
                parsed = ast.literal_eval(str(val).strip())
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            except Exception:
                pass
            return list(default)

        def _set_phase_combo(combo, mode, select_offset=False, default_index=0):
            if combo is None:
                return
            try:
                mode_i = int(mode)
            except Exception:
                combo.setCurrentIndex(default_index)
                return
            if select_offset:
                idx = {0: 0, 1: 0, 2: 1, 3: 2}.get(mode_i, default_index)
            else:
                idx = {2: 0, 3: 1}.get(mode_i, default_index)
            combo.setCurrentIndex(idx)

        constitutiveEQ = params.get("constitutiveEQ", self.form[0].constEQ.currentText())
        matParaSet = params.get("matParaSet", "")
        numCPU = _as_int(params.get("numCPU", self.form[0].numCPUbox.value()), default=self.form[0].numCPUbox.value())
        numIncrements = _as_int(params.get("numIncrements", self.form[0].numPIncBox.value()), default=self.form[0].numPIncBox.value())
        maxIter = _as_int(params.get("maxIter", self.form[0].numIncBox.value()), default=self.form[0].numIncBox.value())
        placementAlg = params.get("placementAlg", self.form[0].placementAlg.currentText())
        geoType = params.get("geoType", self.form[1].geometryType.currentText())
        if geoType == "Prism":
            geoType = "Arbitrary Prism"

        dimensions_raw = params.get("dimensions", "[]")
        dimensions = []
        if geoType == "Sweep-3DP":
            try:
                dimensions = ast.literal_eval(dimensions_raw)
            except Exception as e:
                print(f"Warning: Could not parse Sweep-3DP dimensions: {e}")
                dimensions = []
        else:
            try:
                dims_items = str(dimensions_raw).strip().strip("[").strip("]").split(",")
                for x in dims_items:
                    x_clean = x.strip().strip("'").strip('"')
                    if not x_clean:
                        continue
                    try:
                        dimensions.append(float(x_clean.split()[0]))
                    except Exception:
                        dimensions.append(x_clean)
            except Exception as e:
                print(f"Warning: Could not parse dimensions: {e}")
                dimensions = []

        cadFile = params.get("cadFile", "")
        minPar_sim = _as_float(params.get("minPar_sim", 0.0))
        maxPar_sim = _as_float(params.get("maxPar_sim", 0.0))
        minPar_exp = _as_float(params.get("minPar_exp", 0.0))
        maxPar_exp = _as_float(params.get("maxPar_exp", 0.0))
        fullerCoef = _as_float(params.get("fullerCoef", 0.0))
        sieveCurveDiameter = params.get("sieveCurveDiameter", "")
        sieveCurvePassing = params.get("sieveCurvePassing", "")
        wcRatio = _as_float(params.get("wcRatio", 0.0))
        densityWater = _as_float(params.get("densityWater", 0.0))
        cementC = _as_float(params.get("cementC", 0.0))
        flyashC = _as_float(params.get("flyashC", 0.0))
        silicaC = _as_float(params.get("silicaC", 0.0))
        scmC = _as_float(params.get("scmC", 0.0))
        cementDensity = _as_float(params.get("cementDensity", 0.0))
        flyashDensity = _as_float(params.get("flyashDensity", 0.0))
        silicaDensity = _as_float(params.get("silicaDensity", 0.0))
        scmDensity = _as_float(params.get("scmDensity", 0.0))
        airFrac1 = _as_float(params.get("airFrac1", 0.0))
        fillerC = _as_float(params.get("fillerC", 0.0))
        fillerDensity = _as_float(params.get("fillerDensity", 0.0))
        airFrac2 = _as_float(params.get("airFrac2", 0.0))

        htcToggle = params.get("htcToggle", "Off")
        htcLength = _as_float(params.get("htcLength", 0.0))

        multiMatToggle = params.get("multiMatToggle", "Off")
        aggFile = params.get("aggFile", "")
        multiMatFile = params.get("multiMatFile", "")
        multiMatRule = _as_int(params.get("multiMatRule", 9), default=9)

        grainAggMin = _as_float(params.get("grainAggMin", 0.0))
        grainAggMax = _as_float(params.get("grainAggMax", 0.0))
        grainAggFuller = _as_float(params.get("grainAggFuller", 0.0))
        grainAggSieveD = params.get("grainAggSieveD", "")
        grainAggSieveP = params.get("grainAggSieveP", "")

        grainITZMin = _as_float(params.get("grainITZMin", 0.0))
        grainITZMax = _as_float(params.get("grainITZMax", 0.0))
        grainITZFuller = _as_float(params.get("grainITZFuller", 0.0))
        grainITZSieveD = params.get("grainITZSieveD", "")
        grainITZSieveP = params.get("grainITZSieveP", "")

        grainBinderMin = _as_float(params.get("grainBinderMin", 0.0))
        grainBinderMax = _as_float(params.get("grainBinderMax", 0.0))
        grainBinderFuller = _as_float(params.get("grainBinderFuller", 0.0))
        grainBinderSieveD = params.get("grainBinderSieveD", "")
        grainBinderSieveP = params.get("grainBinderSieveP", "")

        phaseMode = _as_int(params.get("phaseMode", 3), default=3)

        mixPhaseMode = _as_int(params.get("mixPhaseMode", 0), default=0)
        phaseFillerContent = _as_list(params.get("phaseFillerContent", "[]"), default=[fillerC])
        phaseFillerDensity = _as_list(params.get("phaseFillerDensity", "[]"), default=[fillerDensity])

        particlePhaseMode = _as_int(params.get("particlePhaseMode", 0), default=0)
        phaseMinPar = _as_list(params.get("phaseMinPar", "[]"), default=[])
        phaseMaxPar = _as_list(params.get("phaseMaxPar", "[]"), default=[])
        phaseOffsetCoef = _as_list(params.get("phaseOffsetCoef", "[]"), default=[])
        particleOffsetCoef = _as_float(params.get("particleOffsetCoef", 0.2), default=0.2)
        periodicToggle = params.get("periodicToggle", "Off")

        outputDir = params.get("outputDir", self.form[5].outputDir.text())
        dataFilesGen = _as_bool(params.get("dataFilesGen", self.form[5].dataFilesGen.isChecked()), default=self.form[5].dataFilesGen.isChecked())
        visFilesGen = _as_bool(params.get("visFilesGen", self.form[5].visFilesGen.isChecked()), default=self.form[5].visFilesGen.isChecked())
        singleTetGen = _as_bool(params.get("singleTetGen", self.form[5].singleTetGen.isChecked()), default=self.form[5].singleTetGen.isChecked())
        modelType = params.get("modelType", self.form[5].modelType.currentText())

        # Write parameters to input panel
        self.form[0].constEQ.setCurrentText(constitutiveEQ)
        if self.form[0].constEQ.currentIndex() == 0:
            self.form[0].matParaSet4EQ1.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 1:
            self.form[0].matParaSet4EQ2.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 2:
            self.form[0].matParaSet4EQ3.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 3:
            self.form[0].matParaSet4EQ4.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 4:
            self.form[0].matParaSet4EQ5.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 5:
            self.form[0].matParaSet4EQ6.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 6:
            self.form[0].matParaSet4EQ7.setCurrentText(matParaSet)
        elif self.form[0].constEQ.currentIndex() == 7:
            self.form[0].matParaSet4EQ8.setCurrentText(matParaSet)
        self.form[0].numCPUbox.setValue(numCPU)
        self.form[0].numPIncBox.setValue(numIncrements)
        self.form[0].numIncBox.setValue(maxIter)
        self.form[0].placementAlg.setCurrentText(placementAlg)
        self.form[1].geometryType.setCurrentText(geoType)
        geo_idx = self.form[1].geometryType.currentIndex()
        if geo_idx >= 0 and hasattr(self.form[1], "widgetStack2"):
            self.form[1].widgetStack2.setCurrentIndex(geo_idx)
        if geoType == "Box":
            if len(dimensions) >= 3:
                self.form[1].boxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].boxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].boxHeight.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cylinder":
            if len(dimensions) >= 2:
                self.form[1].cylinderHeight.setProperty('rawValue',(dimensions[0]))
                self.form[1].cylinderRadius.setProperty('rawValue',(dimensions[1]))
        elif geoType == "Cone":
            if len(dimensions) >= 2:
                self.form[1].coneHeight.setProperty('rawValue',(dimensions[0]))
                self.form[1].coneRadius1.setProperty('rawValue',(dimensions[1]))
        elif geoType == "Sphere":
            if len(dimensions) >= 1:
                self.form[1].sphereRadius.setProperty('rawValue',(dimensions[0]))
        elif geoType == "Ellipsoid":
            if len(dimensions) >= 6:
                self.form[1].ellipsoidRadius1.setProperty('rawValue',(dimensions[0]))
                self.form[1].ellipsoidRadius2.setProperty('rawValue',(dimensions[1]))
                self.form[1].ellipsoidRadius3.setProperty('rawValue',(dimensions[2]))
                self.form[1].ellipsoidAngle1.setProperty('rawValue',(dimensions[3]))
                self.form[1].ellipsoidAngle2.setProperty('rawValue',(dimensions[4]))
                self.form[1].ellipsoidAngle3.setProperty('rawValue',(dimensions[5]))
        elif geoType == "Arbitrary Prism":
            if len(dimensions) >= 3:
                self.form[1].prismCircumradius.setProperty('rawValue',(dimensions[0]))
                self.form[1].prismHeight.setProperty('rawValue',(dimensions[1]))
                self.form[1].prismPolygon.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Notched Prism - Square":
            if len(dimensions) >= 5:
                self.form[1].notchBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchDepth.setProperty('rawValue',(dimensions[4]))
        elif geoType == "Notched Prism - Semi Circle":
            if len(dimensions) >= 5:
                self.form[1].notchSCBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchSCBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchSCBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchSCWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchSCDepth.setProperty('rawValue',(dimensions[4]))
        elif geoType == "Notched Prism - Semi Ellipse":
            if len(dimensions) >= 5:
                self.form[1].notchSEBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchSEBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchSEBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchSEWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchSEDepth.setProperty('rawValue',(dimensions[4]))
            if len(dimensions) >= 6:
                self.form[1].notchSEtipDepth.setProperty('rawValue',(dimensions[5]))
        elif geoType == "Dogbone":
            if len(dimensions) >= 6:
                self.form[1].dogboneLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].dogboneWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].dogboneThickness.setProperty('rawValue',(dimensions[2]))
                self.form[1].gaugeLength.setProperty('rawValue',(dimensions[3]))
                self.form[1].gaugeWidth.setProperty('rawValue',(dimensions[4]))
                self.form[1].dogboneType.setCurrentText(str(dimensions[5]))
        elif geoType == "Custom":
            if len(dimensions) >= 1 and hasattr(self.form[1], "selectedObject"):
                self.form[1].selectedObject.setText(str(dimensions[0]))
        elif geoType == "Import CAD or Mesh":
            if cadFile:
                if hasattr(self.form[1], "cadName"):
                    self.form[1].cadName.setText("Import geometry listed below")
                self.form[1].cadFile.setText(cadFile)
        elif geoType == "Sweep-3DP":
            try:
                profileTypeIdx = _as_int(dimensions[0], default=0) if len(dimensions) > 0 else 0
                layerWidth = str(dimensions[1]) if len(dimensions) > 1 else ""
                layerHeight = str(dimensions[2]) if len(dimensions) > 2 else ""
                profileFile = str(dimensions[3]) if len(dimensions) > 3 else ""
                pathTypeIdx = _as_int(dimensions[4], default=0) if len(dimensions) > 4 else 0
                distTxt = str(dimensions[5]) if len(dimensions) > 5 else ""
                diaTxt = str(dimensions[6]) if len(dimensions) > 6 else ""
                sideTxt = str(dimensions[7]) if len(dimensions) > 7 else ""
                cadPath = str(dimensions[8]) if len(dimensions) > 8 else ""
                sketchName = str(dimensions[9]) if len(dimensions) > 9 else ""
                numLayersTxt = str(dimensions[10]) if len(dimensions) > 10 else "1"
                numLayers = _as_int(numLayersTxt, default=1)
                if hasattr(self.form[1], "sweep3dpProfileType"):
                    self.form[1].sweep3dpProfileType.setCurrentIndex(profileTypeIdx)
                if profileTypeIdx == 0:
                    if hasattr(self.form[1], "sweep3dpLayerWidth") and layerWidth:
                        self.form[1].sweep3dpLayerWidth.setText(layerWidth)
                    if hasattr(self.form[1], "sweep3dpLayerHeight") and layerHeight:
                        self.form[1].sweep3dpLayerHeight.setText(layerHeight)
                else:
                    if hasattr(self.form[1], "sweep3dpProfileFile") and profileFile:
                        self.form[1].sweep3dpProfileFile.setText(profileFile)
                        if hasattr(self.form[1], "sweep3dpProfileFileName"):
                            self.form[1].sweep3dpProfileFileName.setText("Profile sketch file selected")

                if hasattr(self.form[1], "sweep3dpPathType"):
                    self.form[1].sweep3dpPathType.setCurrentIndex(pathTypeIdx)
                if pathTypeIdx == 0 and hasattr(self.form[1], "sweep3dpPathDistance") and distTxt:
                    self.form[1].sweep3dpPathDistance.setText(distTxt)
                    if hasattr(self.form[1], "sweep3dpNumLayers"):
                        self.form[1].sweep3dpNumLayers.setValue(numLayers)
                elif pathTypeIdx == 1 and hasattr(self.form[1], "sweep3dpPathDiameter") and diaTxt:
                    self.form[1].sweep3dpPathDiameter.setText(diaTxt)
                    if hasattr(self.form[1], "sweep3dpNumLayersCircle"):
                        self.form[1].sweep3dpNumLayersCircle.setValue(numLayers)
                elif pathTypeIdx == 2 and hasattr(self.form[1], "sweep3dpPathSide") and sideTxt:
                    self.form[1].sweep3dpPathSide.setText(sideTxt)
                    if hasattr(self.form[1], "sweep3dpNumLayersSquare"):
                        self.form[1].sweep3dpNumLayersSquare.setValue(numLayers)
                elif pathTypeIdx == 3 and hasattr(self.form[1], "sweep3dpPathFile") and cadPath:
                    self.form[1].sweep3dpPathFile.setText(cadPath)
                    if hasattr(self.form[1], "sweep3dpPathFileName"):
                        self.form[1].sweep3dpPathFileName.setText("Path sketch file selected")
                    if hasattr(self.form[1], "sweep3dpNumLayersCAD"):
                        self.form[1].sweep3dpNumLayersCAD.setValue(numLayers)
                elif pathTypeIdx == 4:
                    if hasattr(self.form[1], "sweep3dpPathSketchName"):
                        self.form[1].sweep3dpPathSketchName.setText(sketchName)
                    try:
                        self.updatePathSketchList()
                    except Exception:
                        pass
                    if hasattr(self.form[1], "sweep3dpNumLayersSketch"):
                        self.form[1].sweep3dpNumLayersSketch.setValue(numLayers)
                elif pathTypeIdx == 5:
                    rasterLoops = _as_int(str(dimensions[11]), default=1) if len(dimensions) > 11 else 1
                    rasterSpacing = str(dimensions[12]) if len(dimensions) > 12 else "5 mm"
                    rasterSlices = _as_int(str(dimensions[13]), default=numLayers) if len(dimensions) > 13 else numLayers
                    rasterCornerFillet = str(dimensions[22]) if len(dimensions) > 22 else "0 mm"
                    rasterPathLength = str(dimensions[23]) if len(dimensions) > 23 else "100 mm"
                    if hasattr(self.form[1], "sweep3dpRasterLoops"):
                        self.form[1].sweep3dpRasterLoops.setValue(max(1, rasterLoops))
                    if hasattr(self.form[1], "sweep3dpRasterSpacing"):
                        self.form[1].sweep3dpRasterSpacing.setText(rasterSpacing)
                    if hasattr(self.form[1], "sweep3dpRasterCornerFillet"):
                        self.form[1].sweep3dpRasterCornerFillet.setText(rasterCornerFillet)
                    if hasattr(self.form[1], "sweep3dpRasterPathLength"):
                        self.form[1].sweep3dpRasterPathLength.setText(rasterPathLength)
                    if hasattr(self.form[1], "sweep3dpNumSlicesRaster"):
                        self.form[1].sweep3dpNumSlicesRaster.setValue(max(1, min(8, rasterSlices)))
                    default_dirs = [0.0, 90.0, 0.0, 90.0, 0.0, 90.0, 0.0, 90.0]
                    for i in range(8):
                        idx = 14 + i
                        val = _as_float(str(dimensions[idx]), default=default_dirs[i]) if len(dimensions) > idx else default_dirs[i]
                        box = getattr(self.form[1], f"sweep3dpSliceDir{i+1}", None)
                        if box is not None:
                            box.setValue(val)
                    if hasattr(self.form[1], "sweep3dpNumSlicesRaster"):
                        self.onRasterNumSlicesChanged(self.form[1].sweep3dpNumSlicesRaster.value())
            except Exception as e:
                print(f"Warning: Could not apply Sweep-3DP dimensions: {e}")
        self.form[1].cadFile.setText(cadFile)
        if hasattr(self.form[2], 'minPar_sim'):
            self.form[2].minPar_sim.setValue(minPar_sim)
            self.form[2].maxPar_sim.setValue(maxPar_sim)
        elif hasattr(self.form[2], 'phase1MinPar'):
            if hasattr(self.form[2], 'phaseSelect'):
                _set_phase_combo(self.form[2].phaseSelect, particlePhaseMode, select_offset=True, default_index=0)
                self.onPhaseSelectChanged(self.form[2].phaseSelect.currentIndex())
            for n in range(1, 5):
                i = n - 1
                wmin = getattr(self.form[2], f"phase{n}MinPar", None)
                wmax = getattr(self.form[2], f"phase{n}MaxPar", None)
                woff = getattr(self.form[2], f"phase{n}OffsetCoef", None)
                if wmin is not None:
                    if i < len(phaseMinPar):
                        wmin.setValue(_as_float(phaseMinPar[i], minPar_sim if n == 1 else 0.0))
                    elif n == 1:
                        wmin.setValue(minPar_sim)
                if wmax is not None:
                    if i < len(phaseMaxPar):
                        wmax.setValue(_as_float(phaseMaxPar[i], maxPar_sim if n == 1 else 0.0))
                    elif n == 1:
                        wmax.setValue(maxPar_sim)
                if woff is not None:
                    if i < len(phaseOffsetCoef):
                        woff.setValue(_as_float(phaseOffsetCoef[i], particleOffsetCoef))
                    else:
                        woff.setValue(particleOffsetCoef)
        if hasattr(self.form[2], 'particleOffsetCoef'):
            self.form[2].particleOffsetCoef.setValue(particleOffsetCoef)
        self.form[3].minPar_exp.setValue(minPar_exp)
        self.form[3].maxPar_exp.setValue(maxPar_exp)
        self.form[3].fullerCoef.setValue(fullerCoef)
        self.form[3].sieveDiameters.setText(str(sieveCurveDiameter))
        self.form[3].sievePassing.setText(str(sieveCurvePassing))
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
        if hasattr(self.form[3], 'airFracArb'):
            self.form[3].airFracArb.setValue(airFrac2)
        if hasattr(self.form[3], 'mixPhaseSelect'):
            _mix_mode = particlePhaseMode if particlePhaseMode in (2, 3) else mixPhaseMode
            _set_phase_combo(self.form[3].mixPhaseSelect, _mix_mode, select_offset=True, default_index=0)
            self.onMixPhaseSelectChanged(self.form[3].mixPhaseSelect.currentIndex())
        phaseFillerVolFrac = _as_list(params.get("phaseFillerVolFrac", "[]"), default=[])
        if not phaseFillerVolFrac and phaseFillerContent:
            for i, c in enumerate(phaseFillerContent):
                d = phaseFillerDensity[i] if i < len(phaseFillerDensity) else 0.0
                if d and abs(d - 1.0) > 1e-12:
                    phaseFillerVolFrac.append(float(c) / float(d))
                else:
                    v = float(c)
                    phaseFillerVolFrac.append(v / 100.0 if v > 1.0 else v)
        if hasattr(self.form[3], 'fillerVolFrac'):
            if len(phaseFillerVolFrac) > 0:
                self.form[3].fillerVolFrac.setValue(_as_float(phaseFillerVolFrac[0], 0.0))
            for n in range(2, 5):
                i = n - 1
                wvf = getattr(self.form[3], f"phase{n}FillerVolFrac", None)
                if wvf is not None and i < len(phaseFillerVolFrac):
                    wvf.setValue(_as_float(phaseFillerVolFrac[i], 0.0))
        elif hasattr(self.form[3], 'fillerContent'):
            self.form[3].fillerContent.setText(str(fillerC))
            self.form[3].fillerDensity.setText(str(fillerDensity))
            if len(phaseFillerContent) > 0:
                self.form[3].fillerContent.setText(str(phaseFillerContent[0]))
            if len(phaseFillerDensity) > 0:
                self.form[3].fillerDensity.setText(str(phaseFillerDensity[0]))
            for n in range(2, 5):
                i = n - 1
                wfc = getattr(self.form[3], f"phase{n}FillerContent", None)
                wfd = getattr(self.form[3], f"phase{n}FillerDensity", None)
                if wfc is not None and i < len(phaseFillerContent):
                    wfc.setText(str(phaseFillerContent[i]))
                if wfd is not None and i < len(phaseFillerDensity):
                    wfd.setText(str(phaseFillerDensity[i]))
        if hasattr(self.form[4], 'HTCtoggle'):
            self.form[4].HTCtoggle.setCurrentText(htcToggle)
        if hasattr(self.form[4], 'HTClength'):
            self.form[4].HTClength.setValue(htcLength)
        for form_item in self.form:
            if hasattr(form_item, "periodicToggle"):
                form_item.periodicToggle.setCurrentText(periodicToggle)
                break
        if multiMatToggle == "On":
            self.form[4].widgetStack2.setCurrentIndex(0)
        self.form[4].multiMatToggle.setCurrentText(multiMatToggle)
        self.form[4].aggFile.setText(aggFile)
        self.form[4].multiMatFile.setText(multiMatFile)
        self.form[4].multiMatRule.setValue(int(multiMatRule))
        self.form[4].grainAggMin.setValue(grainAggMin)
        self.form[4].grainAggMax.setValue(grainAggMax)
        self.form[4].grainAggFuller.setValue(grainAggFuller)
        self.form[4].grainAggSieveD.setText(str(grainAggSieveD))
        self.form[4].grainAggSieveP.setText(str(grainAggSieveP))
        self.form[4].grainITZMin.setValue(grainITZMin)
        self.form[4].grainITZMax.setValue(grainITZMax)
        self.form[4].grainITZFuller.setValue(grainITZFuller)
        self.form[4].grainITZSieveD.setText(str(grainITZSieveD))
        self.form[4].grainITZSieveP.setText(str(grainITZSieveP))
        self.form[4].grainBinderMin.setValue(grainBinderMin)
        self.form[4].grainBinderMax.setValue(grainBinderMax)
        self.form[4].grainBinderFuller.setValue(grainBinderFuller)
        self.form[4].grainBinderSieveD.setText(str(grainBinderSieveD))
        self.form[4].grainBinderSieveP.setText(str(grainBinderSieveP))
        if hasattr(self.form[4], 'multiMatPhaseSelect'):
            _mm_mode = particlePhaseMode if particlePhaseMode in (2, 3) else phaseMode
            _set_phase_combo(self.form[4].multiMatPhaseSelect, _mm_mode, select_offset=False, default_index=1)
            self.onMultiMatPhaseChanged(self.form[4].multiMatPhaseSelect.currentIndex())
        self.form[5].outputDir.setText(outputDir)
        if hasattr(self.form[5], "dataFilesGen"):
            self.form[5].dataFilesGen.setChecked(bool(dataFilesGen))
        if hasattr(self.form[5], "visFilesGen"):
            self.form[5].visFilesGen.setChecked(bool(visFilesGen))
        if hasattr(self.form[5], "singleTetGen"):
            self.form[5].singleTetGen.setChecked(bool(singleTetGen))
        if hasattr(self.form[5], "modelType"):
            self.form[5].modelType.setCurrentText(modelType)


    def debugGenerateRegTet(self):

        self.debugGenerateTet("Regular")

    def debugGenerateIrregTet(self):

        self.debugGenerateTet("Irregular")


    def debugGenerateTet(self,type):


        # Make output directory if does not exist
        outDir =  self.form[5].outputDir.text()
        try:
            os.mkdir(outDir)
        except:
            pass

        # Make a temporary path location
        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        # Store document
        docGui = Gui.activeDocument()

        # Make new document and set view if does not exisit
        try:
            docGui.activeView().viewAxonometric()
        except:
            App.newDocument("Unnamed")
            docGui = Gui.activeDocument()
            docGui.activeView().viewAxonometric()
        Gui.runCommand('Std_PerspectiveCamera',1)

        # Read in inputs from input panel just to get location for file output
        [setupFile, constitutiveEQ, matParaSet, \
            numCPU, numIncrements,maxIter,placementAlg,\
            geoType, dimensions, cadFile,\
            minPar_sim, maxPar_sim,minPar_exp, maxPar_exp, fullerCoef, sieveCurveDiameter, sieveCurvePassing,\
            wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
            cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
            fillerC, fillerDensity, airFrac2,\
            htcToggle, htcLength,\
            _, _, _, _, _, _, _, _, _, _, _, _,\
            multiMatToggle,aggFile,multiMatFile,multiMatRule,\
            grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP,\
            grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP,\
            grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP,\
            phaseMode,\
            mixPhaseMode, phaseFillerContent, phaseFillerDensity,\
            particlePhaseMode, phaseMinPar, phaseMaxPar, phaseOffsetCoefList,\
            periodicToggle,particleOffsetCoef,\
            outputDir, dataFilesGen, visFilesGen, singleTetGen, modelType,\
            _, _, _] = read_LDPMCSL_inputs(self.form)

        if modelType in ["Confinement Shear Lattice (CSL) - LDPM Style ",\
                         "Confinement Shear Lattice (CSL) - Original"]:
            elementType = "CSL"
        else:
            elementType = "LDPM"

        geoName = elementType + "geo" + str(0).zfill(3)
        meshName = elementType + "mesh" + str(0).zfill(3)
        analysisName = elementType + "analysis"
        materialName = elementType + "material"
        dataFilesName = elementType + 'dataFiles'+ str(0).zfill(3)
        visualFilesName = elementType + 'visualFiles'+ str(0).zfill(3)

        # Set view
        docGui.activeView().viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
        Gui.runCommand('Std_DrawStyle',6)
        Gui.runCommand('Std_PerspectiveCamera',1)


        # Generate analysis objects
        self.form[5].statusWindow.setText("Status: Generating analysis objects.") 
        genAna = gen_LDPMCSL_analysis(analysisName,materialName)
        self.form[5].progressBar.setValue(3) 

        [allNodes,allTets,parDiameterList,materialList,minPar,geoName] = gen_LDPM_debugTet(type)

        [tetFacets,facetCenters,facetAreas,facetNormals,tetn1,tetn2,tetPoints,allDiameters,facetPointData,facetCellData] = \
            gen_LDPMCSL_tesselation(allNodes,allTets,parDiameterList,minPar,geoName)   


        self.form[5].progressBar.setValue(95) 

        # Store values for unused features
        edgedata = 0
        edgeMaterialList = 0
        multiMatRule = 0
        particleID = np.zeros(4)
        multiMaterial = 'Off'
        cementStructure = 'Off'

        [facetData,facetMaterial,subtetVol,facetVol1,facetVol2,particleMaterial] = gen_LDPM_facetData(\
            allNodes,allTets,tetFacets,facetCenters,facetAreas,facetNormals,tetn1,\
            tetn2,materialList,multiMatRule,multiMaterial,cementStructure,edgeMaterialList,facetCellData,particleID)

        self.form[5].progressBar.setValue(98) 


        self.form[5].statusWindow.setText("Status: Writing external facet data file.") 

        # Initialize counter for number of facet materials switched
        matSwitched = 0

        itzVolFracSim,binderVolFracSim,aggVolFracSim,itzVolFracAct,binderVolFracAct,aggVolFracAct,\
            PoresVolFracSim,ClinkerVolFracSim,CHVolFracSim,CSH_LDVolFracSim,CSH_HDVolFracSim,\
            PoresVolFracAct,ClinkerVolFracAct,CHVolFracAct,CSH_LDVolFracAct,CSH_HDVolFracAct,\
            matSwitched,multiMatRule = 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0


        App.activeDocument().addObject('App::DocumentObjectGroup',dataFilesName)
        App.activeDocument().getObject(dataFilesName).Label = 'Data Files'

        App.activeDocument().addObject('App::DocumentObjectGroup',visualFilesName)
        App.activeDocument().getObject(visualFilesName).Label = 'Visualization Files'

        App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName))
        App.getDocument(App.ActiveDocument.Name).getObject(analysisName).addObject(App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName))

        self.form[5].statusWindow.setText("Status: Writing node data file.")

        mkData_nodes(geoName,tempPath,allNodes)

        self.form[5].statusWindow.setText("Status: Writing tet data file.")

        mkData_LDPMCSL_tets(geoName,tempPath,allTets)

        self.form[5].statusWindow.setText("Status: Writing facet data file.")

        # If data files requested, generate Facet File
        mkData_LDPMCSL_facets(geoName,tempPath,facetData)
        mkData_LDPMCSL_facetsVertices(geoName,tempPath,tetFacets)
        #mkData_LDPMCSL_faceFacets(geoName,tempPath,surfaceNodes,surfaceFaces)

        self.form[5].statusWindow.setText("Status: Writing particle data file.")

        # If data files requested, generate Particle Data File
        mkData_particles(allNodes,parDiameterList,geoName,tempPath)

        self.form[5].statusWindow.setText("Status: Writing visualization files.")

        # If visuals requested, generate Particle VTK File
        mkVtk_particles(allNodes,parDiameterList,materialList,geoName,tempPath)

        # If visuals requested, generate Facet VTK File
        mkVtk_LDPMCSL_facets(geoName,tempPath,tetFacets,facetMaterial)

        mkVtk_LDPM_singleTet(allNodes,allTets,geoName,tempPath)


        i = 0
        outName = '/' + geoName + geoType + str(i).zfill(3)
        while os.path.isdir(Path(outDir + outName)):
            i = i+1
            outName = '/' + geoName + geoType + str(i).zfill(3)


        mkPy_LDPM_singleDebugParaview(geoName, outDir, outName, tempPath)
        mkPy_LDPM_singleDebugParaviewLabels(geoName, tempPath)

        # Move files to selected output directory
        os.rename(Path(tempPath),Path(outDir + outName))
        os.rename(Path(outDir + outName + '/' + geoName + '-para-singleTet.000.vtk'),Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))

        try:
            App.Console.PrintMessage("Model moved to output folder...\n")
        except Exception:
            print("Model moved to output folder...")


        # Set linked object for node data file
        LDPMnodesData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMnodesData")
        LDPMnodesData.ViewObject.Proxy = IconViewProviderToFile(LDPMnodesData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMnodesData)
        LDPMnodesData.addProperty("App::PropertyFile",'Location','Node Data File','Location of node data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-nodes.dat'))
        
        # Set linked object for tet data file
        LDPMtetsData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMtetsData")
        LDPMtetsData.ViewObject.Proxy = IconViewProviderToFile(LDPMtetsData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMtetsData)
        LDPMtetsData.addProperty("App::PropertyFile",'Location','Tet Data File','Location of tets data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-tets.dat'))

        # Set linked object for facet data file
        LDPMfacetsData = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMfacetsData")
        LDPMfacetsData.ViewObject.Proxy = IconViewProviderToFile(LDPMfacetsData,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(dataFilesName).addObject(LDPMfacetsData)
        LDPMfacetsData.addProperty("App::PropertyFile",'Location','Facet Data File','Location of facet data file').Location=str(Path(outDir + outName + '/' + geoName + '-data-facets.dat'))


        # Set linked object for particle VTK file
        LDPMparticlesVTK = App.ActiveDocument.addObject("Part::FeaturePython", "LDPMparticlesVTK")
        LDPMparticlesVTK.ViewObject.Proxy = IconViewProviderToFile(LDPMparticlesVTK,os.path.join(ICONPATH,'FEMMeshICON.svg'))
        App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMparticlesVTK)
        LDPMparticlesVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-particles.000.vtk'))



        #objName = App.getDocument(App.ActiveDocument.Name).getObjectsByLabel(geoName)[0].Name
        #try:
        #    Gui.getDocument(App.ActiveDocument.Name).getObject(objName).Transparency = 0
        #    Gui.getDocument(App.ActiveDocument.Name).getObject(objName).ShapeColor = (0.80,0.80,0.80)
        #except:
        #    pass



        # Insert mesh visualization and link mesh VTK file
        Fem.insert(str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk')),App.ActiveDocument.Name)
        LDPMmeshVTK = App.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000')
        LDPMmeshVTK.Label = 'LDPMmeshVTK'
        App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMmeshVTK)
        LDPMmeshVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-mesh.000.vtk'))

        # Set visualization properties for mesh
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').DisplayMode = u"Wireframe & Nodes"
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').PointSize = 20.00
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').PointColor = (255.0,170.0,0.0)
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').MaxFacesShowInner = 0
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').BackfaceCulling = False
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_mesh_000').ShapeColor = (0.36,0.36,0.36)
        









        # Insert facet visualization and link facet VTK file
        Fem.insert(str(Path(outDir + outName + '/' + geoName + '-para-facets.000.vtk')),App.ActiveDocument.Name)        
        LDPMfacetsVTK = App.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000')
        LDPMfacetsVTK.Label = 'LDPMfacetsVTK' 
        App.getDocument(App.ActiveDocument.Name).getObject(visualFilesName).addObject(LDPMfacetsVTK)
        LDPMfacetsVTK.addProperty("App::PropertyFile",'Location','Paraview VTK File','Location of Paraview VTK file').Location=str(Path(outDir + outName + '/' + geoName + '-para-facets.000.vtk'))


        # Set visualization properties for facets
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').DisplayMode = u"Faces & Wireframe"
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').MaxFacesShowInner = 0
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').BackfaceCulling = False
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').ShapeColor = (0.36,0.36,0.36)
        Gui.getDocument(App.ActiveDocument.Name).getObject(geoName + '_para_facets_000').Transparency = 50


        self.form[5].progressBar.setValue(100) 


        # Switch to FEM GUI
        App.ActiveDocument.recompute()


        Gui.Control.closeDialog()
        Gui.activateWorkbench("FemWorkbench")
        FemGui.setActiveAnalysis(App.activeDocument().getObject(analysisName))

        # Set view
        docGui.activeView().viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
        Gui.runCommand('Std_DrawStyle',6)
        Gui.runCommand('Std_PerspectiveCamera',1)






        
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


class input_PLDPM_Class():
    """My new command"""

    def GetResources(self):
        return {"Pixmap"  : os.path.join(ICONPATH, "p-ldpm.svg"), 
                "MenuText": "P-LDPM Generation",
                "ToolTip" : "Generation of a P-LDPM geometry"}

    def Activated(self):

        # Close any existing dialog before showing a new one
        try:
            Gui.Control.closeDialog()
        except:
            pass
        
        Gui.Control.showDialog(inputWindow_PLDPM())

        return

    def IsActive(self):

        return True

Gui.addCommand("mod_PLDPM", input_PLDPM_Class())
