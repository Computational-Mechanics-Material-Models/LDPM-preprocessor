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
## 
## ===========================================================================
##
## Description coming soon...
##
## ===========================================================================


import os
import tempfile

import numpy as np

from freecad.ldpmWorkbench.random_field_generation.mkRFParameters import mkRFParameters


def _rf_status(self, text, value=None):
    try:
        from PySide import QtWidgets  # type: ignore
    except ImportError:
        try:
            from PySide2 import QtWidgets  # type: ignore
        except ImportError:
            from PySide import QtGui as QtWidgets  # type: ignore

    gen = self.form[2]
    gen.statusWindow.setText(text)
    if value is not None:
        gen.progressBar.setValue(value)
    QtWidgets.QApplication.processEvents()


def generation_driver_RF(self):
    import FreeCAD as App

    _rf_status(self, "Status: Starting...", 0)

    tempPath = tempfile.mkdtemp(prefix="chronoConc")

    try:
        _rf_status(self, "Status: Writing parameters...", 10)
        mkRFParameters(self, tempPath)

        _rf_status(self, "Status: Generation in process...", 30)
        from freecad.ldpmWorkbench.random_field_generation.driver_RF import driver_RF
        driver_RF(self, tempPath)

        _rf_status(self, "Status: Complete.", 100)
    except Exception as e:
        _rf_status(self, f"Status: ERROR - {e}", 0)
        App.Console.PrintError(f"Random field generation failed: {e}\n")
        return

    field_dir = getattr(self, "_last_rf_field_dir", None)
    if field_dir:
        App.Console.PrintMessage(
            "Random field generation finished successfully.\n"
            f"Output folder: {field_dir}\n"
            f"Parameter file: {field_dir}/rfWorkbench.cwPar\n"
        )
