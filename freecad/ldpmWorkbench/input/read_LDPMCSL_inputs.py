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
## This file contains the function to read the inputs from the GUI and return
## them to the main script.
##
## ===========================================================================

import os

CAD_EXTENSIONS = frozenset({"brep", "brp", "iges", "igs", "step", "stp"})
MESH_EXTENSIONS = frozenset({"inp", "vtk", "vtu"})

_CAD_GLOB = "*.brep *.brp *.iges *.igs *.step *.stp *.BREP *.BRP *.IGES *.IGS *.STEP *.STP"
_MESH_GLOB = "*.inp *.vtk *.vtu *.INP *.VTK *.VTU"

CAD_FILE_DIALOG_FILTER = (
    f"Supported formats ({_CAD_GLOB});;"
    "                    BREP format       (*.brep *.brp *.BREP *.BRP);; "
    "                    IGES format       (*.iges *.igs *.IGES *.IGS);; "
    "                    STEP format       (*.step *.stp *.STEP *.STP)"
)

GEOMETRY_FILE_DIALOG_FILTER = (
    f"Supported formats ({_CAD_GLOB} {_MESH_GLOB});;"
    "                    BREP format       (*.brep *.brp *.BREP *.BRP);; "
    "                    IGES format       (*.iges *.igs *.IGES *.IGS);; "
    "                    STEP format       (*.step *.stp *.STEP *.STP);; "
    "                    Abaqus/CalcuLix format  (*.inp *.INP);; "
    "                    VTK Legacy/modern format (*.vtk *.vtu *.VTK *.VTU)"
)


def file_extension(path):
    return os.path.splitext(path)[1].lstrip(".").lower()


def is_cad_geometry_file(path):
    return file_extension(path) in CAD_EXTENSIONS


def is_mesh_geometry_file(path):
    return file_extension(path) in MESH_EXTENSIONS


def normalize_sweep3dp_path_type_index(path_type_idx):
    legacy_to_current = {0: 0, 2: 1, 4: 2, 5: 3}
    try:
        idx = int(path_type_idx)
    except (TypeError, ValueError):
        return 0
    if idx in legacy_to_current:
        return legacy_to_current[idx]
    if idx in (1, 3):
        return 0
    return max(0, min(3, idx))


def _form_with_attr(form, attr):

    for item in form:
        if hasattr(item, attr):
            return item
    return None


def read_rf_generation_inputs(form, job_plan=None, field_dir=None):

    num_samples = 1
    if form and hasattr(form[0], "numSampleBox"):
        box = form[0].numSampleBox
        if hasattr(box, "value"):
            try:
                num_samples = max(1, int(box.value()))
            except (TypeError, ValueError):
                num_samples = 1

    rf_form = _form_with_attr(form, "rfToggle")
    if rf_form is None:
        return {
            "rfToggle": "Off",
            "numSamples": num_samples,
            "rfFieldDir": "",
            "rfAssignments": "",
            "rfJobPlan": {},
        }

    toggle = str(rf_form.rfToggle.currentText()).strip()
    resolved_dir = field_dir if field_dir not in (None, "") else rf_form.rfFieldDir.text().strip()
    assignments = rf_form.rfAssignmentList.toPlainText().strip()

    plan_out = {}
    if job_plan:
        for sample, realizations in job_plan.items():
            plan_out[str(int(sample))] = [int(r) for r in realizations]

    return {
        "rfToggle": toggle,
        "numSamples": num_samples,
        "rfFieldDir": resolved_dir,
        "rfAssignments": assignments,
        "rfJobPlan": plan_out,
    }


def _widget_float(widget, default=0.0):
    if widget is None:
        return float(default)
    if hasattr(widget, "value"):
        try:
            return float(widget.value() or default)
        except (TypeError, ValueError):
            pass
    text = ""
    if hasattr(widget, "text"):
        try:
            text = widget.text()
        except Exception:
            text = ""
    elif hasattr(widget, "cleanText"):
        try:
            text = widget.cleanText()
        except Exception:
            text = ""
    if not text:
        return float(default)
    try:
        return float(str(text).split(" ")[0].strip())
    except (TypeError, ValueError):
        return float(default)


def _widget_text(widget, default=""):
    if widget is None:
        return default
    if hasattr(widget, "text"):
        try:
            return widget.text()
        except Exception:
            return default
    if hasattr(widget, "cleanText"):
        try:
            return widget.cleanText()
        except Exception:
            return default
    return default


def _combo_phase_mode(combo, select_offset=False, default=3):
    if combo is None:
        return default
    idx = int(combo.currentIndex())
    if select_offset:
        mapping = {0: default, 1: 2, 2: 3}
    else:
        mapping = {0: 2, 1: 3}
    mode = mapping.get(idx, default)
    return mode


def read_LDPMCSL_inputs(form):

    # Basic Settings
    setupFile           = form[0].setupFile.text()

    # Constitutive Equation Settings
    constitutiveEQ      = form[0].constEQ.currentText()
    if form[0].constEQ.currentIndex() == 0:
        matParaSet      = form[0].matParaSet4EQ1.currentText()
    if form[0].constEQ.currentIndex() == 1:
        matParaSet      = form[0].matParaSet4EQ2.currentText()
    if form[0].constEQ.currentIndex() == 2:
        matParaSet      = form[0].matParaSet4EQ3.currentText()
    if form[0].constEQ.currentIndex() == 3:
        matParaSet      = form[0].matParaSet4EQ4.currentText()
    if form[0].constEQ.currentIndex() == 4:
        matParaSet      = form[0].matParaSet4EQ5.currentText()
    if form[0].constEQ.currentIndex() == 5:
        matParaSet      = form[0].matParaSet4EQ6.currentText()
    if form[0].constEQ.currentIndex() == 6:
        matParaSet      = form[0].matParaSet4EQ7.currentText()
    if form[0].constEQ.currentIndex() == 7:
        matParaSet      = form[0].matParaSet4EQ8.currentText()

    # Simulation Settings
    numCPU              = form[0].numCPUbox.value()
    numIncrements       = form[0].numPIncBox.value()
    maxIter             = form[0].numIncBox.value()
    placementAlg        = form[0].placementAlg.currentText()

    # Geometry Settings
    geoType             = form[1].geometryType.currentText()
    dimensions = []
    if geoType == "Truncated Cone":
        dimensions.append(form[1].truncConeHeight.text())
        dimensions.append(form[1].truncConeRadBot.text())
        dimensions.append(form[1].truncConeRadTop.text())
    if geoType == "Box":
        dimensions.append(form[1].boxLength.text())
        dimensions.append(form[1].boxWidth.text())
        dimensions.append(form[1].boxHeight.text())
    if geoType == "Cylinder":
        dimensions.append(form[1].cylinderHeight.text())
        dimensions.append(form[1].cylinderRadius.text())
    if geoType == "Cone":
        dimensions.append(form[1].coneHeight.text())
        dimensions.append(form[1].coneRadius1.text())
        dimensions.append("0 mm")
    if geoType == "Sphere":
        dimensions.append(form[1].sphereRadius.text())
    if geoType == "Ellipsoid":
        dimensions.append(form[1].ellipsoidRadius1.text())
        dimensions.append(form[1].ellipsoidRadius2.text())
        dimensions.append(form[1].ellipsoidRadius3.text())
        dimensions.append(form[1].ellipsoidAngle1.text())
        dimensions.append(form[1].ellipsoidAngle2.text())
        dimensions.append(form[1].ellipsoidAngle3.text())
    if geoType == "Arbitrary Prism":
        dimensions.append(form[1].prismCircumradius.text())
        dimensions.append(form[1].prismHeight.text())
        dimensions.append(form[1].prismPolygon.text())
    if geoType == "Notched Prism - Square":
        dimensions.append(form[1].notchBoxLength.text())
        dimensions.append(form[1].notchBoxWidth.text())
        dimensions.append(form[1].notchBoxHeight.text())
        dimensions.append(form[1].notchWidth.text())
        dimensions.append(form[1].notchDepth.text())
    if geoType == "Notched Prism - Semi Circle":
        dimensions.append(form[1].notchSCBoxLength.text())
        dimensions.append(form[1].notchSCBoxWidth.text())
        dimensions.append(form[1].notchSCBoxHeight.text())
        dimensions.append(form[1].notchSCWidth.text())
        dimensions.append(form[1].notchSCDepth.text())
    if geoType == "Notched Prism - Semi Ellipse":
        dimensions.append(form[1].notchSEBoxLength.text())
        dimensions.append(form[1].notchSEBoxWidth.text())
        dimensions.append(form[1].notchSEBoxHeight.text())
        dimensions.append(form[1].notchSEWidth.text())
        dimensions.append(form[1].notchSEDepth.text())
        dimensions.append(form[1].notchSEtipDepth.text())
    if geoType == "Dogbone":
        dimensions.append(form[1].dogboneLength.text())
        dimensions.append(form[1].dogboneWidth.text())
        dimensions.append(form[1].dogboneThickness.text())
        dimensions.append(form[1].gaugeLength.text())
        dimensions.append(form[1].gaugeWidth.text())
        dimensions.append(form[1].dogboneType.currentText())
    if geoType == "Custom":
        if hasattr(form[1], 'selectedObject'):
            dimensions.append(form[1].selectedObject.toPlainText().strip())
        else:
            dimensions.append("")
    if geoType == "Sweep-3DP":
        # Profile type: 0 = Rectangular, 1 = CAD file
        dimensions.append(str(form[1].sweep3dpProfileType.currentIndex()))
        # If rectangular profile
        if form[1].sweep3dpProfileType.currentIndex() == 0:
            dimensions.append(form[1].sweep3dpLayerWidth.text())
            dimensions.append(form[1].sweep3dpLayerHeight.text())
            dimensions.append("")  # No profile file
        else:
            dimensions.append("")  # No layer width
            dimensions.append("")  # No layer height
            dimensions.append(form[1].sweep3dpProfileFile.toPlainText())
        pathTypeIdx = form[1].sweep3dpPathType.currentIndex()
        dimensions.append(str(pathTypeIdx))

        # Store all possible params so downstream can switch by index safely:
        # [distance, diameter, side, cadPath, sketchName, numLayers]
        if pathTypeIdx == 0:
            distTxt = form[1].sweep3dpPathDistance.text()
            if not distTxt or distTxt.strip() == "":
                distTxt = "100 mm"
            dimensions.append(distTxt)
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            numLayers = int(form[1].sweep3dpNumLayers.value() or 1)
            dimensions.append(str(numLayers))
        elif pathTypeIdx == 1:
            dimensions.append("")
            dimensions.append("")
            sideTxt = form[1].sweep3dpPathSide.text()
            if not sideTxt or sideTxt.strip() == "":
                sideTxt = "50 mm"
            dimensions.append(sideTxt)
            dimensions.append("")
            dimensions.append("")
            numLayers = int(form[1].sweep3dpNumLayersSquare.value() or 1)
            dimensions.append(str(numLayers))
        elif pathTypeIdx == 2:
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            sketch_name = form[1].sweep3dpPathSketchName.text()
            dimensions.append(sketch_name)
            numLayers = int(form[1].sweep3dpNumLayersSketch.value() or 1)
            dimensions.append(str(numLayers))
        else:
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            dimensions.append("")
            numLayers = int(form[1].sweep3dpNumSlicesRaster.value() or 1)
            dimensions.append(str(numLayers))

            rasterLoops = int(form[1].sweep3dpRasterLoops.value() or 1)
            rasterSpacing = form[1].sweep3dpRasterSpacing.text()
            rasterCornerFillet = form[1].sweep3dpRasterCornerFillet.text()
            rasterPathLength = form[1].sweep3dpRasterPathLength.text() if hasattr(form[1], "sweep3dpRasterPathLength") else ""
            if not rasterSpacing or rasterSpacing.strip() == "":
                rasterSpacing = "5 mm"
            if not rasterCornerFillet or rasterCornerFillet.strip() == "":
                rasterCornerFillet = "0 mm"
            if not rasterPathLength or rasterPathLength.strip() == "":
                rasterPathLength = "100 mm"
            dimensions.append(str(rasterLoops))
            dimensions.append(rasterSpacing)
            dimensions.append(str(numLayers))
            dimensions.append(str(float(form[1].sweep3dpSliceDir1.value() or 0.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir2.value() or 90.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir3.value() or 0.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir4.value() or 90.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir5.value() or 0.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir6.value() or 90.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir7.value() or 0.0)))
            dimensions.append(str(float(form[1].sweep3dpSliceDir8.value() or 90.0)))
            dimensions.append(rasterCornerFillet)
            dimensions.append(rasterPathLength)

    cadFile             = form[1].cadFile.toPlainText()

    # Particle Settings
    particlePhaseMode = 0
    phaseMinPar = [0.0] * 3
    phaseMaxPar = [0.0] * 3
    phaseOffsetCoefList = [0.2] * 3
    if hasattr(form[2], "minPar_sim"):
        minPar_sim = float(form[2].minPar_sim.value() or 0)
        maxPar_sim = float(form[2].maxPar_sim.value() or 0)
    elif hasattr(form[2], "phase1MinPar"):
        particlePhaseMode = _combo_phase_mode(
            getattr(form[2], "phaseSelect", None), select_offset=True, default=0
        )
        n_phases = particlePhaseMode if particlePhaseMode in (2, 3) else 1
        for n in range(1, 4):
            phaseMinPar[n - 1] = _widget_float(getattr(form[2], f"phase{n}MinPar", None))
            phaseMaxPar[n - 1] = _widget_float(getattr(form[2], f"phase{n}MaxPar", None))
            phaseOffsetCoefList[n - 1] = _widget_float(
                getattr(form[2], f"phase{n}OffsetCoef", None), 0.2
            )
        active_mins = phaseMinPar[:n_phases]
        active_maxs = phaseMaxPar[:n_phases]
        minPar_sim = min(active_mins) if active_mins else 0.0
        maxPar_sim = max(active_maxs) if active_maxs else 0.0
    else:
        minPar_sim = 0.0
        maxPar_sim = 0.0
    # Mix Design
    minPar_exp          = float(form[3].minPar_exp.value() or 0)
    maxPar_exp          = float(form[3].maxPar_exp.value() or 0)
    fullerCoef          = float(form[3].fullerCoef.value() or 0)  
    sieveCurveDiameter  = form[3].sieveDiameters.text()        
    sieveCurvePassing   = form[3].sievePassing.text() 
    wcRatio             = float(form[3].wcRatio.value() or 0)
    densityWater        = float(form[3].waterDensity.text() or 0)
    cementC             = float(form[3].cementContent.text() or 0)
    flyashC             = float(form[3].flyashContent.text() or 0)
    silicaC             = float(form[3].silicaContent.text() or 0)
    scmC                = float(form[3].scmContent.text() or 0)
    if hasattr(form[3], "fillerVolFrac"):
        fillerC = _widget_float(getattr(form[3], "fillerVolFrac", None))
        fillerDensity = 1.0
    else:
        fillerC             = float(form[3].fillerContent.text() or 0)
        fillerDensity       = float(form[3].fillerDensity.text() or 0)
    cementDensity       = float(form[3].cementDensity.text() or 0)
    flyashDensity       = float(form[3].flyashDensity.text() or 0)
    silicaDensity       = float(form[3].silicaDensity.text() or 0)
    scmDensity          = float(form[3].scmDensity.text() or 0)
    airFrac1            = float(form[3].airFrac.value() or 0)
    if hasattr(form[3], 'airFracArb'):
        airFrac2            = float(form[3].airFracArb.value() or 0)
    else:
        airFrac2            = 0.0

    # Additional Parameters - HTC Parameters
    htcForm = _form_with_attr(form, "HTCtoggle")
    if htcForm is not None:
        HTCtoggle           = htcForm.HTCtoggle.currentText()
        HTClength           = htcForm.HTClength.text()
        HTClength           = float(HTClength.split(" ")[0].strip())
    else:
        HTCtoggle           = "Off"
        HTClength           = 0.0

    reinfForm = _form_with_attr(form, "fiberToggle")
    if reinfForm is None:
        reinfForm = _form_with_attr(form, "fiberToggle_sweep3dp")
    
    # Additional Parameters - Fiber Reinforcement Parameters
    if reinfForm is not None and geoType == "Sweep-3DP" and hasattr(reinfForm, 'fiberToggle_sweep3dp'):
        fiberToggle         = reinfForm.fiberToggle_sweep3dp.currentText()
        fiberCutting        = reinfForm.fiberCutting_sweep3dp.currentText()
        fiberDiameter       = float(reinfForm.fiberDiameter_sweep3dp.value() or 0)
        fiberLength         = float(reinfForm.fiberLength_sweep3dp.value() or 0)
        fiberVol            = float(reinfForm.fiberVol_sweep3dp.value() or 0)
        fiberOrientation1   = 0
        fiberOrientation2   = 0
        fiberOrientation3   = 0
        fiberPref           = float(reinfForm.fiberPref_sweep3dp.value() or 0)
        fiberFile           = reinfForm.fiberFile.text()
        fiberIntersections  = reinfForm.fiberIntersections_sweep3dp.currentText()
        fiberOutputFiles    = reinfForm.fiberOutputFiles_sweep3dp.currentText() if hasattr(reinfForm, "fiberOutputFiles_sweep3dp") else "Off"
    elif reinfForm is not None:
        fiberToggle         = reinfForm.fiberToggle.currentText()
        fiberCutting        = reinfForm.fiberCutting.currentText()
        fiberDiameter       = reinfForm.fiberDiameter.text()
        fiberDiameter       = float(fiberDiameter.split(" ")[0].strip())
        fiberLength         = reinfForm.fiberLength.text()
        fiberLength         = float(fiberLength.split(" ")[0].strip())
        fiberVol            = float(reinfForm.fiberVol.value() or 0)
        fiberOrientation1   = float(reinfForm.fiberOrien1.value() or 0)
        fiberOrientation2   = float(reinfForm.fiberOrien2.value() or 0)
        fiberOrientation3   = float(reinfForm.fiberOrien3.value() or 0)
        fiberPref           = float(reinfForm.fiberPref.value() or 0)
        fiberFile           = reinfForm.fiberFile.text()
        fiberIntersections  = reinfForm.fiberIntersections.currentText()
        fiberOutputFiles    = reinfForm.fiberOutputFiles.currentText() if hasattr(reinfForm, "fiberOutputFiles") else "Off"
    else:
        fiberToggle         = "Off"
        fiberCutting        = "Off"
        fiberDiameter       = 0.0
        fiberLength         = 0.0
        fiberVol            = 0.0
        fiberOrientation1   = 0.0
        fiberOrientation2   = 0.0
        fiberOrientation3   = 0.0
        fiberPref           = 0.0
        fiberFile           = ""
        fiberIntersections  = "Off"
        fiberOutputFiles    = "Off"

    # Additional Parameters - Multi-Material Parameters
    multiMatForm = _form_with_attr(form, "multiMatToggle")
    if multiMatForm is not None:
        multiMatToggle      = multiMatForm.multiMatToggle.currentText()
        multiMatFile        = multiMatForm.multiMatFile.text()
        aggFile             = multiMatForm.aggFile.text()
        multiMatRule        = int(multiMatForm.multiMatRule.value() or 9)
        phaseMode           = _combo_phase_mode(
            getattr(multiMatForm, "multiMatPhaseSelect", None), select_offset=False, default=3
        )

        grainAggMin         = _widget_float(getattr(multiMatForm, "grainAggMin", None))
        grainAggMax         = _widget_float(getattr(multiMatForm, "grainAggMax", None))
        grainAggFuller      = _widget_float(getattr(multiMatForm, "grainAggFuller", None))
        grainAggSieveD      = _widget_text(getattr(multiMatForm, "grainAggSieveD", None))
        grainAggSieveP      = _widget_text(getattr(multiMatForm, "grainAggSieveP", None))

        grainITZMin         = _widget_float(getattr(multiMatForm, "grainITZMin", None))
        grainITZMax         = _widget_float(getattr(multiMatForm, "grainITZMax", None))
        grainITZFuller      = _widget_float(getattr(multiMatForm, "grainITZFuller", None))
        grainITZSieveD      = _widget_text(getattr(multiMatForm, "grainITZSieveD", None))
        grainITZSieveP      = _widget_text(getattr(multiMatForm, "grainITZSieveP", None))

        grainBinderMin      = _widget_float(getattr(multiMatForm, "grainBinderMin", None))
        grainBinderMax      = _widget_float(getattr(multiMatForm, "grainBinderMax", None))
        grainBinderFuller   = _widget_float(getattr(multiMatForm, "grainBinderFuller", None))
        grainBinderSieveD   = _widget_text(getattr(multiMatForm, "grainBinderSieveD", None))
        grainBinderSieveP   = _widget_text(getattr(multiMatForm, "grainBinderSieveP", None))
    else:
        multiMatToggle      = "Off"
        multiMatFile        = ""
        aggFile             = ""
        multiMatRule        = 9
        phaseMode           = 3
        grainAggMin         = 0.0
        grainAggMax         = 0.0
        grainAggFuller      = 0.0
        grainAggSieveD      = ""
        grainAggSieveP      = ""
        grainITZMin         = 0.0
        grainITZMax         = 0.0
        grainITZFuller      = 0.0
        grainITZSieveD      = ""
        grainITZSieveP      = ""
        grainBinderMin      = 0.0
        grainBinderMax      = 0.0
        grainBinderFuller   = 0.0
        grainBinderSieveD   = ""
        grainBinderSieveP   = ""

    if multiMatToggle == "On":
        if particlePhaseMode in (2, 3):
            phaseMode = particlePhaseMode
        if phaseMode == 2:
            phase_exp_mins = [v for v in (grainAggMin, grainBinderMin) if v > 0]
            phase_exp_maxs = [v for v in (grainAggMax, grainBinderMax) if v > 0]
        else:
            phase_exp_mins = [v for v in (grainAggMin, grainITZMin, grainBinderMin) if v > 0]
            phase_exp_maxs = [v for v in (grainAggMax, grainITZMax, grainBinderMax) if v > 0]
        if phase_exp_mins and phase_exp_maxs:
            minPar_exp = min(phase_exp_mins)
            maxPar_exp = max(phase_exp_maxs)

    mixPhaseMode = _combo_phase_mode(
        getattr(form[3], "mixPhaseSelect", None), select_offset=True, default=0
    )
    if particlePhaseMode in (2, 3):
        mixPhaseMode = particlePhaseMode
    if hasattr(form[3], "fillerVolFrac"):
        phaseFillerContent = [_widget_float(getattr(form[3], "fillerVolFrac", None))]
        phaseFillerDensity = [1.0]
        for n in range(2, 4):
            phaseFillerContent.append(
                _widget_float(getattr(form[3], f"phase{n}FillerVolFrac", None))
            )
            phaseFillerDensity.append(1.0)
    else:
        phaseFillerContent = [fillerC]
        phaseFillerDensity = [fillerDensity]
        for n in range(2, 4):
            phaseFillerContent.append(
                _widget_float(getattr(form[3], f"phase{n}FillerContent", None))
            )
            phaseFillerDensity.append(
                _widget_float(getattr(form[3], f"phase{n}FillerDensity", None))
            )

    # Additional Parameters - Periodic Boundary Conditions
    periodicForm = _form_with_attr(form, "periodicToggle")
    if periodicForm is not None:
        periodicToggle      = periodicForm.periodicToggle.currentText()
    else:
        periodicToggle      = "Off"
    particleForm = _form_with_attr(form, "particleOffsetCoef")
    if particleForm is not None:
        particleOffsetCoef = float(particleForm.particleOffsetCoef.value() or 0.2)
    elif hasattr(form[2], "particleOffsetCoef"):
        particleOffsetCoef = float(form[2].particleOffsetCoef.value() or 0.2)
    elif hasattr(form[2], "phase1OffsetCoef"):
        n_phases = particlePhaseMode if particlePhaseMode in (2, 3) else 1
        offsets = phaseOffsetCoefList[:n_phases]
        particleOffsetCoef = float(sum(offsets) / len(offsets)) if offsets else 0.2
    else:
        particleOffsetCoef = 0.2


    genForm = _form_with_attr(form, "outputDir")
    if genForm is None:
        genForm = form[5]
    outputDir           = genForm.outputDir.text()
    dataFilesGen        = genForm.dataFilesGen.isChecked()
    visFilesGen         = genForm.visFilesGen.isChecked()
    singleTetGen        = genForm.singleTetGen.isChecked()
    modelType           = genForm.modelType.currentText()

    orientForm = reinfForm if reinfForm is not None else htcForm
    orientationPathType_sweep3dp = orientForm.orientationPathType_sweep3dp.currentIndex() if hasattr(orientForm, 'orientationPathType_sweep3dp') else 0
    orientationPathSketchName_sweep3dp = (orientForm.orientationPathSketchName_sweep3dp.text() or "") if hasattr(orientForm, 'orientationPathSketchName_sweep3dp') else ""
    orientationSegments_sweep3dp = int(orientForm.orientationSegments_sweep3dp.value() or 36) if hasattr(orientForm, 'orientationSegments_sweep3dp') else 36

    return setupFile, constitutiveEQ, matParaSet, \
        numCPU, numIncrements,maxIter,placementAlg,\
        geoType, dimensions, cadFile,\
        minPar_sim, maxPar_sim, minPar_exp, maxPar_exp, fullerCoef, sieveCurveDiameter, sieveCurvePassing,\
        wcRatio, densityWater, cementC, flyashC, silicaC, scmC,\
        cementDensity, flyashDensity, silicaDensity, scmDensity, airFrac1, \
        fillerC, fillerDensity, airFrac2,\
        HTCtoggle, HTClength,\
        fiberToggle, fiberCutting, fiberDiameter, fiberLength, fiberVol, fiberOrientation1, fiberOrientation2, fiberOrientation3, fiberPref, fiberFile, fiberIntersections, fiberOutputFiles,\
        multiMatToggle,aggFile,multiMatFile,multiMatRule,\
        grainAggMin, grainAggMax, grainAggFuller, grainAggSieveD, grainAggSieveP,\
        grainITZMin, grainITZMax, grainITZFuller, grainITZSieveD, grainITZSieveP,\
        grainBinderMin, grainBinderMax, grainBinderFuller, grainBinderSieveD, grainBinderSieveP,\
        phaseMode,\
        mixPhaseMode, phaseFillerContent, phaseFillerDensity,\
        particlePhaseMode, phaseMinPar, phaseMaxPar, phaseOffsetCoefList,\
        periodicToggle,particleOffsetCoef,\
        outputDir, dataFilesGen, visFilesGen, singleTetGen, modelType,\
        orientationPathType_sweep3dp, orientationPathSketchName_sweep3dp, orientationSegments_sweep3dp