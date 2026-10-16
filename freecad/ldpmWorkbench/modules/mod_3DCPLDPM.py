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
## 3DCP-LDPM module for 3D Printing LDPM generation
##
## ===========================================================================

# pyright: reportMissingImports=false

# Importing: standard
import json
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
import re

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
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs                    import read_LDPMCSL_inputs, GEOMETRY_FILE_DIALOG_FILTER, PROFILE_FILE_DIALOG_FILTER, normalize_sweep3dp_path_type_index, sweep3dp_path_ui_index

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
from freecad.ldpmWorkbench.generation.gen_mesh_preview                  import (
    find_latest_mesh_preview,
    run_mesh_preview,
)
from freecad.ldpmWorkbench.modules.mod_MeshPreview                      import launch_mesh_preview



# Turn off error for divide by zero and invalid operations
np.seterr(divide='ignore', invalid='ignore')



from freecad.ldpmWorkbench.generation.gen_LDPMCSL_multiStep import configure_multiprocessing_for_freecad
configure_multiprocessing_for_freecad()



class inputWindow_3DCPLDPM:
    def __init__(self):

        self.form = []

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_3DCPLDPM_modelProps.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_geometry.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_particles.ui"))        
        self.form.append(cwloadUIfile("ui_3DCPLDPM_mixDesign.ui"))          
        self.form.append(cwloadUIfile("ui_3DCPLDPM_additionalPara.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_addReinf.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_interlayer.ui"))
        self.randomFieldForm = cwloadUIfile("ui_3DCPLDPM_randomField.ui")
        self.form.append(cwloadUIfile("ui_3DCPLDPM_modelPreview.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_generation.ui"))
        self.form.append(cwloadUIfile("ui_3DCPLDPM_debugging.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Model Settings")
        self.form[1].setWindowTitle("Geometry")
        self.form[2].setWindowTitle("Particles")        
        self.form[3].setWindowTitle("Mix Design")
        self.form[4].setWindowTitle("Reinforcement Parameters")
        self.form[5].setWindowTitle("Additional Reinforcement Parameters")
        self.form[6].setWindowTitle("Interlayer Parameters")
        self.randomFieldForm.setWindowTitle("Random Field")
        self.form[7].setWindowTitle("Mesh Preview")
        self.form[8].setWindowTitle("Model Generation")
        self.form[9].setWindowTitle("Generate Single Tet")

        cwloadUIicon(self.form[0],"FEM_MaterialMechanicalNonlinear.svg")
        cwloadUIicon(self.form[1],"PartDesign_AdditiveBox.svg")
        cwloadUIicon(self.form[2],"Arch_Material_Group.svg")
        cwloadUIicon(self.form[3],"FEM_ConstraintFlowVelocity.svg")
        cwloadUIicon(self.form[4],"PartDesign_Line.svg")
        cwloadUIicon(self.form[5],"PartDesign_Line.svg")
        cwloadUIicon(self.form[6],"PartDesign_AdditiveHelix.svg")
        cwloadUIicon(self.randomFieldForm,"particles_input.svg")
        cwloadUIicon(self.form[7],"mesh_preview.svg")
        cwloadUIicon(self.form[8],"3DCP-LDPM.svg")
        cwloadUIicon(self.form[9],"PartDesign_Sprocket.svg")

        # Set initial output directory
        self.form[8].outputDir.setText(str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench')))

        if hasattr(self.form[4], 'PrimitiveTypeCB'):
            rebar_idx = self.form[4].PrimitiveTypeCB.findText("Rebar Parameters")
            if rebar_idx >= 0:
                self.form[4].PrimitiveTypeCB.removeItem(rebar_idx)
        if hasattr(self.form[1], 'geometryType'):
            lshape_idx = self.form[1].geometryType.findText("L-shape")
            if lshape_idx >= 0:
                self.form[1].geometryType.setItemIcon(
                    lshape_idx,
                    QtGui.QIcon(os.path.join(ICONPATH, "Part_LShape.svg")),
                )
            QtCore.QObject.connect(self.form[1].geometryType, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateReinforcementFiberPage)
        self.updateReinforcementFiberPage()
        
        # Initialize sketch list for path
        self.updatePathSketchList()
        if hasattr(self.form[4], 'orientationPathType_sweep3dp'):
            self.updateOrientationPathSketchList()
            self.onOrientationPathTypeChanged(self.form[4].orientationPathType_sweep3dp.currentIndex())

        # Connect selectObject and deselectObject Button in the Geometry Tab
        QtCore.QObject.connect(self.form[1].selectObjectButton, QtCore.SIGNAL("clicked()"), self.selectGeometry)
        QtCore.QObject.connect(self.form[1].deselectObjectButton, QtCore.SIGNAL("clicked()"), self.deselectGeometry)

        # Connect Open File Buttons
        QtCore.QObject.connect(self.form[0].readFileButton, QtCore.SIGNAL("clicked()"), self.openFilePara)
        QtCore.QObject.connect(self.form[1].readFileButton, QtCore.SIGNAL("clicked()"), self.openFileGeo)
        QtCore.QObject.connect(self.form[1].readProfileFileButton, QtCore.SIGNAL("clicked()"), self.openProfileFile)
        QtCore.QObject.connect(self.form[1].createSketchButton, QtCore.SIGNAL("clicked()"), self.createPathSketch)
        QtCore.QObject.connect(self.form[1].selectSketchButton, QtCore.SIGNAL("clicked()"), self.selectPathSketch)
        QtCore.QObject.connect(self.form[1].sweep3dpPathType, QtCore.SIGNAL("currentIndexChanged(int)"), self.updatePathSketchList)
        QtCore.QObject.connect(self.form[1].sweep3dpPathSketch, QtCore.SIGNAL("currentIndexChanged(int)"), self.onPathSketchSelected)
        if hasattr(self.form[1], "sweep3dpFirstLayerProperties"):
            QtCore.QObject.connect(
                self.form[1].sweep3dpFirstLayerProperties,
                QtCore.SIGNAL("toggled(bool)"),
                self.onFirstLayerPropertiesToggled,
            )
            self.onFirstLayerPropertiesToggled(self.form[1].sweep3dpFirstLayerProperties.isChecked())
        if hasattr(self.form[1], "sweep3dpCircularSeam"):
            QtCore.QObject.connect(
                self.form[1].sweep3dpCircularSeam,
                QtCore.SIGNAL("toggled(bool)"),
                self.onCircularSeamToggled,
            )
            self.onCircularSeamToggled(self.form[1].sweep3dpCircularSeam.isChecked())
        if hasattr(self.form[5], "addReinfTypeCB"):
            QtCore.QObject.connect(self.form[5].addReinfTypeCB, QtCore.SIGNAL("currentIndexChanged(int)"), self.onAddReinfTypeChanged)
            self.onAddReinfTypeChanged(self.form[5].addReinfTypeCB.currentIndex())
        if hasattr(self.form[5], "addReinfToggle"):
            QtCore.QObject.connect(self.form[5].addReinfToggle, QtCore.SIGNAL("currentIndexChanged(int)"), self.onAddReinfToggleChanged)
            self.onAddReinfToggleChanged(self.form[5].addReinfToggle.currentIndex())
        if hasattr(self.form[5], "rebarCadGroup"):
            QtCore.QObject.connect(self.form[5].rebarCadGroup, QtCore.SIGNAL("toggled(bool)"), self.onRebarCadGroupToggled)
            self.onRebarCadGroupToggled(self.form[5].rebarCadGroup.isChecked())
        if hasattr(self.form[5], "rebarLinesGroup"):
            QtCore.QObject.connect(self.form[5].rebarLinesGroup, QtCore.SIGNAL("toggled(bool)"), self.onRebarLinesGroupToggled)
            self.onRebarLinesGroupToggled(self.form[5].rebarLinesGroup.isChecked())
        if hasattr(self.form[5], "rebarCadButton"):
            QtCore.QObject.connect(self.form[5].rebarCadButton, QtCore.SIGNAL("clicked()"), self.openRebarCadFile)
        if hasattr(self.form[5], "cableCadButton"):
            QtCore.QObject.connect(self.form[5].cableCadButton, QtCore.SIGNAL("clicked()"), self.openCableCadFile)
        if hasattr(self.form[1], 'sweep3dpNumSlicesRaster'):
            QtCore.QObject.connect(self.form[1].sweep3dpNumSlicesRaster, QtCore.SIGNAL("valueChanged(int)"), self.onRasterNumSlicesChanged)
        if hasattr(self.form[4], 'orientationPathType_sweep3dp'):
            QtCore.QObject.connect(self.form[4].orientationPathType_sweep3dp, QtCore.SIGNAL("currentIndexChanged(int)"), self.onOrientationPathTypeChanged)
        if hasattr(self.form[4], 'orientationPathSketch_sweep3dp'):
            QtCore.QObject.connect(self.form[4].orientationPathSketch_sweep3dp, QtCore.SIGNAL("currentIndexChanged(int)"), self.onOrientationPathSketchSelected)
        QtCore.QObject.connect(self.randomFieldForm.rfFieldDirButton, QtCore.SIGNAL("clicked()"), self.openRFFieldDir)
        QtCore.QObject.connect(self.randomFieldForm.rfSubmitAssignment, QtCore.SIGNAL("clicked()"), self.submitRFAssignment)
        QtCore.QObject.connect(self.form[8].readDirButton, QtCore.SIGNAL("clicked()"), self.openDir)
        if hasattr(self.form[4], 'readMultiMatFile'):
            QtCore.QObject.connect(self.form[4].readMultiMatFile, QtCore.SIGNAL("clicked()"), self.openMultiMatFile)
        if hasattr(self.form[4], 'readAggFile'):
            QtCore.QObject.connect(self.form[4].readAggFile, QtCore.SIGNAL("clicked()"), self.openAggFile)
        QtCore.QObject.connect(self.form[4].readFileButton, QtCore.SIGNAL("clicked()"), self.openFiberFile)
        if hasattr(self.form[1], 'sweep3dpNumSlicesRaster'):
            self.onRasterNumSlicesChanged(self.form[1].sweep3dpNumSlicesRaster.value())

        # Run generation for LDPM or CSL
        QtCore.QObject.connect(self.form[8].generate, QtCore.SIGNAL("clicked()"), self.generationDriver)
        QtCore.QObject.connect(self.form[8].generateFast, QtCore.SIGNAL("clicked()"), self.generationDriverFast)
        QtCore.QObject.connect(self.form[8].externalGenerate, QtCore.SIGNAL("clicked()"), self.generationDriverExternal)
        QtCore.QObject.connect(self.form[8].writePara, QtCore.SIGNAL("clicked()"), self.writeParameters)
        QtCore.QObject.connect(self.form[7].generateMesh, QtCore.SIGNAL("clicked()"), self.generateMeshPreview)
        QtCore.QObject.connect(self.form[7].openInViewer, QtCore.SIGNAL("clicked()"), self.openMeshPreviewViewer)

        # Interlayer toggle — show/hide type selector
        QtCore.QObject.connect(self.form[6].interlayerToggle, QtCore.SIGNAL("currentIndexChanged(int)"), self.form[6].interlayerStack.setCurrentIndex)

        for row in (1, 2):
            toggle = getattr(self.form[6], "multiDir" + str(row) + "Toggle")
            QtCore.QObject.connect(
                toggle,
                QtCore.SIGNAL("currentIndexChanged(int)"),
                lambda idx, r=row: self._updateMultiDirRow(r, idx),
            )
            self._updateMultiDirRow(row, toggle.currentIndex())

        il = self.form[6]
        if hasattr(il, "customInterlayerMode"):
            QtCore.QObject.connect(
                il.customInterlayerMode,
                QtCore.SIGNAL("currentIndexChanged(int)"),
                self._syncCustomInterlayerSection,
            )
            self._syncCustomInterlayerSection(il.customInterlayerMode.currentIndex())
        if hasattr(il, "customDxfCadButton"):
            QtCore.QObject.connect(
                il.customDxfCadButton,
                QtCore.SIGNAL("clicked()"),
                self.openCustomDxfCadFile,
            )

        QtCore.QObject.connect(self.form[9].generate_reg, QtCore.SIGNAL("clicked()"), self.debugGenerateRegTet)
        QtCore.QObject.connect(self.form[9].generate_irreg, QtCore.SIGNAL("clicked()"), self.debugGenerateIrregTet)



    def _rfNumRealizations(self, field_dir):

        npy_path = os.path.join(field_dir, "random_variables.npy")
        dat_path = os.path.join(field_dir, "random_variables.dat")
        if os.path.isfile(npy_path):
            return int(np.load(npy_path).shape[1])
        if os.path.isfile(dat_path):
            return int(np.loadtxt(dat_path).shape[1])
        return None

    def _parseRFAssignments(self, text, n_samples, n_realz):

        job_plan = {}
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            match = re.match(r"^S(\d+)\s*>\s*R(\d+)$", line, re.IGNORECASE)
            if not match:
                return None, f"Invalid assignment line: '{line}' (expected S# > R#)."
            sample = int(match.group(1))
            realization = int(match.group(2))
            if sample < 1 or sample > n_samples:
                return None, f"Sample {sample} out of range (1..{n_samples})."
            if realization < 0 or realization >= n_realz:
                return None, f"Realization {realization} out of range (0..{n_realz - 1})."
            job_plan.setdefault(sample, [])
            if realization not in job_plan[sample]:
                job_plan[sample].append(realization)

        missing = [s for s in range(1, n_samples + 1) if s not in job_plan]
        if missing:
            return None, f"Missing realization assignment for sample(s): {missing}."

        return job_plan, None

    def _rfGateAndRoute(self, requested):

        rf_form = self.randomFieldForm
        if str(rf_form.rfToggle.currentText()).strip().lower() != "on":
            self._rfJobPlan = None
            return True

        field_dir = rf_form.rfFieldDir.text().strip()
        if not field_dir:
            msg = "Random Field is On: select a Random Field input folder."
            App.Console.PrintMessage(msg + "\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {msg}")
            return False
        if not os.path.isdir(field_dir):
            msg = f"Random Field is On: folder not found: {field_dir}"
            App.Console.PrintMessage(msg + "\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {msg}")
            return False

        assignment_text = rf_form.rfAssignmentList.toPlainText().strip()
        if not assignment_text:
            msg = "Random Field is On: submit at least one Sample > Realization assignment."
            App.Console.PrintMessage(msg + "\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {msg}")
            return False

        n_samples = max(1, int(self.form[0].numSampleBox.value()))
        n_realz = self._rfNumRealizations(field_dir)
        if n_realz is None:
            msg = "Random Field is On: random_variables file not found in RF folder."
            App.Console.PrintMessage(msg + "\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {msg}")
            return False

        job_plan, err = self._parseRFAssignments(assignment_text, n_samples, n_realz)
        if err:
            App.Console.PrintMessage(err + "\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {err}")
            return False

        self._rfJobPlan = job_plan
        self._rfFieldDir = field_dir

        route = "fast" if n_samples <= 1 else "external"
        route_label = "model" if route == "fast" else "external"
        if requested == route:
            App.Console.PrintMessage(
                f"Random Field On: Number of Samples = {n_samples} → {route_label} generation.\n"
            )
            return True

        App.Console.PrintMessage(
            f"Random Field On: Number of Samples = {n_samples} → routing to {route_label} generation.\n"
        )
        if route == "fast":
            self.generationDriverFast()
        else:
            self.generationDriverExternal()
        return False

    def generationDriver(self):

        if not self._rfGateAndRoute("normal"):
            return

        # Make a temporary path location
        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = False
        mkParameters(self,"LDPMCSL",tempPath,module="3DCPLDPM")
        
        try:
            driver_LDPMCSL(self,fastGen,tempPath)
        except RuntimeError as e:
            # Catch RuntimeError from particle placement failures
            print(f"Generation failed: {e}")
            App.Console.PrintError(f"Generation failed: {e}\n")
            # Update UI to show error
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)
        except Exception as e:
            # Catch any other exceptions
            print(f"Unexpected error during generation: {e}")
            import traceback
            traceback.print_exc()
            App.Console.PrintError(f"Unexpected error: {e}\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)

    def generationDriverFast(self):

        if not self._rfGateAndRoute("fast"):
            return

        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        fastGen = True
        mkParameters(self,"LDPMCSL",tempPath,module="3DCPLDPM")

        try:
            driver_LDPMCSL(self,fastGen,tempPath)
        except RuntimeError as e:
            print(f"Generation failed: {e}")
            App.Console.PrintError(f"Generation failed: {e}\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)
        except Exception as e:
            print(f"Unexpected error during generation: {e}")
            import traceback
            traceback.print_exc()
            App.Console.PrintError(f"Unexpected error: {e}\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)

    def generationDriverExternal(self):

        if not self._rfGateAndRoute("external"):
            return

        tempPath = tempfile.gettempdir() + "/chronoConc" + str(int(np.random.uniform(1e7,1e8))) + '/'
        os.mkdir(tempPath)

        mkParameters(self,"LDPMCSL",tempPath,module="3DCPLDPM")
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
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)
        except Exception as e:
            print(f"Unexpected error during external generation: {e}")
            import traceback
            traceback.print_exc()
            App.Console.PrintError(f"Unexpected error: {e}\n")
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)


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
        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a profile sketch (closed loop, XZ or YZ plane)", path, PROFILE_FILE_DIALOG_FILTER
        )
        if OpenName == "":  # if the name file is not selected then Abort process
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].sweep3dpProfileFileName.setText("Profile sketch file selected")
            self.form[1].sweep3dpProfileFile.setText(OpenName)

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
        if self.form[1].sweep3dpPathType.currentIndex() == 3:
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

    def updateReinforcementFiberPage(self, index=-1):
        if not hasattr(self.form[4], 'widgetStack2'):
            return
        geoType = self.form[1].geometryType.currentText()
        stack_idx = 1 if geoType == "Sweep-3DP" else 0
        self.form[4].widgetStack2.setCurrentIndex(stack_idx)
        if hasattr(self.form[4], 'PrimitiveTypeCB'):
            cb = self.form[4].PrimitiveTypeCB
            if cb.currentIndex() != stack_idx:
                cb.setCurrentIndex(stack_idx)

    def onCircularSeamToggled(self, checked):
        show = bool(checked)
        for name in (
            "label_circularSeamPosition",
            "sweep3dpCircularSeamPosition",
            "label_circularSeamDistance",
            "sweep3dpCircularSeamDistance",
            "label_circularSeamFillet",
            "sweep3dpCircularSeamFillet",
        ):
            widget = getattr(self.form[1], name, None)
            if widget is not None:
                widget.setVisible(show)

    def onAddReinfTypeChanged(self, index):
        if not hasattr(self.form[5], "groupBox_addReinf"):
            return
        title = "Cable Reinforcement Parameters" if int(index) == 1 else "Conventional Reinforcement Parameters"
        self.form[5].groupBox_addReinf.setTitle(title)

    def onAddReinfToggleChanged(self, index):
        show = int(index) == 1
        panel = self.form[5]
        if hasattr(panel, "groupBox_addReinf"):
            panel.groupBox_addReinf.setVisible(show)
        if hasattr(panel, "groupBox_element"):
            panel.groupBox_element.setVisible(show)

    def onRebarCadGroupToggled(self, checked):
        if hasattr(self.form[5], "rebarCadFields"):
            self.form[5].rebarCadFields.setVisible(bool(checked))

    def onRebarLinesGroupToggled(self, checked):
        if hasattr(self.form[5], "rebarLineFields"):
            self.form[5].rebarLineFields.setVisible(bool(checked))

    def openRebarCadFile(self):
        self._openReinforcementCadFile("rebarCadFile")

    def openCableCadFile(self):
        self._openReinforcementCadFile("cableCadFile")

    def _openReinforcementCadFile(self, widget_name):
        path = App.ConfigGet("UserHomePath")
        filetype = "DXF format (*.dxf);;All Files (*.*)"
        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a reinforcement CAD file", path, filetype
        )
        if OpenName == "":
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            getattr(self.form[5], widget_name).setText(OpenName)

    def onFirstLayerPropertiesToggled(self, checked):
        show = bool(checked)
        for name in (
            "label_firstLayerWidth",
            "sweep3dpFirstLayerWidth",
            "label_firstLayerHeight",
            "sweep3dpFirstLayerHeight",
        ):
            widget = getattr(self.form[1], name, None)
            if widget is not None:
                widget.setVisible(show)

    def onRasterNumSlicesChanged(self, value):
        for i in range(1, 9):
            label = getattr(self.form[1], f"sweep3dpSliceDirLabel{i}", None)
            box = getattr(self.form[1], f"sweep3dpSliceDir{i}", None)
            is_visible = i <= int(value)
            if label is not None:
                label.setVisible(is_visible)
            if box is not None:
                box.setVisible(is_visible)

    def updateOrientationPathSketchList(self):
        if not hasattr(self.form[4], 'orientationPathSketch_sweep3dp'):
            return
        self.form[4].orientationPathSketch_sweep3dp.clear()
        if App.ActiveDocument:
            for obj in App.ActiveDocument.Objects:
                if hasattr(obj, 'TypeId') and 'Sketch' in obj.TypeId:
                    self.form[4].orientationPathSketch_sweep3dp.addItem(obj.Label, obj.Name)
        if getattr(self.form[4], 'orientationPathType_sweep3dp', None) and self.form[4].orientationPathType_sweep3dp.currentIndex() == 3:
            current_name = self.form[4].orientationPathSketchName_sweep3dp.text()
            if current_name:
                idx = self.form[4].orientationPathSketch_sweep3dp.findData(current_name)
                if idx >= 0:
                    self.form[4].orientationPathSketch_sweep3dp.setCurrentIndex(idx)

    def onOrientationPathTypeChanged(self, index):
        if not hasattr(self.form[4], 'textLabel_orientationPathSketch_sweep3dp'):
            return
        show_sketch = (index == 3)
        self.form[4].textLabel_orientationPathSketch_sweep3dp.setVisible(show_sketch)
        self.form[4].orientationPathSketch_sweep3dp.setVisible(show_sketch)
        self.form[4].orientationPathSketchName_sweep3dp.setVisible(show_sketch)
        if show_sketch:
            self.updateOrientationPathSketchList()

    def onOrientationPathSketchSelected(self, index):
        if index >= 0 and hasattr(self.form[4], 'orientationPathSketch_sweep3dp'):
            sketch_name = self.form[4].orientationPathSketch_sweep3dp.itemData(index)
            if sketch_name:
                self.form[4].orientationPathSketchName_sweep3dp.setText(sketch_name)

    def openDir(self):

        path = App.ConfigGet('UserHomePath')

        OpenName = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Open Directory', path, QtWidgets.QFileDialog.ShowDirsOnly
        )

        if OpenName == '':  # if not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[8].outputDir.setText(OpenName)

        return OpenName

    def openRFFieldDir(self):

        path = App.ConfigGet('UserHomePath')

        OpenName = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select Random Field Input Folder', path, QtWidgets.QFileDialog.ShowDirsOnly
        )

        if OpenName == '':
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.randomFieldForm.rfFieldDir.setText(OpenName)

        return OpenName

    def submitRFAssignment(self):

        rf_form = self.randomFieldForm
        sample = rf_form.rfSampleGroup.text().strip()
        realization = rf_form.rfRealization.text().strip()
        if sample == '' or realization == '':
            App.Console.PrintMessage('Enter Sample Group and Realizations before Submit\n')
            return

        line = f"S{sample} > R{realization}"
        existing = rf_form.rfAssignmentList.toPlainText().strip()
        if existing:
            rf_form.rfAssignmentList.setPlainText(existing + "\n" + line)
        else:
            rf_form.rfAssignmentList.setPlainText(line)

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

    def openFiberFile(self):

        path = App.ConfigGet('UserHomePath')
        filetype = 'CT Scan Fiber File (*.txt *.dat);;All Files (*)'

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Read a CT scan fiber file', path, filetype
        )
        if OpenName == '':  # if the name file is not selected then Abort process
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[4].fiberFile.setText(OpenName)

    def _syncCustomInterlayerSection(self, index):

        il = self.form[6]
        sections = (
            "gb_custom_four_point",
            "gb_custom_path_ribbon",
            "gb_custom_dxf",
        )
        for i, name in enumerate(sections):
            box = getattr(il, name, None)
            if box is not None:
                box.setVisible(i == int(index))

    def openCustomDxfCadFile(self):

        path = App.ConfigGet("UserHomePath")
        filetype = "DXF format (*.dxf);;All Files (*.*)"
        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a custom interlayer CAD file", path, filetype
        )
        if OpenName == "":
            App.Console.PrintMessage("Process aborted" + "\n")
        elif hasattr(self.form[6], "customDxfCadFile"):
            self.form[6].customDxfCadFile.setText(OpenName)

    def _updateMultiDirRow(self, row, index):
        il = self.form[6]
        on = index == 1
        getattr(il, "multiDir" + str(row) + "Axis").setEnabled(on)
        getattr(il, "multiDir" + str(row) + "Mode").setEnabled(on)

    def writeParameters(self):

        mkParameters(self,"LDPMCSL","writeOnly",module="3DCPLDPM")

    def generateMeshPreview(self):
        try:
            self._lastMeshPreview = run_mesh_preview(self, "3DCPLDPM")
        except Exception as e:
            self._lastMeshPreview = None
            self.form[8].statusWindow.setText(f"Status: ERROR - {str(e)}")
            self.form[8].progressBar.setValue(0)
            App.Console.PrintError("Mesh preview failed: %s\n" % e)

    def openMeshPreviewViewer(self):
        info = getattr(self, "_lastMeshPreview", None)
        if info is None or not info.get("geometry") or not os.path.isfile(info["geometry"]):
            info = find_latest_mesh_preview(self.form[8].outputDir.text())
        if info is None or not info.get("geometry") or not os.path.isfile(info["geometry"]):
            self.form[8].statusWindow.setText("Status: ERROR - No mesh preview folder found.")
            App.Console.PrintError("No mesh preview folder found.\n")
            return
        self._lastMeshPreview = info
        launch_mesh_preview(
            geometry=info.get("geometry"),
            interfaces=info.get("interfaces"),
            auto_preview=True,
        )

    # Read parameters from file and write to input panel in FreeCAD
    def _restore_fused_sweep_geometry_from_params(self, params, _as_int, _as_float, _set_qty, _as_bool):
        geo = self.form[1]
        if not hasattr(geo, "sweep3dpPathType"):
            return
        path_idx = _as_int(params.get("fusePathType", 0), default=0)
        ui_path_idx = sweep3dp_path_ui_index(path_idx)
        geo.sweep3dpPathType.setCurrentIndex(ui_path_idx)
        if hasattr(geo, "pathStack"):
            geo.pathStack.setCurrentIndex(ui_path_idx)
        if hasattr(geo, "sweep3dpLayerWidth"):
            _set_qty(geo.sweep3dpLayerWidth, params.get("layerWidth", 10.0), 10.0)
        if hasattr(geo, "sweep3dpLayerHeight"):
            _set_qty(geo.sweep3dpLayerHeight, params.get("layerHeight", 5.0), 5.0)
        num_layers = max(1, _as_int(params.get("numLayers", 1), default=1))
        path_distance = params.get("pathDistance", 0.0)
        if path_idx == 0:
            if hasattr(geo, "sweep3dpPathDistance"):
                _set_qty(geo.sweep3dpPathDistance, path_distance, 100.0)
            if hasattr(geo, "sweep3dpNumLayers"):
                geo.sweep3dpNumLayers.setValue(num_layers)
        elif path_idx == 1:
            if hasattr(geo, "sweep3dpPathSide"):
                _set_qty(geo.sweep3dpPathSide, path_distance, 50.0)
            if hasattr(geo, "sweep3dpNumLayersSquare"):
                geo.sweep3dpNumLayersSquare.setValue(num_layers)
        elif path_idx == 2:
            sketch_name = str(params.get("fuseSketchName", "") or "")
            if hasattr(geo, "sweep3dpPathSketchName"):
                geo.sweep3dpPathSketchName.setText(sketch_name)
            try:
                self.updatePathSketchList()
            except Exception:
                pass
            if hasattr(geo, "sweep3dpNumLayersSketch"):
                geo.sweep3dpNumLayersSketch.setValue(num_layers)
        elif path_idx == 6:
            dia = params.get("circularDiameter", path_distance)
            if hasattr(geo, "sweep3dpCircularDiameter"):
                _set_qty(geo.sweep3dpCircularDiameter, dia, 100.0)
            if hasattr(geo, "sweep3dpNumLayersCircular"):
                geo.sweep3dpNumLayersCircular.setValue(num_layers)
            seam_on = _as_bool(params.get("circularSeam", "No"), default=False)
            if hasattr(geo, "sweep3dpCircularSeam"):
                geo.sweep3dpCircularSeam.setChecked(seam_on)
                self.onCircularSeamToggled(seam_on)
            seam_pos = str(params.get("circularSeamMode", "Aligned") or "Aligned")
            if hasattr(geo, "sweep3dpCircularSeamPosition"):
                pos_idx = geo.sweep3dpCircularSeamPosition.findText(seam_pos)
                if pos_idx >= 0:
                    geo.sweep3dpCircularSeamPosition.setCurrentIndex(pos_idx)
            if hasattr(geo, "sweep3dpCircularSeamDistance"):
                _set_qty(geo.sweep3dpCircularSeamDistance, params.get("circularSeamDistance", 1.0), 1.0)
        elif path_idx == 3:
            raster_loops = max(1, _as_int(params.get("rasterLoops", 1), default=1))
            if hasattr(geo, "sweep3dpRasterLoops"):
                geo.sweep3dpRasterLoops.setValue(raster_loops)
            if hasattr(geo, "sweep3dpRasterSpacing"):
                _set_qty(geo.sweep3dpRasterSpacing, params.get("rasterSpacing", 5.0), 5.0)
            if hasattr(geo, "sweep3dpRasterPathLength"):
                _set_qty(geo.sweep3dpRasterPathLength, path_distance, 100.0)
            raster_slices = max(1, min(8, num_layers))
            if hasattr(geo, "sweep3dpNumSlicesRaster"):
                geo.sweep3dpNumSlicesRaster.setValue(raster_slices)
            angles_raw = params.get("rasterAngles", "[]")
            try:
                raster_angles = json.loads(angles_raw) if isinstance(angles_raw, str) else list(angles_raw)
            except Exception:
                raster_angles = []
            default_dirs = [0.0, 90.0, 0.0, 90.0, 0.0, 90.0, 0.0, 90.0]
            for i in range(raster_slices):
                val = raster_angles[i] if i < len(raster_angles) else default_dirs[i]
                box = getattr(geo, f"sweep3dpSliceDir{i + 1}", None)
                if box is not None:
                    box.setValue(float(val))
            if hasattr(geo, "sweep3dpNumSlicesRaster"):
                self.onRasterNumSlicesChanged(geo.sweep3dpNumSlicesRaster.value())

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

        def _qty_value(val, default=0.0):
            try:
                s = str(val).strip().strip("'").strip('"')
                if not s:
                    return default
                return float(s.split()[0])
            except Exception:
                return default

        def _set_qty(widget, val, default=0.0):
            if widget is None:
                return
            widget.setProperty("rawValue", _qty_value(val, default))

        def _json_str(val, default=""):
            text = "" if val is None else str(val).strip()
            if not text:
                return default
            try:
                loaded = json.loads(text)
                if isinstance(loaded, str):
                    return loaded
            except Exception:
                pass
            if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
                return text[1:-1]
            return text

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

        fiberToggle = params.get("fiberToggle", "Off")
        fiberCutting = params.get("fiberCutting", "")
        fiberDiameter = _as_float(params.get("fiberDiameter", 0.0))
        fiberLength = _as_float(params.get("fiberLength", 0.0))
        fiberVol = _as_float(params.get("fiberVol", 0.0))
        fiberOrientation1 = _as_float(params.get("fiberOrientation1", 0.0))
        fiberOrientation2 = _as_float(params.get("fiberOrientation2", 0.0))
        fiberOrientation3 = _as_float(params.get("fiberOrientation3", 0.0))
        fiberPref = _as_float(params.get("fiberPref", 0.0))
        fiberFile = params.get("fiberFile", "")
        fiberIntersections = params.get("fiberIntersections", "")
        fiberOutputFiles = params.get("fiberOutputFiles", "Off")
        fiberInterfaceIntersect = params.get("fiberInterfaceIntersect", "On")

        orientationPathType_sweep3dp = _as_int(params.get("orientationPathType_sweep3dp", 0), default=0)
        orientationPathSketchName_sweep3dp = params.get("orientationPathSketchName_sweep3dp", "")
        orientationSegmentLength_sweep3dp = _as_float(params.get("orientationSegmentLength_sweep3dp", params.get("orientationSegments_sweep3dp", 10.0)), default=10.0)
        if "orientationSegmentLength_sweep3dp" not in params and "orientationSegments_sweep3dp" in params:
            orientationSegmentLength_sweep3dp = 10.0
        if orientationSegmentLength_sweep3dp <= 0:
            orientationSegmentLength_sweep3dp = 10.0

        particleOffsetCoef = _as_float(params.get("particleOffsetCoef", 0.2), default=0.2)

        outputDir = params.get("outputDir", self.form[8].outputDir.text())
        dataFilesGen = _as_bool(params.get("dataFilesGen", self.form[8].dataFilesGen.isChecked()), default=self.form[8].dataFilesGen.isChecked())
        visFilesGen = _as_bool(params.get("visFilesGen", self.form[8].visFilesGen.isChecked()), default=self.form[8].visFilesGen.isChecked())
        singleTetGen = _as_bool(params.get("singleTetGen", self.form[8].singleTetGen.isChecked()), default=self.form[8].singleTetGen.isChecked())
        modelType = params.get("modelType", self.form[8].modelType.currentText())

        interlayerToggle = params.get("interlayerToggle", "No")
        interlayerType = params.get("interlayerType", "Unidirectional Interlayer")
        if interlayerType == "Interlayer at Fused Surfaces":
            interlayerType = "Fused Surfaces"
        firstLayerThickness = _as_float(params.get("firstLayerThickness", 1.0), default=1.0)
        layerThickness = _as_float(params.get("layerThickness", 1.0), default=1.0)
        layerWidth = _as_float(params.get("layerWidth", 1.0), default=1.0)
        interfaceThickness = _as_float(params.get("interfaceThickness", 1.0), default=1.0)
        interlayerAxis = params.get("interlayerAxis", "Z")
        overlapMf = _as_int(params.get("overlapMf", 5), default=5)
        if "bulkMf" in params:
            bulkMf = _as_int(params.get("bulkMf", 1), default=1)
        else:
            bulkMf = 1 if _as_int(params.get("interlayerMf", 2), default=2) == 2 else 2
        interlayerMf = _as_int(params.get("interlayerMf", 2), default=2)
        xMf = _as_int(params.get("xMf", 2), default=2)
        yMf = _as_int(params.get("yMf", 3), default=3)
        zMf = _as_int(params.get("zMf", 4), default=4)

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
        if hasattr(self.form[0], "mpiToggle"):
            self.form[0].mpiToggle.setCurrentText(params.get("mpiToggle", self.form[0].mpiToggle.currentText()))
        if hasattr(self.form[0], "mpiRank"):
            self.form[0].mpiRank.setValue(_as_int(params.get("mpiRank", self.form[0].mpiRank.value()), default=self.form[0].mpiRank.value()))
        if hasattr(self.form[0], "mpiNodes"):
            self.form[0].mpiNodes.setValue(_as_int(params.get("mpiNodes", self.form[0].mpiNodes.value()), default=self.form[0].mpiNodes.value()))
        self.form[1].geometryType.setCurrentText(geoType)
        geo_idx = self.form[1].geometryType.currentIndex()
        if geo_idx >= 0 and hasattr(self.form[1], "widgetStack2"):
            self.form[1].widgetStack2.setCurrentIndex(geo_idx)
        self.updateReinforcementFiberPage()
        if geoType == "Box":
            if len(dimensions) >= 3:
                self.form[1].boxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].boxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].boxHeight.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Cylinder":
            if len(dimensions) >= 2:
                self.form[1].cylinderHeight.setProperty('rawValue',(dimensions[0]))
                self.form[1].cylinderRadius.setProperty('rawValue',(dimensions[1]))
        elif geoType == "L-shape":
            if len(dimensions) >= 2:
                _set_qty(self.form[1].lshapeLengthX, dimensions[0], 50.0)
                _set_qty(self.form[1].lshapeLengthY, dimensions[1], 50.0)
            if len(dimensions) >= 5:
                if hasattr(self.form[1], "lshapeWidth"):
                    _set_qty(self.form[1].lshapeWidth, dimensions[2], 10.0)
                _set_qty(self.form[1].lshapeThickness, dimensions[3], 10.0)
                if hasattr(self.form[1], "lshapeInsideFillet"):
                    _set_qty(self.form[1].lshapeInsideFillet, dimensions[4], 0.0)
            elif len(dimensions) >= 3:
                if hasattr(self.form[1], "lshapeWidth"):
                    _set_qty(self.form[1].lshapeWidth, dimensions[2], 10.0)
                _set_qty(self.form[1].lshapeThickness, dimensions[2], 10.0)
                if len(dimensions) >= 4 and hasattr(self.form[1], "lshapeInsideFillet"):
                    _set_qty(self.form[1].lshapeInsideFillet, dimensions[3], 0.0)
        elif geoType == "Cone":
            if len(dimensions) >= 3 and hasattr(self.form[1], "coneHeight"):
                self.form[1].coneHeight.setProperty('rawValue',(dimensions[0]))
                self.form[1].coneRadius1.setProperty('rawValue',(dimensions[1]))
                self.form[1].coneRadius2.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Sphere":
            if len(dimensions) >= 1 and hasattr(self.form[1], "sphereRadius"):
                self.form[1].sphereRadius.setProperty('rawValue',(dimensions[0]))
        elif geoType == "Ellipsoid":
            if len(dimensions) >= 6 and hasattr(self.form[1], "ellipsoidRadius1"):
                self.form[1].ellipsoidRadius1.setProperty('rawValue',(dimensions[0]))
                self.form[1].ellipsoidRadius2.setProperty('rawValue',(dimensions[1]))
                self.form[1].ellipsoidRadius3.setProperty('rawValue',(dimensions[2]))
                self.form[1].ellipsoidAngle1.setProperty('rawValue',(dimensions[3]))
                self.form[1].ellipsoidAngle2.setProperty('rawValue',(dimensions[4]))
                self.form[1].ellipsoidAngle3.setProperty('rawValue',(dimensions[5]))
        elif geoType == "Arbitrary Prism":
            if len(dimensions) >= 3 and hasattr(self.form[1], "prismCircumradius"):
                self.form[1].prismCircumradius.setProperty('rawValue',(dimensions[0]))
                self.form[1].prismHeight.setProperty('rawValue',(dimensions[1]))
                self.form[1].prismPolygon.setProperty('rawValue',(dimensions[2]))
        elif geoType == "Notched Prism - Square":
            if len(dimensions) >= 5 and hasattr(self.form[1], "notchBoxLength"):
                self.form[1].notchBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchDepth.setProperty('rawValue',(dimensions[4]))
        elif geoType == "Notched Prism - Semi Circle":
            if len(dimensions) >= 5 and hasattr(self.form[1], "notchSCBoxLength"):
                self.form[1].notchSCBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchSCBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchSCBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchSCWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchSCDepth.setProperty('rawValue',(dimensions[4]))
        elif geoType == "Notched Prism - Semi Ellipse":
            if len(dimensions) >= 5 and hasattr(self.form[1], "notchSEBoxLength"):
                self.form[1].notchSEBoxLength.setProperty('rawValue',(dimensions[0]))
                self.form[1].notchSEBoxWidth.setProperty('rawValue',(dimensions[1]))
                self.form[1].notchSEBoxHeight.setProperty('rawValue',(dimensions[2]))
                self.form[1].notchSEWidth.setProperty('rawValue',(dimensions[3]))
                self.form[1].notchSEDepth.setProperty('rawValue',(dimensions[4]))
        elif geoType == "Dogbone":
            if len(dimensions) >= 6 and hasattr(self.form[1], "dogboneLength"):
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
                rawPathIdx = _as_int(dimensions[4], default=0) if len(dimensions) > 4 else 0
                pathTypeIdx = 6 if rawPathIdx == 6 else normalize_sweep3dp_path_type_index(rawPathIdx)
                uiPathIdx = sweep3dp_path_ui_index(rawPathIdx)
                distTxt = str(dimensions[5]) if len(dimensions) > 5 else ""
                sideTxt = str(dimensions[7]) if len(dimensions) > 7 else ""
                sketchName = str(dimensions[9]) if len(dimensions) > 9 else ""
                numLayersTxt = str(dimensions[10]) if len(dimensions) > 10 else "1"
                numLayers = _as_int(numLayersTxt, default=1)
                if hasattr(self.form[1], "sweep3dpProfileType"):
                    self.form[1].sweep3dpProfileType.setCurrentIndex(profileTypeIdx)
                if hasattr(self.form[1], "profileStack"):
                    self.form[1].profileStack.setCurrentIndex(profileTypeIdx)
                if profileTypeIdx == 0:
                    if hasattr(self.form[1], "sweep3dpLayerWidth"):
                        _set_qty(self.form[1].sweep3dpLayerWidth, layerWidth, 10.0)
                    if hasattr(self.form[1], "sweep3dpLayerHeight"):
                        _set_qty(self.form[1].sweep3dpLayerHeight, layerHeight, 5.0)
                else:
                    if hasattr(self.form[1], "sweep3dpProfileFile") and profileFile:
                        self.form[1].sweep3dpProfileFile.setText(profileFile)
                        if hasattr(self.form[1], "sweep3dpProfileFileName"):
                            self.form[1].sweep3dpProfileFileName.setText("Profile sketch file selected")

                if hasattr(self.form[1], "sweep3dpPathType"):
                    self.form[1].sweep3dpPathType.setCurrentIndex(uiPathIdx)
                if hasattr(self.form[1], "pathStack"):
                    self.form[1].pathStack.setCurrentIndex(uiPathIdx)
                if pathTypeIdx == 0 and hasattr(self.form[1], "sweep3dpPathDistance"):
                    _set_qty(self.form[1].sweep3dpPathDistance, distTxt, 100.0)
                    if hasattr(self.form[1], "sweep3dpNumLayers"):
                        self.form[1].sweep3dpNumLayers.setValue(numLayers)
                elif pathTypeIdx == 1 and hasattr(self.form[1], "sweep3dpPathSide"):
                    _set_qty(self.form[1].sweep3dpPathSide, sideTxt, 100.0)
                    if hasattr(self.form[1], "sweep3dpNumLayersSquare"):
                        self.form[1].sweep3dpNumLayersSquare.setValue(numLayers)
                elif pathTypeIdx == 2:
                    if hasattr(self.form[1], "sweep3dpPathSketchName"):
                        self.form[1].sweep3dpPathSketchName.setText(sketchName)
                    try:
                        self.updatePathSketchList()
                    except Exception:
                        pass
                    if hasattr(self.form[1], "sweep3dpNumLayersSketch"):
                        self.form[1].sweep3dpNumLayersSketch.setValue(numLayers)
                elif pathTypeIdx == 3:
                    rasterLoops = _as_int(str(dimensions[11]), default=1) if len(dimensions) > 11 else 1
                    rasterSpacing = str(dimensions[12]) if len(dimensions) > 12 else "5 mm"
                    rasterSlices = _as_int(str(dimensions[13]), default=numLayers) if len(dimensions) > 13 else numLayers
                    rasterSlices = max(1, min(8, rasterSlices))
                    if len(dimensions) >= 24:
                        fillet_idx = 22
                        length_idx = 23
                    else:
                        fillet_idx = 14 + rasterSlices
                        length_idx = 15 + rasterSlices
                    rasterCornerFillet = str(dimensions[fillet_idx]) if len(dimensions) > fillet_idx else "0 mm"
                    rasterPathLength = str(dimensions[length_idx]) if len(dimensions) > length_idx else "100 mm"
                    if hasattr(self.form[1], "sweep3dpRasterLoops"):
                        self.form[1].sweep3dpRasterLoops.setValue(max(1, rasterLoops))
                    if hasattr(self.form[1], "sweep3dpRasterSpacing"):
                        _set_qty(self.form[1].sweep3dpRasterSpacing, rasterSpacing, 5.0)
                    if hasattr(self.form[1], "sweep3dpRasterCornerFillet"):
                        _set_qty(self.form[1].sweep3dpRasterCornerFillet, rasterCornerFillet, 0.0)
                    if hasattr(self.form[1], "sweep3dpRasterPathLength"):
                        _set_qty(self.form[1].sweep3dpRasterPathLength, rasterPathLength, 100.0)
                    if hasattr(self.form[1], "sweep3dpNumSlicesRaster"):
                        self.form[1].sweep3dpNumSlicesRaster.setValue(rasterSlices)
                    default_dirs = [0.0, 90.0, 0.0, 90.0, 0.0, 90.0, 0.0, 90.0]
                    for i in range(rasterSlices):
                        idx = 14 + i
                        val = _qty_value(dimensions[idx], default_dirs[i]) if len(dimensions) > idx else default_dirs[i]
                        box = getattr(self.form[1], f"sweep3dpSliceDir{i+1}", None)
                        if box is not None:
                            box.setValue(val)
                    if hasattr(self.form[1], "sweep3dpNumSlicesRaster"):
                        self.onRasterNumSlicesChanged(self.form[1].sweep3dpNumSlicesRaster.value())
                elif pathTypeIdx == 6:
                    diaTxt = str(dimensions[6]) if len(dimensions) > 6 else ""
                    seamRaw = str(dimensions[11]) if len(dimensions) > 11 else "No"
                    seamPos = str(dimensions[12]) if len(dimensions) > 12 else "Aligned"
                    seamDist = str(dimensions[13]) if len(dimensions) > 13 else "1 mm"
                    seamFillet = str(dimensions[14]) if len(dimensions) > 14 else "0 mm"
                    if hasattr(self.form[1], "sweep3dpCircularDiameter"):
                        _set_qty(self.form[1].sweep3dpCircularDiameter, diaTxt, 100.0)
                    if hasattr(self.form[1], "sweep3dpNumLayersCircular"):
                        self.form[1].sweep3dpNumLayersCircular.setValue(numLayers)
                    seam_on = seamRaw.strip().lower() in ("yes", "y", "on", "true", "1")
                    if hasattr(self.form[1], "sweep3dpCircularSeam"):
                        self.form[1].sweep3dpCircularSeam.setChecked(seam_on)
                        self.onCircularSeamToggled(seam_on)
                    if hasattr(self.form[1], "sweep3dpCircularSeamPosition"):
                        pos_idx = self.form[1].sweep3dpCircularSeamPosition.findText(seamPos)
                        if pos_idx >= 0:
                            self.form[1].sweep3dpCircularSeamPosition.setCurrentIndex(pos_idx)
                    if hasattr(self.form[1], "sweep3dpCircularSeamDistance"):
                        _set_qty(self.form[1].sweep3dpCircularSeamDistance, seamDist, 1.0)
                    if hasattr(self.form[1], "sweep3dpCircularSeamFillet"):
                        _set_qty(self.form[1].sweep3dpCircularSeamFillet, seamFillet, 0.0)
            except Exception as e:
                print(f"Warning: Could not apply Sweep-3DP dimensions: {e}")
            if hasattr(self.form[1], "sweep3dpFirstLayerProperties"):
                flp_raw = params.get("sweep3dpFirstLayerProperties", "No")
                flp_on = str(flp_raw).strip().lower() in ("yes", "y", "on", "true", "1")
                self.form[1].sweep3dpFirstLayerProperties.setChecked(flp_on)
                self.onFirstLayerPropertiesToggled(flp_on)
                if hasattr(self.form[1], "sweep3dpFirstLayerWidth"):
                    _set_qty(
                        self.form[1].sweep3dpFirstLayerWidth,
                        str(params.get("sweep3dpFirstLayerWidth", "")),
                        10.0,
                    )
                if hasattr(self.form[1], "sweep3dpFirstLayerHeight"):
                    _set_qty(
                        self.form[1].sweep3dpFirstLayerHeight,
                        str(params.get("sweep3dpFirstLayerHeight", "")),
                        5.0,
                    )
        self.form[1].cadFile.setText(cadFile)
        self.form[2].minPar_sim.setValue(minPar_sim)
        self.form[2].maxPar_sim.setValue(maxPar_sim)
        if hasattr(self.form[2], "particleOffsetCoef"):
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
        self.form[3].fillerContent.setText(str(fillerC))
        self.form[3].fillerDensity.setText(str(fillerDensity))
        self.form[3].airFracArb.setValue(airFrac2)
        if hasattr(self.form[4], 'HTCtoggle'):
            self.form[4].HTCtoggle.setCurrentText(htcToggle)
        if hasattr(self.form[4], 'HTClength'):
            self.form[4].HTClength.setValue(htcLength)
        self.updateReinforcementFiberPage()
        if geoType == "Sweep-3DP" and hasattr(self.form[4], "fiberToggle_sweep3dp"):
            self.form[4].fiberToggle_sweep3dp.setCurrentText(fiberToggle)
            if hasattr(self.form[4], "fiberCutting_sweep3dp") and fiberCutting:
                self.form[4].fiberCutting_sweep3dp.setCurrentText(fiberCutting)
            if hasattr(self.form[4], "fiberDiameter_sweep3dp"):
                self.form[4].fiberDiameter_sweep3dp.setValue(fiberDiameter)
            if hasattr(self.form[4], "fiberLength_sweep3dp"):
                self.form[4].fiberLength_sweep3dp.setValue(fiberLength)
            if hasattr(self.form[4], "fiberVol_sweep3dp"):
                self.form[4].fiberVol_sweep3dp.setValue(fiberVol)
            if hasattr(self.form[4], "fiberPref_sweep3dp"):
                self.form[4].fiberPref_sweep3dp.setValue(fiberPref)
            if hasattr(self.form[4], "fiberFile"):
                self.form[4].fiberFile.setText(fiberFile)
            if hasattr(self.form[4], "fiberIntersections_sweep3dp") and fiberIntersections:
                self.form[4].fiberIntersections_sweep3dp.setCurrentText(fiberIntersections)
            if hasattr(self.form[4], "fiberOutputFiles_sweep3dp") and fiberOutputFiles:
                self.form[4].fiberOutputFiles_sweep3dp.setCurrentText(fiberOutputFiles)
            if hasattr(self.form[4], "fiberInterfaceIntersect_sweep3dp") and fiberInterfaceIntersect:
                self.form[4].fiberInterfaceIntersect_sweep3dp.setCurrentText(fiberInterfaceIntersect)
        else:
            self.form[4].fiberToggle.setCurrentText(fiberToggle)
            if fiberCutting:
                self.form[4].fiberCutting.setCurrentText(fiberCutting)
            self.form[4].fiberDiameter.setValue(fiberDiameter)
            self.form[4].fiberLength.setValue(fiberLength)
            self.form[4].fiberVol.setValue(fiberVol)
            self.form[4].fiberOrien1.setValue(fiberOrientation1)
            self.form[4].fiberOrien2.setValue(fiberOrientation2)
            self.form[4].fiberOrien3.setValue(fiberOrientation3)
            self.form[4].fiberPref.setValue(fiberPref)
            self.form[4].fiberFile.setText(fiberFile)
            if hasattr(self.form[4], "fiberIntersections") and fiberIntersections:
                self.form[4].fiberIntersections.setCurrentText(fiberIntersections)
            if hasattr(self.form[4], "fiberOutputFiles") and fiberOutputFiles:
                self.form[4].fiberOutputFiles.setCurrentText(fiberOutputFiles)
            if hasattr(self.form[4], "fiberInterfaceIntersect") and fiberInterfaceIntersect:
                self.form[4].fiberInterfaceIntersect.setCurrentText(fiberInterfaceIntersect)
        if hasattr(self.form[4], 'orientationPathType_sweep3dp'):
            self.form[4].orientationPathType_sweep3dp.setCurrentIndex(
                sweep3dp_path_ui_index(orientationPathType_sweep3dp)
            )
            self.onOrientationPathTypeChanged(self.form[4].orientationPathType_sweep3dp.currentIndex())
        if hasattr(self.form[4], 'orientationPathSketchName_sweep3dp'):
            self.form[4].orientationPathSketchName_sweep3dp.setText(orientationPathSketchName_sweep3dp or "")
            self.updateOrientationPathSketchList()
        if hasattr(self.form[4], 'orientationSegmentLength_sweep3dp'):
            self.form[4].orientationSegmentLength_sweep3dp.setValue(orientationSegmentLength_sweep3dp)
        self.form[8].outputDir.setText(outputDir)
        if hasattr(self.form[8], "dataFilesGen"):
            self.form[8].dataFilesGen.setChecked(bool(dataFilesGen))
        if hasattr(self.form[8], "visFilesGen"):
            self.form[8].visFilesGen.setChecked(bool(visFilesGen))
        if hasattr(self.form[8], "singleTetGen"):
            self.form[8].singleTetGen.setChecked(bool(singleTetGen))
        if hasattr(self.form[8], "modelType"):
            self.form[8].modelType.setCurrentText(modelType)

        if hasattr(self.form[6], "interlayerToggle"):
            self.form[6].interlayerToggle.setCurrentText(interlayerToggle)
            self.form[6].interlayerType.setCurrentText(interlayerType)
            if hasattr(self.form[6], "interlayerTypeStack"):
                self.form[6].interlayerTypeStack.setCurrentIndex(self.form[6].interlayerType.currentIndex())
            if interlayerType == "Custom":
                if hasattr(self.form[6], "customInterfaceThickness"):
                    self.form[6].customInterfaceThickness.setProperty("rawValue", interfaceThickness)
                if hasattr(self.form[6], "customBulkMf"):
                    self.form[6].customBulkMf.setValue(bulkMf)
                custom_mode = str(params.get("customMode", "fourPoint")).strip()
                mode_text = {
                    "fourPoint": "4-Point Planar Surface",
                    "pathRibbon": "Path Ribbon (Planar)",
                    "dxfImport": "DXF / CAD Import",
                }.get(custom_mode, "4-Point Planar Surface")
                if hasattr(self.form[6], "customInterlayerMode"):
                    self.form[6].customInterlayerMode.setCurrentText(mode_text)
                    self._syncCustomInterlayerSection(self.form[6].customInterlayerMode.currentIndex())
                if hasattr(self.form[6], "customInterlayerDefinition"):
                    self.form[6].customInterlayerDefinition.setPlainText(
                        _json_str(params.get("customDefinition", ""))
                    )
                if hasattr(self.form[6], "customPathRibbonDefinition"):
                    self.form[6].customPathRibbonDefinition.setPlainText(
                        _json_str(params.get("customPathRibbonDefinition", ""))
                    )
                il = self.form[6]
                if hasattr(il, "customPathRibbonPlane"):
                    il.customPathRibbonPlane.setCurrentText(
                        _json_str(params.get("customPathRibbonPlane", "XY"), "XY") or "XY"
                    )
                if hasattr(il, "customPathRibbonType"):
                    path_type = _json_str(params.get("customPathRibbonType", "Polyline"), "Polyline")
                    if path_type not in ("Line", "Polyline", "Spline"):
                        path_type = "Polyline"
                    il.customPathRibbonType.setCurrentText(path_type)
                if hasattr(il, "customPathRibbonPlaneHeight"):
                    il.customPathRibbonPlaneHeight.setProperty(
                        "rawValue", float(params.get("customPathRibbonPlaneHeight", 0.0) or 0.0)
                    )
                if hasattr(il, "customDxfCadFile"):
                    il.customDxfCadFile.setText(_json_str(params.get("customDxfCadFile", "")))
                if hasattr(il, "customDxfPlane"):
                    il.customDxfPlane.setCurrentText(
                        _json_str(params.get("customDxfPlane", "XY"), "XY") or "XY"
                    )
                if hasattr(il, "customDxfPlaneHeight"):
                    il.customDxfPlaneHeight.setProperty(
                        "rawValue", float(params.get("customDxfPlaneHeight", 0.0) or 0.0)
                    )
                if hasattr(il, "customDxfStartPosition"):
                    start_pos = _json_str(params.get("customDxfStartPosition", ""))
                    if not str(start_pos).strip():
                        sx = float(params.get("customDxfStartX", 0.0) or 0.0)
                        sy = float(params.get("customDxfStartY", 0.0) or 0.0)
                        start_pos = f"{sx}, {sy}, 0"
                    il.customDxfStartPosition.setText(str(start_pos))
                if hasattr(il, "customDxfMf"):
                    il.customDxfMf.setValue(int(params.get("customDxfMf", 2) or 2))
            elif interlayerType == "Fused Surfaces":
                if hasattr(self.form[6], "fuseSweepGeometryType"):
                    self.form[6].fuseSweepGeometryType.setCurrentIndex(
                        sweep3dp_path_ui_index(_as_int(params.get("fusePathType", 0), default=0))
                    )
                self._restore_fused_sweep_geometry_from_params(
                    params, _as_int, _as_float, _set_qty, _as_bool
                )
                xy_on = str(params.get("fuseInterfaceX", "No")).strip().lower() in ("yes", "y", "on", "true", "1") or str(params.get("fuseInterfaceY", "No")).strip().lower() in ("yes", "y", "on", "true", "1")
                if hasattr(self.form[6], "fuseInterfaceXY"):
                    self.form[6].fuseInterfaceXY.setChecked(xy_on)
                if hasattr(self.form[6], "fuseInterfaceZ"):
                    self.form[6].fuseInterfaceZ.setChecked(str(params.get("fuseInterfaceZ", "Yes")).strip().lower() in ("yes", "y", "on", "true", "1"))
                if hasattr(self.form[6], "fuseInterfaceThickness"):
                    self.form[6].fuseInterfaceThickness.setProperty("rawValue", interfaceThickness)
                if hasattr(self.form[6], "fuseBulkMf"):
                    self.form[6].fuseBulkMf.setValue(bulkMf)
                if hasattr(self.form[6], "fuseXmF"):
                    self.form[6].fuseXmF.setValue(xMf)
                    self.form[6].fuseYmF.setValue(yMf)
                    self.form[6].fuseZmF.setValue(zMf)
                if hasattr(self.form[6], "fuseOverlapMf"):
                    self.form[6].fuseOverlapMf.setValue(overlapMf)
            else:
                self.form[6].uniFirstLayerThickness.setProperty("rawValue", firstLayerThickness)
                self.form[6].uniLayerThickness.setProperty("rawValue", layerThickness)
                self.form[6].uniInterfaceThickness.setProperty("rawValue", interfaceThickness)
                self.form[6].uniInterlayerAxis.setCurrentText(interlayerAxis)
                self.form[6].uniBulkMf.setValue(bulkMf)
                if hasattr(self.form[6], "uniInterlayerMf"):
                    self.form[6].uniInterlayerMf.setValue(interlayerMf)
            if hasattr(self.form[6], "multiFirstLayerThickness"):
                self.form[6].multiFirstLayerThickness.setProperty("rawValue", firstLayerThickness)
                self.form[6].multiLayerThickness.setProperty("rawValue", layerThickness)
                self.form[6].multiLayerWidth.setProperty("rawValue", layerWidth)
                self.form[6].multiInterfaceThickness.setProperty("rawValue", interfaceThickness)
                self.form[6].multiBulkMf.setValue(bulkMf)
                if hasattr(self.form[6], "multiXmF"):
                    self.form[6].multiXmF.setValue(xMf)
                    self.form[6].multiYmF.setValue(yMf)
                    self.form[6].multiZmF.setValue(zMf)
                self.form[6].multiOverlapMf.setValue(overlapMf)
                for row in (1, 2):
                    toggle = params.get("multiDir" + str(row) + "Toggle", "No")
                    axis = params.get("multiDir" + str(row) + "Axis", "X")
                    mode = params.get("multiDir" + str(row) + "Mode", "Height")
                    getattr(self.form[6], "multiDir" + str(row) + "Toggle").setCurrentText(toggle)
                    getattr(self.form[6], "multiDir" + str(row) + "Axis").setCurrentText(axis)
                    getattr(self.form[6], "multiDir" + str(row) + "Mode").setCurrentText(mode)
                    self._updateMultiDirRow(row, getattr(self.form[6], "multiDir" + str(row) + "Toggle").currentIndex())

        self._readReinforcementParameters(params, _as_bool, _as_int, _as_float)

    def _readReinforcementParameters(self, params, as_bool, as_int, as_float):
        if not hasattr(self.form[5], "addReinfTypeCB"):
            return
        panel = self.form[5]
        if hasattr(panel, "addReinfToggle"):
            toggle = str(params.get("addReinfToggle", "Off")).strip()
            if toggle.lower() in ("on", "yes", "y", "true", "1"):
                panel.addReinfToggle.setCurrentText("On")
            else:
                panel.addReinfToggle.setCurrentText("Off")
            self.onAddReinfToggleChanged(panel.addReinfToggle.currentIndex())
        if "addReinfType" in params:
            panel.addReinfTypeCB.setCurrentText(params.get("addReinfType", "Conventional Reinforcement"))
            if hasattr(panel, "addReinfStack"):
                panel.addReinfStack.setCurrentIndex(panel.addReinfTypeCB.currentIndex())
            self.onAddReinfTypeChanged(panel.addReinfTypeCB.currentIndex())
        if hasattr(panel, "rebarCadGroup") and "rebarCadOn" in params:
            panel.rebarCadGroup.setChecked(as_bool(params.get("rebarCadOn", "No")))
            self.onRebarCadGroupToggled(panel.rebarCadGroup.isChecked())
        if hasattr(panel, "rebarLinesGroup") and "rebarLinesOn" in params:
            panel.rebarLinesGroup.setChecked(as_bool(params.get("rebarLinesOn", "No")))
            self.onRebarLinesGroupToggled(panel.rebarLinesGroup.isChecked())
        self._setReinfText(panel, "rebarCadFile", params)
        self._setReinfValue(panel, "rebarCadStartX", params, as_float)
        self._setReinfValue(panel, "rebarCadStartY", params, as_float)
        self._setReinfValue(panel, "rebarCadHeight", params, as_float)
        self._setReinfValue(panel, "rebarCadRotation", params, as_float)
        self._setReinfText(panel, "rebarCadHeights", params)
        self._setReinfValue(panel, "rebarLineStartX", params, as_float)
        self._setReinfValue(panel, "rebarLineStartY", params, as_float)
        for index in (1, 2):
            prefix = "rebarDir" + str(index)
            self._setReinfValue(panel, prefix + "Distance", params, as_float)
            if hasattr(panel, prefix + "Direction") and prefix + "Direction" in params:
                getattr(panel, prefix + "Direction").setCurrentText(str(params.get(prefix + "Direction", "X")))
            self._setReinfValue(panel, prefix + "Count", params, as_int)
            self._setReinfValue(panel, prefix + "Spacing", params, as_float)
            self._setReinfText(panel, prefix + "Height", params)
        self._setReinfText(panel, "cableCadFile", params)
        self._setReinfValue(panel, "cableCadStartX", params, as_float)
        self._setReinfValue(panel, "cableCadStartY", params, as_float)
        self._setReinfValue(panel, "cableCadHeight", params, as_float)
        self._setReinfValue(panel, "cableCadRotation", params, as_float)
        self._setReinfText(panel, "cableCadHeights", params)
        if "elementLength" in params:
            self._setReinfValue(panel, "elementLength", params, as_float)
        elif hasattr(panel, "elementLength"):
            panel.elementLength.setValue(1.0)
        if "elementDiameter" in params:
            self._setReinfValue(panel, "elementDiameter", params, as_float)
        elif hasattr(panel, "elementDiameter"):
            panel.elementDiameter.setValue(1.0)
        if hasattr(panel, "reinfElementType"):
            if "reinfElementType" in params:
                panel.reinfElementType.setCurrentText(str(params.get("reinfElementType", "2DOF-T2D2/LINK1")))
            else:
                panel.reinfElementType.setCurrentText("2DOF-T2D2/LINK1")

    def _setReinfText(self, panel, name, params):
        if hasattr(panel, name) and name in params:
            getattr(panel, name).setText(str(params.get(name, "")))

    def _setReinfValue(self, panel, name, params, convert):
        if hasattr(panel, name) and name in params:
            getattr(panel, name).setValue(convert(params.get(name)))

    def debugGenerateRegTet(self):

        self.debugGenerateTet("Regular")

    def debugGenerateIrregTet(self):

        self.debugGenerateTet("Irregular")


    def debugGenerateTet(self,type):


        # Make output directory if does not exist
        outDir =  self.form[8].outputDir.text()
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
            fiberToggle, fiberCutting, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberFile, fiberIntersections, fiberOutputFiles, fiberInterfaceIntersect,\
            multiMatToggle,aggFile,multiMatFile,multiMatRule,\
            grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP,\
            grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP,\
            grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP,\
            phaseMode,\
            mixPhaseMode, phaseFillerContent, phaseFillerDensity,\
            particlePhaseMode, phaseMinPar, phaseMaxPar, phaseOffsetCoefList,\
            periodicToggle,particleOffsetCoef,\
            outputDir, dataFilesGen, visFilesGen, singleTetGen, modelType,\
            orientationPathType_sweep3dp, orientationPathSketchName_sweep3dp, orientationSegmentLength_sweep3dp] = read_LDPMCSL_inputs(self.form)

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
        self.form[8].statusWindow.setText("Status: Generating analysis objects.") 
        genAna = gen_LDPMCSL_analysis(analysisName,materialName)
        self.form[8].progressBar.setValue(3) 

        [allNodes,allTets,parDiameterList,materialList,minPar,geoName] = gen_LDPM_debugTet(type)

        [tetFacets,facetCenters,facetAreas,facetNormals,tetn1,tetn2,tetPoints,allDiameters,facetPointData,facetCellData] = \
            gen_LDPMCSL_tesselation(allNodes,allTets,parDiameterList,minPar,geoName)   


        self.form[8].progressBar.setValue(95) 

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

        self.form[8].progressBar.setValue(98) 


        self.form[8].statusWindow.setText("Status: Writing external facet data file.") 

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

        self.form[8].statusWindow.setText("Status: Writing node data file.")

        mkData_nodes(geoName,tempPath,allNodes)

        self.form[8].statusWindow.setText("Status: Writing tet data file.")

        mkData_LDPMCSL_tets(geoName,tempPath,allTets)

        self.form[8].statusWindow.setText("Status: Writing facet data file.")

        # If data files requested, generate Facet File
        mkData_LDPMCSL_facets(geoName,tempPath,facetData)
        mkData_LDPMCSL_facetsVertices(geoName,tempPath,tetFacets)
        #mkData_LDPMCSL_faceFacets(geoName,tempPath,surfaceNodes,surfaceFaces)

        self.form[8].statusWindow.setText("Status: Writing particle data file.")

        # If data files requested, generate Particle Data File
        mkData_particles(allNodes,parDiameterList,geoName,tempPath)

        self.form[8].statusWindow.setText("Status: Writing visualization files.")

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


        self.form[8].progressBar.setValue(100) 


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


class input_3DCPLDPM_Class():
    """My new command"""

    def GetResources(self):
        return {"Pixmap"  : os.path.join(ICONPATH, "3DCP-LDPM.svg"),
                "MenuText": "3DCP-LDPM Generation",
                "ToolTip" : "Generation of a 3DCP-LDPM geometry"}

    def Activated(self):

        # Close any existing dialog before showing a new one
        try:
            Gui.Control.closeDialog()
        except:
            pass
        
        Gui.Control.showDialog(inputWindow_3DCPLDPM())

        return

    def IsActive(self):

        return True

Gui.addCommand("mod_3DCPLDPM", input_3DCPLDPM_Class())
