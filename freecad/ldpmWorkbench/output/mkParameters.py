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
## ===========================================================================

import json
import os
from pathlib import Path

# Importing: input
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs                    import read_LDPMCSL_inputs, read_rf_generation_inputs
from freecad.ldpmWorkbench.input.read_interlayer_inputs            import read_interlayer_inputs
from freecad.ldpmWorkbench.input.read_SPHDEM_inputs                     import read_SPHDEM_inputs


def _normalize_module(module):
    if module is None:
        return "LDPM"
    name = str(module).strip().upper()
    aliases = {
        "LDPMCSL": "LDPM",
        "CSL": "LDPM",
        "P-LDPM": "PLDPM",
        "P_LDPM": "PLDPM",
        "3DCP": "3DCPLDPM",
        "3DCP-LDPM": "3DCPLDPM",
        "3DCP_LDPM": "3DCPLDPM",
    }
    return aliases.get(name, name)


def mkParameters(self, elementSet, tempPath, module=None):

    module_name = _normalize_module(module)

    write_multimat = module_name == "PLDPM"
    write_phase_particles = module_name == "PLDPM"
    write_mix_phases = module_name == "PLDPM"
    write_htc = module_name == "LDPM"
    write_periodic = module_name == "LDPM"
    write_interlayer = module_name == "3DCPLDPM"
    write_sweep_orient = module_name == "3DCPLDPM"
    write_fiber = module_name != "PLDPM"
    write_rf = module_name != "PLDPM"

    # Read in inputs from input panel
    if elementSet == "LDPMCSL":
        [setupFile, constitutiveEQ, matParaSet, \
            numCPU, numIncrements,maxIter,placementAlg,\
            geoType, dimensions, cadFile,\
            minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, fullerCoef, sieveCurveDiameter, sieveCurvePassing,\
            wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
            cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
            fillerC, fillerDensity, airFrac2,\
            htcToggle, htcLength,\
            fiberToggle, fiberCutting, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberFile, fiberIntersections, fiberOutputFiles,\
            multiMatToggle,aggFile,multiMatFile,multiMatRule,\
            grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP,\
            grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP,\
            grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP,\
            phaseMode,\
            mixPhaseMode, phaseFillerContent, phaseFillerDensity,\
            particlePhaseMode, phaseMinPar, phaseMaxPar, phaseOffsetCoefList,\
            periodicToggle,particleOffsetCoef,\
            outDir, dataFilesGen, visFilesGen, singleTetGen, modelType,\
            orientationPathType_sweep3dp, orientationPathSketchName_sweep3dp, orientationSegments_sweep3dp] = read_LDPMCSL_inputs(self.form)
        interlayer_params = read_interlayer_inputs(self.form) if write_interlayer else None
        rf_params = (
            read_rf_generation_inputs(
                self.form,
                job_plan=getattr(self, "_rfJobPlan", None),
                field_dir=getattr(self, "_rfFieldDir", None),
            )
            if write_rf
            else None
        )
    else:
        [setupFile, \
            numCPU, numIncrements,maxIter,placementAlg,\
            geoType, dimensions, cadFile,\
            minPar, maxPar, fullerCoef, sieveCurveDiameter, sieveCurvePassing, minDistCoef,\
            wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
            cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
            fillerC, fillerDensity, airFrac2,\
            outDir, modelType] = read_SPHDEM_inputs(self.form)


    # Make output directory if does not exist
    try:
        os.mkdir(outDir)
    except:
        pass

    # If tempPath is "writeOnly" (meaning we only write the parameter file and don't generate the model) then write to default location
    if tempPath == "writeOnly":
        usePath = Path(outDir + "/ldpmWorkbench.cwPar")
    else:
        usePath = Path(tempPath + "/ldpmWorkbench.cwPar")

    # Write parameters to file
    if elementSet == "LDPMCSL":
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
// LDPM Workbench Parameter File
// ================================================================================
// 
// LDPM Workbench developed by Northwestern University
//
// ================================================================================
        \n\n""")
            f.write("module = " + module_name + "\n")
            f.write("numCPU = " + str(numCPU) + "\n")
            f.write("numIncrements = " + str(numIncrements) + "\n")
            f.write("maxIter = " + str(maxIter) + "\n")
            f.write("placementAlg = " + placementAlg + "\n")
            f.write("geoType = " + geoType + "\n")
            f.write("dimensions = " + str(dimensions) + "\n")
            f.write("cadFile = " + cadFile + "\n")
            f.write("minPar_sim = " + str(minPar_sim) + "\n")
            f.write("maxPar_sim = " + str(maxPar_sim) + "\n")
            f.write("minPar_exp = " + str(minPar_exp) + "\n")
            f.write("maxPar_exp = " + str(maxPar_exp) + "\n")
            f.write("fullerCoef = " + str(fullerCoef) + "\n")
            f.write("sieveCurveDiameter = " + str(sieveCurveDiameter) + "\n")
            f.write("sieveCurvePassing = " + str(sieveCurvePassing) + "\n")
            f.write("wcRatio = " + str(wcRatio) + "\n")
            f.write("densityWater = " + str(densityWater) + "\n")
            f.write("cementC = " + str(cementC) + "\n")
            f.write("flyashC = " + str(flyashC) + "\n")
            f.write("silicaC = " + str(silicaC) + "\n")
            f.write("scmC = " + str(scmC) + "\n")
            f.write("cementDensity = " + str(cementDensity) + "\n")
            f.write("flyashDensity = " + str(flyashDensity) + "\n")
            f.write("silicaDensity = " + str(silicaDensity) + "\n")
            f.write("scmDensity = " + str(scmDensity) + "\n")
            f.write("airFrac1 = " + str(airFrac1) + "\n")
            if write_mix_phases:
                f.write("fillerC = " + str(fillerC) + "\n")
                f.write("fillerDensity = " + str(fillerDensity) + "\n")

            if write_htc:
                f.write("htcToggle = " + htcToggle + "\n")
                f.write("htcLength = " + str(htcLength) + "\n")

            if write_fiber:
                f.write("fiberToggle = " + fiberToggle + "\n")
                f.write("fiberCutting = " + fiberCutting + "\n")
                f.write("fiberDiameter = " + str(fiberDiameter) + "\n")
                f.write("fiberLength = " + str(fiberLength) + "\n")
                f.write("fiberVol = " + str(fiberVol) + "\n")
                f.write("fiberOrientation1 = " + str(fiberOrientation1) + "\n")
                f.write("fiberOrientation2 = " + str(fiberOrientation2) + "\n")
                f.write("fiberOrientation3 = " + str(fiberOrientation3) + "\n")
                f.write("fiberPref = " + str(fiberPref) + "\n")
                f.write("fiberFile = " + fiberFile + "\n")
                f.write("fiberIntersections = " + str(fiberIntersections) + "\n")
                f.write("fiberOutputFiles = " + str(fiberOutputFiles) + "\n")

            if write_sweep_orient:
                f.write("orientationPathType_sweep3dp = " + str(orientationPathType_sweep3dp) + "\n")
                f.write("orientationPathSketchName_sweep3dp = " + str(orientationPathSketchName_sweep3dp) + "\n")
                f.write("orientationSegments_sweep3dp = " + str(orientationSegments_sweep3dp) + "\n")

            if write_multimat:
                f.write("multiMatToggle = " + multiMatToggle + "\n")
                f.write("multiMatFile = " + multiMatFile + "\n")
                f.write("aggFile = " + aggFile + "\n")
                f.write("multiMatRule = " + str(multiMatRule) + "\n")
                f.write("grainAggMin = " + str(grainAggMin) + "\n")
                f.write("grainAggMax = " + str(grainAggMax) + "\n")
                f.write("grainAggFuller = " + str(grainAggFuller) + "\n")
                f.write("grainAggSieveD = " + str(grainAggSieveD) + "\n")
                f.write("grainAggSieveP = " + str(grainAggSieveP) + "\n")
                f.write("grainITZMin = " + str(grainITZMin) + "\n")
                f.write("grainITZMax = " + str(grainITZMax) + "\n")
                f.write("grainITZFuller = " + str(grainITZFuller) + "\n")
                f.write("grainITZSieveD = " + str(grainITZSieveD) + "\n")
                f.write("grainITZSieveP = " + str(grainITZSieveP) + "\n")
                f.write("grainBinderMin = " + str(grainBinderMin) + "\n")
                f.write("grainBinderMax = " + str(grainBinderMax) + "\n")
                f.write("grainBinderFuller = " + str(grainBinderFuller) + "\n")
                f.write("grainBinderSieveD = " + str(grainBinderSieveD) + "\n")
                f.write("grainBinderSieveP = " + str(grainBinderSieveP) + "\n")
                f.write("phaseMode = " + str(phaseMode) + "\n")

            if write_mix_phases:
                f.write("mixPhaseMode = " + str(mixPhaseMode) + "\n")
                phaseFillerVolFrac = [float(c) for c in phaseFillerContent]
                f.write("phaseFillerVolFrac = " + str(phaseFillerVolFrac) + "\n")
                f.write("phaseFillerContent = " + str(phaseFillerContent) + "\n")
                f.write("phaseFillerDensity = " + str(phaseFillerDensity) + "\n")

            if write_phase_particles:
                particlePhaseMode = 0
                phaseMinPar = []
                phaseMaxPar = []
                phaseOffsetCoefList = []
                particles_form = next((item for item in self.form if hasattr(item, "phase1MinPar")), None)
                if particles_form is not None:
                    if hasattr(particles_form, "phaseSelect"):
                        _pidx = int(particles_form.phaseSelect.currentIndex())
                        particlePhaseMode = {0: 0, 1: 2, 2: 3}.get(_pidx, 0)
                    for n in range(1, 4):
                        _wmin = getattr(particles_form, f"phase{n}MinPar", None)
                        _wmax = getattr(particles_form, f"phase{n}MaxPar", None)
                        _woff = getattr(particles_form, f"phase{n}OffsetCoef", None)
                        try:
                            phaseMinPar.append(float(_wmin.value()) if _wmin is not None else 0.0)
                        except Exception:
                            phaseMinPar.append(0.0)
                        try:
                            phaseMaxPar.append(float(_wmax.value()) if _wmax is not None else 0.0)
                        except Exception:
                            phaseMaxPar.append(0.0)
                        try:
                            phaseOffsetCoefList.append(float(_woff.value()) if _woff is not None else 0.2)
                        except Exception:
                            phaseOffsetCoefList.append(0.2)
                f.write("particlePhaseMode = " + str(particlePhaseMode) + "\n")
                f.write("phaseMinPar = " + str(phaseMinPar) + "\n")
                f.write("phaseMaxPar = " + str(phaseMaxPar) + "\n")
                f.write("phaseOffsetCoef = " + str(phaseOffsetCoefList) + "\n")

            if write_periodic:
                f.write("periodicToggle = " + periodicToggle + "\n")

            f.write("particleOffsetCoef = " + str(particleOffsetCoef) + "\n")
            f.write("dataFilesGen = " + str(dataFilesGen) + "\n")
            f.write("visFilesGen = " + str(visFilesGen) + "\n")
            f.write("singleTetGen = " + str(singleTetGen) + "\n")
            if write_rf and rf_params is not None:
                f.write("rfToggle = " + str(rf_params["rfToggle"]) + "\n")
                f.write("numSamples = " + str(rf_params["numSamples"]) + "\n")
                f.write("rfFieldDir = " + str(rf_params["rfFieldDir"]) + "\n")
                f.write("rfAssignments = " + json.dumps(rf_params["rfAssignments"]) + "\n")
                f.write("rfJobPlan = " + json.dumps(rf_params["rfJobPlan"]) + "\n")

            if write_interlayer and interlayer_params is not None:
                interlayer_type = interlayer_params["interlayerType"]
                f.write("interlayerToggle = " + ("Yes" if interlayer_params["enabled"] else "No") + "\n")
                f.write("interlayerType = " + interlayer_type + "\n")
                f.write("interfaceThickness = " + str(interlayer_params["interfaceThickness"]) + "\n")
                f.write("bulkMf = " + str(interlayer_params["bulkMf"]) + "\n")
                if interlayer_type == "Custom":
                    f.write("customDefinition = " + json.dumps(interlayer_params.get("customDefinition", "")) + "\n")
                elif interlayer_type == "Multidirectional Interlayer":
                    f.write("firstLayerThickness = " + str(interlayer_params["firstLayerThickness"]) + "\n")
                    f.write("layerThickness = " + str(interlayer_params["layerThickness"]) + "\n")
                    f.write("layerWidth = " + str(interlayer_params.get("layerWidth", 1.0)) + "\n")
                    f.write("xMf = " + str(interlayer_params.get("xMf", 2)) + "\n")
                    f.write("yMf = " + str(interlayer_params.get("yMf", 3)) + "\n")
                    f.write("zMf = " + str(interlayer_params.get("zMf", 4)) + "\n")
                    f.write("overlapMf = " + str(interlayer_params.get("overlapMf", 5)) + "\n")
                    for i, direction in enumerate(interlayer_params.get("multiDirections", []), start=1):
                        f.write("multiDir" + str(i) + "Toggle = " + ("Yes" if direction.get("enabled") else "No") + "\n")
                        f.write("multiDir" + str(i) + "Axis = " + direction.get("axis", "X") + "\n")
                        f.write("multiDir" + str(i) + "Mode = " + direction.get("mode", "Height") + "\n")
                else:
                    f.write("firstLayerThickness = " + str(interlayer_params["firstLayerThickness"]) + "\n")
                    f.write("layerThickness = " + str(interlayer_params["layerThickness"]) + "\n")
                    f.write("interlayerAxis = " + interlayer_params.get("axis", "Z") + "\n")
                    f.write("interlayerMf = " + str(interlayer_params.get("interlayerMf", 2)) + "\n")

            f.write("modelType = " + modelType + "\n")
            f.write("outputDir = " + outDir + "\n")
        print("Parameters written to file")


    elif elementSet == "SPHDEM":
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
// LDPM Workbench Parameter File
// ================================================================================
// 
// LDPM Workbench developed by Northwestern University
//
// ================================================================================
        \n\n""")
            f.write("module = SPHDEM\n")
            f.write("numCPU = " + str(numCPU) + "\n")
            f.write("numIncrements = " + str(numIncrements) + "\n")
            f.write("maxIter = " + str(maxIter) + "\n")
            f.write("placementAlg = " + placementAlg + "\n")
            f.write("geoType = " + geoType + "\n")
            f.write("dimensions = " + str(dimensions) + "\n")
            f.write("cadFile = " + cadFile + "\n")
            f.write("minPar = " + str(minPar) + "\n")
            f.write("maxPar = " + str(maxPar) + "\n")
            f.write("fullerCoef = " + str(fullerCoef) + "\n")
            f.write("sieveCurveDiameter = " + str(sieveCurveDiameter) + "\n")
            f.write("sieveCurvePassing = " + str(sieveCurvePassing) + "\n")
            f.write("particleOffsetCoef = " + str(minDistCoef) + "\n")
            f.write("wcRatio = " + str(wcRatio) + "\n")
            f.write("densityWater = " + str(densityWater) + "\n")
            f.write("cementC = " + str(cementC) + "\n")
            f.write("flyashC = " + str(flyashC) + "\n")
            f.write("silicaC = " + str(silicaC) + "\n")
            f.write("scmC = " + str(scmC) + "\n")
            f.write("cementDensity = " + str(cementDensity) + "\n")
            f.write("flyashDensity = " + str(flyashDensity) + "\n")
            f.write("silicaDensity = " + str(silicaDensity) + "\n")
            f.write("scmDensity = " + str(scmDensity) + "\n")
            f.write("airFrac1 = " + str(airFrac1) + "\n")
            f.write("modelType = " + modelType + "\n")
            f.write("outputDir = " + outDir + "\n")

        print("Parameters written to file")
    
    else:
        print("Error: Element set not recognized")
