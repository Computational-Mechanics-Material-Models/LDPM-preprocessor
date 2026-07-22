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
import shutil
from pathlib import Path

import numpy as np

from freecad.ldpmWorkbench.random_field_generation.read_RF_inputs import read_RF_inputs
from freecad.ldpmWorkbench.random_field_generation.rf_generator import RandomField

TRACE_FRACTION = 0.99
NUM_EIG_ESTIMATION_MIN = 50
TRUNCATED_GAUSSIAN_CUTOFF = 0.0

_UI_DIST_TYPE_MAP = {
    "Gaussian-truncated": "TruncatedGaussian",
}


TRUNCATED_GAUSSIAN_MEAN = 1.0


def _resolve_dist_type(ui_dist_type):

    backend_type = _UI_DIST_TYPE_MAP.get(ui_dist_type)
    if backend_type is None:
        raise ValueError(f"Unknown distribution type: {ui_dist_type}")
    return backend_type


def _build_distribution(params):

    backend_type = _resolve_dist_type(params["dist_type"])
    if backend_type == "TruncatedGaussian":
        cutoff = TRUNCATED_GAUSSIAN_CUTOFF
        dist_params = []
        for cov_key in ("elasticity_cov", "strength_cov", "fracture_cov"):
            std = TRUNCATED_GAUSSIAN_MEAN * float(params[cov_key]) / 100.0
            dist_params.append([TRUNCATED_GAUSSIAN_MEAN, std, cutoff])
    else:
        dist_params = [
            [params["elasticity_mean"], params["elasticity_std"]],
            [params["strength_mean"], params["strength_std"]],
            [params["fracture_mean"], params["fracture_std"]],
        ]

    dist_types = [backend_type, backend_type, backend_type]
    return dist_types, dist_params


def _parse_first_seed(seeds_text):

    parts = [p.strip() for p in seeds_text.split(",") if p.strip()]
    if not parts:
        raise ValueError("Enter at least one random seed.")
    return int(parts[0])


def _next_field_dir(output_dir):

    base = Path(output_dir)
    index = 0
    while (base / f"RF_field_{index:03d}").exists():
        index += 1
    field_dir = base / f"RF_field_{index:03d}"
    field_dir.mkdir(parents=True, exist_ok=True)
    return str(field_dir)


def _latest_field_dir(output_dir):

    base = Path(output_dir)
    if not base.is_dir():
        return None

    candidates = sorted(base.glob("RF_field_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        if (path / "report.dat").is_file():
            return str(path)
    return None


def _validate_params(params):

    output_dir = params["outputDir"].strip()
    if not output_dir:
        raise ValueError("Set an output directory before generating the random field.")

    for axis, span in (("x", params["x_range"]), ("y", params["y_range"]), ("z", params["z_range"])):
        if span[1] <= 0.0:
            raise ValueError(f"Invalid {axis} domain size: must be greater than zero.")

    for i, value in enumerate(params["corr_l"]):
        if value <= 0.0:
            raise ValueError(f"Autocorrelation length for axis {i} must be greater than zero.")

    if params["grid_spacing"] <= 0.0:
        raise ValueError("Grid spacing must be greater than zero.")

    if params["numRealizations"] <= 0:
        raise ValueError("Number of realizations must be greater than zero.")

    if _resolve_dist_type(params["dist_type"]) == "TruncatedGaussian":
        for label, cov_key in (
            ("Elasticity", "elasticity_cov"),
            ("Strength", "strength_cov"),
            ("Fracture (Energy)", "fracture_cov"),
        ):
            if float(params[cov_key]) <= 0.0:
                raise ValueError(f"{label} COV must be greater than zero.")


def _build_random_field(params, field_dir):

    dist_types, dist_params = _build_distribution(params)

    return RandomField(
        dimension=3,
        dist_types=dist_types,
        dist_params=dist_params,
        CC=np.array(params["cross_correlation"]),
        name=field_dir,
        corr_l=params["corr_l"],
        corr_f=params["corr_f"],
        x_range=[float(params["x_range"][0]), float(params["x_range"][1])],
        y_range=[float(params["y_range"][0]), float(params["y_range"][1])],
        z_range=[float(params["z_range"][0]), float(params["z_range"][1])],
        sampling_type="LHS",
        filesavetype="binary",
        periodic=params["periodic"],
        rank_correlation=params["rank_correlation"],
        grid_file=params["grid_file"],
        grid_spacing=float(params["grid_spacing"]),
        trace_fraction=TRACE_FRACTION,
        num_eig_estimation=NUM_EIG_ESTIMATION_MIN,
        sparse=params["sparse"],
    )


def driver_RF(self, tempPath):

    import FreeCAD as App

    params = read_RF_inputs(self.form)
    _validate_params(params)

    output_dir = params["outputDir"].strip()
    os.makedirs(output_dir, exist_ok=True)

    field_dir = _next_field_dir(output_dir)
    field_name = os.path.basename(field_dir)
    seed = _parse_first_seed(params["seeds"])

    App.Console.PrintMessage(f"Generating random field in {field_dir}\n")

    rf = _build_random_field(params, field_dir)
    rf.generateRandVariables(params["numRealizations"], seed=seed)
    rf.generateFieldOnGrid()

    node_file = params["rfFieldInputFile"].strip()
    use_eole = bool(node_file) and not node_file.lower().endswith(".cwpar")
    if use_eole:
        rf.generateFieldEOLE(nodefile=node_file)

    if params["visFilesGen"]:
        if use_eole:
            rf.saveFieldNodesVTKDots()
        else:
            rf.saveGridNodesVTKDots()

    cwpar_src = Path(tempPath) / "rfWorkbench.cwPar"
    if cwpar_src.is_file():
        shutil.copy2(cwpar_src, Path(field_dir) / "rfWorkbench.cwPar")

    self._last_rf_field_dir = field_dir

    App.Console.PrintMessage(
        f"Random field generation complete: {field_name} ({params['numRealizations']} realizations)\n"
    )


def run_rf_error_evaluation(self):

    import FreeCAD as App

    params = read_RF_inputs(self.form)
    output_dir = params["outputDir"].strip()

    field_dir = getattr(self, "_last_rf_field_dir", None) or _latest_field_dir(output_dir)
    if not field_dir:
        raise ValueError("No generated random field found. Run generation first.")

    App.Console.PrintMessage(f"Running error evaluation on {field_dir}\n")

    rf = RandomField(readFromFolder=field_dir)
    node_file = params["rfFieldInputFile"].strip()
    use_eole = bool(node_file) and not node_file.lower().endswith(".cwpar")
    use_grid = params["grid_file"] is not None or not use_eole
    rf.errorEvaluation(max_node_num=5e3, grid_data=use_grid)

    App.Console.PrintMessage("Error evaluation complete.\n")


def resolve_rf_realization(rf_params, sample_id=1):

    if rf_params is None:
        return None
    toggle = str(rf_params.get("rfToggle", "Off")).strip().lower()
    if toggle != "on":
        return None

    plan = rf_params.get("rfJobPlan") or {}
    key = str(int(sample_id))
    realizations = plan.get(key) or plan.get(sample_id)
    if not realizations:
        return None
    return int(realizations[0])


def _rf_folder_has(folder, name):

    return (
        os.path.isfile(os.path.join(folder, name + ".npy"))
        or os.path.isfile(os.path.join(folder, name + ".dat"))
    )


def _validate_rf_field_folder(rf_field_dir):

    folder = os.path.abspath(os.path.expanduser(str(rf_field_dir).strip()))
    if not os.path.isdir(folder):
        raise ValueError(f"RF folder not found: {folder}")

    missing = []
    if not os.path.isfile(os.path.join(folder, "report.dat")):
        missing.append("report.dat")
    if not _rf_folder_has(folder, "random_variables"):
        missing.append("random_variables.npy/.dat")
    if not (
        _rf_folder_has(folder, "grid_nodes")
        or (
            _rf_folder_has(folder, "grid_nodesX")
            and _rf_folder_has(folder, "grid_nodesY")
            and _rf_folder_has(folder, "grid_nodesZ")
        )
    ):
        missing.append("grid_nodes (.npy/.dat)")
    if not (
        _rf_folder_has(folder, "ijk")
        or (
            _rf_folder_has(folder, "eigenvalues_0")
            and _rf_folder_has(folder, "eigenvectors_0")
        )
    ):
        missing.append("ijk or eigenvalues_0/eigenvectors_0 (.npy/.dat)")
    if not (
        _rf_folder_has(folder, "eigenvalues_C")
        and _rf_folder_has(folder, "eigenvectors_C")
    ):
        missing.append("eigenvalues_C/eigenvectors_C (.npy/.dat)")

    if missing:
        raise ValueError(
            "RF folder missing files needed for EOLE: "
            + ", ".join(missing)
            + f" in {folder}"
        )

    return folder


def apply_rf_eole_to_facet_data(facetData, rf_field_dir, realization):

    facetData = np.asarray(facetData, dtype=float)
    if facetData.ndim != 2 or facetData.shape[0] == 0:
        return facetData

    ncols = facetData.shape[1]
    if ncols == 19:
        ips = facetData[:, 6:9]
    elif ncols == 24:
        ips = facetData[:, 7:10]
    elif ncols in (22, 27):
        return facetData
    else:
        raise ValueError(
            f"Unsupported facetData width {ncols}; expected 19 (LDPM) or 24 (CSL)."
        )

    if not rf_field_dir:
        raise ValueError("Random Field folder path is empty.")

    folder = _validate_rf_field_folder(rf_field_dir)
    rf = RandomField(readFromFolder=folder)

    lo = np.min(ips, axis=0)
    hi = np.max(ips, axis=0)
    eps = 1e-2
    if (
        lo[0] < rf.x_range[0] - eps
        or hi[0] > rf.x_range[1] + eps
        or lo[1] < rf.y_range[0] - eps
        or hi[1] > rf.y_range[1] + eps
        or lo[2] < rf.z_range[0] - eps
        or hi[2] > rf.z_range[1] + eps
    ):
        raise ValueError(
            "Geometry facet coordinates are outside the RF domain. "
            f"geo min={lo}, max={hi}; "
            f"RF x={rf.x_range}, y={rf.y_range}, z={rf.z_range}."
        )

    gf = rf.getFieldEOLE(ips, realizations=[int(realization)])

    n_facets = int(ips.shape[0])
    extras = np.ones((n_facets, 3), dtype=float)
    nvar = int(gf.shape[0])
    for i in range(min(3, nvar)):
        extras[:, i] = gf[i, :, 0]

    return np.hstack([facetData, extras])
