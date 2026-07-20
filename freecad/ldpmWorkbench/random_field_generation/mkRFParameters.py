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


import json
import os
from pathlib import Path

from freecad.ldpmWorkbench.random_field_generation.read_RF_inputs import read_RF_inputs


def mkRFParameters(self, tempPath):

    params = read_RF_inputs(self.form)
    outDir = params["outputDir"]

    try:
        os.mkdir(outDir)
    except OSError:
        pass

    if tempPath == "writeOnly":
        usePath = Path(outDir + "/rfWorkbench.cwPar")
    else:
        usePath = Path(tempPath + "/rfWorkbench.cwPar")

    with open(usePath, "w") as f:
        f.write("""
// ================================================================================
// LDPM WORKBENCH - github.com/Concrete-Chrono-Development/chrono-preprocessor
//
// Copyright (c) 2023 
// All rights reserved. 
//
// Use of the code that generated this file is governed by a BSD-style license that
// can be found in the LICENSE file at the top level of the distribution and at
// github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
//
// ================================================================================
// Random Field Workbench Parameter File
// ================================================================================
// 
// RF Workbench developed by Brno University of Technology
// created by Jan Elias
// jan.elias@vut.cz
// 2020
// ================================================================================
        \n\n""")
        domain = [
            f"{params['x_range'][1]:.2f} mm",
            f"{params['y_range'][1]:.2f} mm",
            f"{params['z_range'][1]:.2f} mm",
        ]
        f.write("numRealizations = " + str(params["numRealizations"]) + "\n")
        f.write("seeds = " + params["seeds"] + "\n")
        f.write("periodic = " + str(params["periodic"]) + "\n")
        f.write("x_range = " + str(params["x_range"]) + "\n")
        f.write("y_range = " + str(params["y_range"]) + "\n")
        f.write("z_range = " + str(params["z_range"]) + "\n")
        f.write("domain = " + str(domain) + "\n")
        f.write("corr_l = " + str(params["corr_l"]) + "\n")
        f.write("corr_f = " + params["corr_f"] + "\n")
        f.write("dist_type = " + params["dist_type"] + "\n")
        f.write("grid_spacing = " + str(params["grid_spacing"]) + "\n")
        f.write("grid_file = " + str(params["grid_file"]) + "\n")
        f.write("sparse = " + str(params["sparse"]) + "\n")
        f.write("rank_correlation = " + str(params["rank_correlation"]) + "\n")
        f.write("elasticity_mean = " + str(params["elasticity_mean"]) + "\n")
        f.write("elasticity_std = " + str(params["elasticity_std"]) + "\n")
        f.write("strength_mean = " + str(params["strength_mean"]) + "\n")
        f.write("strength_std = " + str(params["strength_std"]) + "\n")
        f.write("fracture_mean = " + str(params["fracture_mean"]) + "\n")
        f.write("fracture_std = " + str(params["fracture_std"]) + "\n")
        f.write("cross_correlation = " + json.dumps(params["cross_correlation"]) + "\n")
        f.write("rfFieldInputFile = " + params["rfFieldInputFile"] + "\n")
        f.write("dataFilesGen = " + str(params["dataFilesGen"]) + "\n")
        f.write("visFilesGen = " + str(params["visFilesGen"]) + "\n")
        f.write("rfAssignments = " + json.dumps(params["rfAssignments"]) + "\n")
        f.write("modelType = " + params["modelType"] + "\n")
        f.write("outputDir = " + outDir + "\n")

    print("RF parameters written to file")
