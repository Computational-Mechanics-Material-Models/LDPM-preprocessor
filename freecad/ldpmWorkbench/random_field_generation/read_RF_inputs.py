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


def _qty(widget):

    text = str(widget.text()).strip()
    if text:
        return float(text.split()[0])
    return float(widget.value())


def _std(mean, cov_pct):

    return mean * cov_pct / 100.0


def read_RF_inputs(form):

    ms = form[0]
    rf = form[1]
    gen = form[2]

    elasticity_mean = float(rf.rfFieldElasticityMean.value())
    strength_mean = float(rf.rfFieldStrengthMean.value())
    fracture_mean = float(rf.rfFieldFractureMean.value())

    cross_correlation = [
        [float(rf.rfMatrixC11.value()), float(rf.rfMatrixC12.value()), float(rf.rfMatrixC13.value())],
        [float(rf.rfMatrixC12.value()), float(rf.rfMatrixC22.value()), float(rf.rfMatrixC23.value())],
        [float(rf.rfMatrixC13.value()), float(rf.rfMatrixC23.value()), float(rf.rfMatrixC33.value())],
    ]

    grid_file = rf.rfGridFile.text().strip()

    return {
        "numRealizations": int(ms.rfNumSamplesBox.value()),
        "seeds": ms.rfSeedsLine.text().strip(),
        "periodic": [
            bool(rf.rfFieldPeriodicX.isChecked()),
            bool(rf.rfFieldPeriodicY.isChecked()),
            bool(rf.rfFieldPeriodicZ.isChecked()),
        ],
        "x_range": [0.0, _qty(rf.rfFieldXSize)],
        "y_range": [0.0, _qty(rf.rfFieldYSize)],
        "z_range": [0.0, _qty(rf.rfFieldZSize)],
        "corr_l": [
            float(rf.rfFieldCorrLX.value()),
            float(rf.rfFieldCorrLY.value()),
            float(rf.rfFieldCorrLZ.value()),
        ],
        "corr_f": rf.rfFieldCorrFunction.currentText(),
        "dist_type": rf.rfFieldDistType.currentText(),
        "grid_spacing": float(rf.rfFieldGridSpacing.value()),
        "grid_file": grid_file if grid_file else None,
        "sparse": bool(gen.rfFieldSparse.isChecked()),
        "rank_correlation": bool(gen.rfFieldRankCorrelation.isChecked()),
        "elasticity_mean": elasticity_mean,
        "elasticity_cov": float(rf.rfFieldElasticityCOV.value()),
        "elasticity_std": _std(elasticity_mean, float(rf.rfFieldElasticityCOV.value())),
        "strength_mean": strength_mean,
        "strength_cov": float(rf.rfFieldStrengthCOV.value()),
        "strength_std": _std(strength_mean, float(rf.rfFieldStrengthCOV.value())),
        "fracture_mean": fracture_mean,
        "fracture_cov": float(rf.rfFieldFractureCOV.value()),
        "fracture_std": _std(fracture_mean, float(rf.rfFieldFractureCOV.value())),
        "cross_correlation": cross_correlation,
        "rfFieldInputFile": ms.rfFieldInputFile.text().strip(),
        "outputDir": gen.outputDir.text().strip(),
        "dataFilesGen": bool(gen.rfDataFilesGen.isChecked()),
        "visFilesGen": bool(gen.rfVisFilesGen.isChecked()),
        "modelType": gen.modelType.currentText(),
        "rfAssignments": gen.rfAssignmentList.toPlainText().strip(),
    }
