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
##
## Description coming soon...
##
##
## ===========================================================================

# pyright: reportMissingImports=false

import os
from pathlib import Path

import FreeCADGui as Gui
import FreeCAD as App

try:  # FreeCAD 1.0 provides a PySide shim
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:  # FreeCAD 0.20 ships PySide2
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:  # Fall back for very old FreeCAD versions
        from PySide import QtCore, QtGui  # type: ignore
        QtWidgets = QtGui  # type: ignore

from freecad.ldpmWorkbench import ICONPATH
from freecad.ldpmWorkbench.util.cwloadUIfile import cwloadUIfile
from freecad.ldpmWorkbench.util.cwloadUIicon import cwloadUIicon
from freecad.ldpmWorkbench.random_field_generation import generation_driver_RF


class inputWindow_RF:
    def __init__(self):

        self.form = []

        # Load UI's for Side Panel
        self.form.append(cwloadUIfile("ui_RF-LDPM_modelProps.ui"))
        self.form.append(cwloadUIfile("ui_RF-LDPM_randomField.ui"))
        self.form.append(cwloadUIfile("ui_RF-LDPM_randomFieldGeneration.ui"))

        # Label, Load Icons, and Initialize Panels
        self.form[0].setWindowTitle("Model Settings")
        self.form[1].setWindowTitle("Random Field Parameters")
        self.form[2].setWindowTitle("Random Field Generation")

        cwloadUIicon(self.form[0], "FEM_MaterialMechanicalNonlinear.svg")
        cwloadUIicon(self.form[1], "particles_input.svg")
        cwloadUIicon(self.form[2], "rf_field_generation.svg")

        defaultOutDir = str(Path(App.ConfigGet('UserHomePath') + '/ldpmWorkbench'))
        self.form[2].outputDir.setText(defaultOutDir)

        QtCore.QObject.connect(self.form[2].readDirButton, QtCore.SIGNAL("clicked()"), self.openRFFieldDir)
        QtCore.QObject.connect(self.form[0].rfFieldReadFileButton, QtCore.SIGNAL("clicked()"), self.openRFFieldInputFile)
        QtCore.QObject.connect(self.form[2].generateRandomField, QtCore.SIGNAL("clicked()"), self.runRFGeneration)
        QtCore.QObject.connect(self.form[1].rfGridFileReadButton, QtCore.SIGNAL("clicked()"), self.openRFGridFile)
        QtCore.QObject.connect(self.form[2].rfErrorEvaluation, QtCore.SIGNAL("clicked()"), self.runRFErrorEvaluation)
        self._last_rf_field_dir = None
        self.form[2].groupBox_rf_assignment.setVisible(False)

    def getStandardButtons(self):

        return int(QtWidgets.QDialogButtonBox.Close)

    def openRFFieldDir(self):

        path = App.ConfigGet('UserHomePath')

        OpenName = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Open Directory', path, QtWidgets.QFileDialog.ShowDirsOnly
        )

        if OpenName == '':
            App.Console.PrintMessage('Process aborted' + '\n')
        else:
            self.form[2].outputDir.setText(OpenName)

        return OpenName

    def openRFFieldInputFile(self):

        path = App.ConfigGet("UserHomePath")
        filetype = "CW Parameter input format (*.cwPar)"

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read a parameter file", path, filetype
        )
        if OpenName == "":
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[0].rfFieldInputFile.setText(OpenName)
            self.readParameters()

        return OpenName

    def readParameters(self):

        paraFile = self.form[0].rfFieldInputFile.text().strip()
        if not paraFile:
            return

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
                return int(float(str(val).strip()))
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
                import ast
                out = ast.literal_eval(str(val).strip())
                if isinstance(out, (list, tuple)):
                    return list(out)
            except Exception:
                pass
            return default

        def _cov(mean, std):
            try:
                m = float(mean)
                s = float(std)
                if m != 0.0:
                    return abs(s / m) * 100.0
            except Exception:
                pass
            return 0.0

        def _combo(widget, text):
            if text is None:
                return
            idx = widget.findText(str(text))
            if idx >= 0:
                widget.setCurrentIndex(idx)
            else:
                try:
                    widget.setCurrentText(str(text))
                except Exception:
                    pass

        ms = self.form[0]
        rf = self.form[1]
        gen = self.form[2]

        ms.rfNumSamplesBox.setValue(max(1, _as_int(params.get("numRealizations", ms.rfNumSamplesBox.value()), ms.rfNumSamplesBox.value())))
        if "seeds" in params:
            ms.rfSeedsLine.setText(params.get("seeds", ""))

        periodic = _as_list(params.get("periodic", "[False, False, False]"), [False, False, False])
        rf.rfFieldPeriodicX.setChecked(_as_bool(periodic[0] if len(periodic) > 0 else False))
        rf.rfFieldPeriodicY.setChecked(_as_bool(periodic[1] if len(periodic) > 1 else False))
        rf.rfFieldPeriodicZ.setChecked(_as_bool(periodic[2] if len(periodic) > 2 else False))

        x_range = _as_list(params.get("x_range", "[0.0, 0.0]"), [0.0, 0.0])
        y_range = _as_list(params.get("y_range", "[0.0, 0.0]"), [0.0, 0.0])
        z_range = _as_list(params.get("z_range", "[0.0, 0.0]"), [0.0, 0.0])
        try:
            rf.rfFieldXSize.setProperty("rawValue", float(x_range[1]) if len(x_range) > 1 else 0.0)
            rf.rfFieldYSize.setProperty("rawValue", float(y_range[1]) if len(y_range) > 1 else 0.0)
            rf.rfFieldZSize.setProperty("rawValue", float(z_range[1]) if len(z_range) > 1 else 0.0)
        except Exception:
            pass

        corr_l = _as_list(params.get("corr_l", "[0.0, 0.0, 0.0]"), [0.0, 0.0, 0.0])
        if len(corr_l) > 0:
            rf.rfFieldCorrLX.setValue(_as_float(corr_l[0]))
        if len(corr_l) > 1:
            rf.rfFieldCorrLY.setValue(_as_float(corr_l[1]))
        if len(corr_l) > 2:
            rf.rfFieldCorrLZ.setValue(_as_float(corr_l[2]))

        _combo(rf.rfFieldCorrFunction, params.get("corr_f"))
        _combo(rf.rfFieldDistType, params.get("dist_type"))
        if "grid_spacing" in params:
            rf.rfFieldGridSpacing.setValue(_as_float(params.get("grid_spacing"), rf.rfFieldGridSpacing.value()))

        grid_file = params.get("grid_file", "")
        if str(grid_file).strip() in ["", "None", "none"]:
            rf.rfGridFile.setText("")
        else:
            rf.rfGridFile.setText(str(grid_file).strip())

        e_mean = _as_float(params.get("elasticity_mean", rf.rfFieldElasticityMean.value()), rf.rfFieldElasticityMean.value())
        s_mean = _as_float(params.get("strength_mean", rf.rfFieldStrengthMean.value()), rf.rfFieldStrengthMean.value())
        f_mean = _as_float(params.get("fracture_mean", rf.rfFieldFractureMean.value()), rf.rfFieldFractureMean.value())
        rf.rfFieldElasticityMean.setValue(e_mean)
        rf.rfFieldStrengthMean.setValue(s_mean)
        rf.rfFieldFractureMean.setValue(f_mean)

        if "elasticity_cov" in params:
            rf.rfFieldElasticityCOV.setValue(_as_float(params.get("elasticity_cov")))
        elif "elasticity_std" in params:
            rf.rfFieldElasticityCOV.setValue(_cov(e_mean, params.get("elasticity_std")))
        if "strength_cov" in params:
            rf.rfFieldStrengthCOV.setValue(_as_float(params.get("strength_cov")))
        elif "strength_std" in params:
            rf.rfFieldStrengthCOV.setValue(_cov(s_mean, params.get("strength_std")))
        if "fracture_cov" in params:
            rf.rfFieldFractureCOV.setValue(_as_float(params.get("fracture_cov")))
        elif "fracture_std" in params:
            rf.rfFieldFractureCOV.setValue(_cov(f_mean, params.get("fracture_std")))

        cross = _as_list(params.get("cross_correlation", "[]"), [])
        try:
            import json
            if isinstance(params.get("cross_correlation"), str) and params.get("cross_correlation", "").strip().startswith("["):
                cross = json.loads(params.get("cross_correlation"))
        except Exception:
            pass
        if isinstance(cross, list) and len(cross) >= 3:
            try:
                rf.rfMatrixC11.setValue(_as_float(cross[0][0], 1.0))
                rf.rfMatrixC12.setValue(_as_float(cross[0][1], 0.0))
                rf.rfMatrixC13.setValue(_as_float(cross[0][2], 0.0))
                rf.rfMatrixC21.setValue(_as_float(cross[1][0], cross[0][1]))
                rf.rfMatrixC22.setValue(_as_float(cross[1][1], 1.0))
                rf.rfMatrixC23.setValue(_as_float(cross[1][2], 0.0))
                rf.rfMatrixC31.setValue(_as_float(cross[2][0], cross[0][2]))
                rf.rfMatrixC32.setValue(_as_float(cross[2][1], cross[1][2]))
                rf.rfMatrixC33.setValue(_as_float(cross[2][2], 1.0))
            except Exception:
                pass

        if "sparse" in params:
            gen.rfFieldSparse.setChecked(_as_bool(params.get("sparse")))
        if "rank_correlation" in params:
            gen.rfFieldRankCorrelation.setChecked(_as_bool(params.get("rank_correlation")))
        if "dataFilesGen" in params:
            gen.rfDataFilesGen.setChecked(_as_bool(params.get("dataFilesGen"), True))
        if "visFilesGen" in params:
            gen.rfVisFilesGen.setChecked(_as_bool(params.get("visFilesGen"), True))
        if "outputDir" in params and params.get("outputDir", "").strip():
            gen.outputDir.setText(params.get("outputDir").strip())
        _combo(gen.modelType, params.get("modelType"))

        if "rfAssignments" in params:
            assign_raw = params.get("rfAssignments", "")
            try:
                import json
                assign_val = json.loads(assign_raw)
                if isinstance(assign_val, str):
                    gen.rfAssignmentList.setPlainText(assign_val)
                else:
                    gen.rfAssignmentList.setPlainText(str(assign_val))
            except Exception:
                gen.rfAssignmentList.setPlainText(str(assign_raw).strip().strip('"'))

        App.Console.PrintMessage(f"RF parameters loaded from {paraFile}\n")

    def openRFGridFile(self):

        path = App.ConfigGet("UserHomePath")
        filetype = "Grid data (*.npy *.csv *.txt);;All Files (*)"

        OpenName, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Read random field grid file", path, filetype
        )
        if OpenName == "":
            App.Console.PrintMessage("Process aborted" + "\n")
        else:
            self.form[1].rfGridFile.setText(OpenName)

        return OpenName

    def runRFGeneration(self):

        generation_driver_RF(self)

    def runRFErrorEvaluation(self):

        try:
            import traceback
            from freecad.ldpmWorkbench.random_field_generation.driver_RF import run_rf_error_evaluation
            run_rf_error_evaluation(self)
        except Exception as e:
            App.Console.PrintError(f"Error evaluation failed: {e}\n")
            App.Console.PrintError(traceback.format_exc())

    def reject(self):
        try:
            Gui.ActiveDocument.resetEdit()
            Gui.Control.closeDialog()
        except Exception:
            Gui.Control.closeDialog()


class input_RF_Class():

    def GetResources(self):
        return {"Pixmap": os.path.join(ICONPATH, "rf_ldpm.svg"),
                "MenuText": "RF-Generation",
                "ToolTip": "Generation of Random Field"}

    def Activated(self):

        try:
            Gui.Control.closeDialog()
        except Exception:
            pass

        Gui.Control.showDialog(inputWindow_RF())

        return

    def IsActive(self):
        return True


Gui.addCommand("mod_RF", input_RF_Class())
