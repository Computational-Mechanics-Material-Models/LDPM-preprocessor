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
## Generate Mesh Preview
##
## ===========================================================================


import os
import subprocess
from pathlib import Path

import numpy as np

import FreeCAD as App

from freecad.ldpmWorkbench.generation.gen_LDPMCSL_externalMesh import (
    export_shape_brep,
    find_gmsh_binary,
    freecad_gmsh_binary,
    write_brep_geo,
)
from freecad.ldpmWorkbench.generation.gen_LDPMCSL_geometry import gen_LDPMCSL_geometry
from freecad.ldpmWorkbench.generation.gen_3DCP_interlayer import (
    build_interface_regions,
    custom_surface_preview_triangles,
)
from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs import read_LDPMCSL_inputs
from freecad.ldpmWorkbench.input.read_interlayer_inputs import read_interlayer_inputs
from freecad.ldpmWorkbench.output.mkData_surfMesh import mkData_surfMesh
from freecad.ldpmWorkbench.output.mkParameters import mkParameters

_UNBOUNDED = 1e29


def _geo_type_out_name(geo_type):
    if geo_type in ["Box", "Cylinder", "Cone", "Sphere", "Ellipsoid", "Prism", "Dogbone", "Custom"]:
        return geo_type
    if geo_type == "L-shape":
        return "Lshape"
    if geo_type == "Notched Prism - Semi Circle":
        return "NotchedPrismSemiCircle"
    if geo_type == "Notched Prism - Square":
        return "NotchedPrismSquare"
    if geo_type == "Notched Prism - Ellipse":
        return "NotchedPrismEllipse"
    if geo_type == "Import CAD or Mesh":
        return "ImportedFile"
    if geo_type == "Sweep-3DP":
        return "Sweep"
    return geo_type


def find_latest_mesh_preview(output_dir):
    root = Path(str(output_dir))
    if not root.is_dir():
        return None
    best = None
    best_mtime = -1.0
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        faces = list(folder.glob("*-para-faces.000.vtk"))
        if not faces:
            continue
        geo_vtk = faces[0]
        try:
            mtime = geo_vtk.stat().st_mtime
        except OSError:
            continue
        if mtime < best_mtime:
            continue
        best_mtime = mtime
        iface = list(folder.glob("*-para-interfaces.000.vtk"))
        best = {
            "geometry": str(geo_vtk),
            "interfaces": str(iface[0]) if iface else None,
            "outDir": str(folder),
        }
    return best


def _make_out_folder(out_dir, geo_name, geo_type):
    geo_type_out = _geo_type_out_name(geo_type)
    i = 0
    out_name = "/" + geo_name + geo_type_out + str(i).zfill(3)
    while os.path.isdir(Path(str(out_dir) + out_name)):
        i += 1
        out_name = "/" + geo_name + geo_type_out + str(i).zfill(3)
    out_folder = Path(str(out_dir) + out_name)
    out_folder.mkdir(parents=True, exist_ok=True)
    temp_path = str(out_folder).replace("\\", "/")
    if not temp_path.endswith("/"):
        temp_path += "/"
    return out_folder, temp_path


def _status(form, text):
    msg = str(text)
    for item in form:
        if hasattr(item, "statusWindow"):
            try:
                item.statusWindow.setText("Status: " + msg)
            except Exception:
                pass
            break
    try:
        App.Console.PrintMessage(msg + ("" if msg.endswith("\n") else "\n"))
    except Exception:
        print(msg)


def _ensure_document():
    previous = App.ActiveDocument
    doc = App.newDocument("MeshPreviewGeo")
    App.setActiveDocument(doc.Name)
    try:
        import FreeCADGui as Gui

        Gui.setActiveDocument(doc.Name)
    except Exception:
        pass
    return doc, previous


def _restore_document(doc, previous):
    try:
        App.closeDocument(doc.Name)
    except Exception:
        pass
    if previous is not None:
        try:
            App.setActiveDocument(previous.Name)
            import FreeCADGui as Gui

            Gui.setActiveDocument(previous.Name)
        except Exception:
            pass


def _run_gmsh_surface(gmsh_bin, geo_path, msh_path):
    cmd = [
        str(gmsh_bin),
        str(geo_path),
        "-2",
        "-format",
        "msh2",
        "-o",
        str(msh_path),
        "-v",
        "1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not Path(msh_path).is_file():
        raise RuntimeError(
            "Gmsh surface meshing failed.\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
        )


def _parse_msh2_surface(msh_path):
    nodes = {}
    tris = []
    section = None
    with open(msh_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("$"):
                if line == "$Nodes":
                    section = "nodes_count"
                elif line == "$EndNodes":
                    section = None
                elif line == "$Elements":
                    section = "elements_count"
                elif line == "$EndElements":
                    section = None
                else:
                    section = None
                continue
            if section == "nodes_count":
                section = "nodes"
                continue
            if section == "nodes":
                parts = line.split()
                if len(parts) >= 4:
                    nodes[int(parts[0])] = [
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3]),
                    ]
                continue
            if section == "elements_count":
                section = "elements"
                continue
            if section == "elements":
                parts = line.split()
                if len(parts) < 4:
                    continue
                etype = int(parts[1])
                ntags = int(parts[2])
                start = 3 + ntags
                if etype == 2 and len(parts) >= start + 3:
                    tris.append([int(parts[start + i]) for i in range(3)])
                continue
    if not nodes:
        raise RuntimeError(f"No nodes found in mesh file: {msh_path}")
    if not tris:
        raise RuntimeError(f"No surface triangles found in mesh file: {msh_path}")
    tags = sorted(nodes.keys())
    tag_to_idx = {tag: i for i, tag in enumerate(tags)}
    surface_nodes = np.array([nodes[tag] for tag in tags], dtype=float)
    surface_faces = np.array(
        [[tag_to_idx[a], tag_to_idx[b], tag_to_idx[c]] for a, b, c in tris],
        dtype=int,
    )
    return surface_nodes, surface_faces


def _clamp_region(mins, maxs, min_c, max_c):
    mins = np.asarray(mins, dtype=float).reshape(3)
    maxs = np.asarray(maxs, dtype=float).reshape(3)
    min_c = np.asarray(min_c, dtype=float).reshape(3)
    max_c = np.asarray(max_c, dtype=float).reshape(3)
    lo = np.empty(3, dtype=float)
    hi = np.empty(3, dtype=float)
    for i in range(3):
        if abs(mins[i]) >= _UNBOUNDED:
            lo[i] = min_c[i]
        else:
            lo[i] = max(mins[i], min_c[i])
        if abs(maxs[i]) >= _UNBOUNDED:
            hi[i] = max_c[i]
        else:
            hi[i] = min(maxs[i], max_c[i])
        if hi[i] < lo[i]:
            lo[i], hi[i] = hi[i], lo[i]
    return lo, hi


def _region_to_quad(mins, maxs, min_c, max_c):
    lo, hi = _clamp_region(mins, maxs, min_c, max_c)
    spans = hi - lo
    axis = int(np.argmin(spans))
    center = 0.5 * (lo[axis] + hi[axis])
    others = [i for i in range(3) if i != axis]
    a0, a1 = others
    p = []
    for u, v in ((lo[a0], lo[a1]), (hi[a0], lo[a1]), (hi[a0], hi[a1]), (lo[a0], hi[a1])):
        pt = [0.0, 0.0, 0.0]
        pt[axis] = center
        pt[a0] = u
        pt[a1] = v
        p.append(pt)
    return p


def _write_polydata(path, points, cells):
    if not cells:
        return None
    size = sum(len(cell) + 1 for cell in cells)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# vtk DataFile Version 2.0\n")
        f.write("Mesh Preview Interfaces\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")
        f.write(f"POINTS {len(points)} float\n")
        f.write("\n".join(" ".join(f"{v:.8g}" for v in row) for row in points))
        f.write("\n\n")
        f.write(f"POLYGONS {len(cells)} {size}\n")
        for cell in cells:
            f.write(str(len(cell)) + " " + " ".join(str(int(index)) for index in cell) + "\n")
    return path


def _write_interface_vtk(path, min_c, max_c, interlayer_params):
    surface_tris = custom_surface_preview_triangles(min_c, interlayer_params)
    if surface_tris:
        points = []
        cells = []
        for tri in surface_tris:
            base = len(points)
            points.extend(tri)
            cells.append([base, base + 1, base + 2])
        return _write_polydata(path, points, cells)

    regions = build_interface_regions(min_c, max_c, interlayer_params)
    if not regions:
        return None
    points = []
    cells = []
    for region in regions:
        if not isinstance(region, (tuple, list)) or len(region) != 2:
            continue
        mins, maxs = region
        quad = _region_to_quad(mins, maxs, min_c, max_c)
        base = len(points)
        points.extend(quad)
        cells.append([base, base + 1, base + 2, base + 3])
    return _write_polydata(path, points, cells)


def _cleanup(paths):
    for path in paths:
        try:
            Path(path).unlink()
        except OSError:
            pass


def _mesh_preview_geo_inputs(form):
    vals = read_LDPMCSL_inputs(form)
    geo_type = vals[7]
    dimensions = vals[8]
    cad_file = vals[9]
    min_par_sim = float(vals[10] or 0.0)
    output_dir = str(vals[75])
    model_type = vals[79]
    return geo_type, dimensions, cad_file, min_par_sim, output_dir, model_type


def run_mesh_preview(self, module_name):
    form = self.form
    geo_type, dimensions, cad_file, min_par_sim, output_dir, model_type = (
        _mesh_preview_geo_inputs(form)
    )
    if min_par_sim <= 0.0:
        raise RuntimeError("Minimum particle size must be greater than zero for mesh preview.")
    interlayer_params = read_interlayer_inputs(form)

    if model_type in [
        "Confinement Shear Lattice (CSL) - LDPM Style ",
        "Confinement Shear Lattice (CSL) - Original",
    ]:
        element_type = "CSL"
    else:
        element_type = "LDPM"
    geo_name = element_type + "geo" + str(0).zfill(3)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_folder, temp_path = _make_out_folder(output_dir, geo_name, geo_type)

    _status(form, "Saving parameters.")
    mkParameters(self, "LDPMCSL", temp_path, module=module_name)

    brep_path = Path(temp_path) / (geo_name + "_geometry.brep")
    geo_path = Path(temp_path) / (geo_name + "_surface.geo")
    msh_path = Path(temp_path) / (geo_name + "_surface.msh")
    geo_vtk = Path(temp_path) / (geo_name + "-para-faces.000.vtk")
    iface_vtk = Path(temp_path) / (geo_name + "-para-interfaces.000.vtk")

    _status(form, "Building geometry for preview.")
    doc, previous = _ensure_document()
    try:
        if geo_type == "Sweep-3DP" and len(dimensions) < 11:
            raise RuntimeError("Sweep-3DP dimensions are incomplete for preview.")
        gen_geo = gen_LDPMCSL_geometry(dimensions, geo_type, geo_name, cad_file)
        if gen_geo is None:
            raise RuntimeError(f"Geometry not created for '{geo_type}'.")
        try:
            doc.recompute()
        except Exception:
            pass
        export_shape_brep(gen_geo, brep_path)
        shape = gen_geo.Shape if hasattr(gen_geo, "Shape") else gen_geo
        bb = shape.BoundBox
        min_c = np.array([bb.XMin, bb.YMin, bb.ZMin], dtype=float)
        max_c = np.array([bb.XMax, bb.YMax, bb.ZMax], dtype=float)
    finally:
        _restore_document(doc, previous)

    _status(form, "Meshing surface with Gmsh.")
    try:
        gmsh_bin = freecad_gmsh_binary()
    except Exception:
        gmsh_bin = find_gmsh_binary()
    write_brep_geo(brep_path, geo_path, min_par_sim)
    _run_gmsh_surface(gmsh_bin, geo_path, msh_path)
    surface_nodes, surface_faces = _parse_msh2_surface(msh_path)
    mkData_surfMesh(surface_nodes, surface_faces, geo_name, temp_path)

    iface_path = None
    if interlayer_params.get("enabled"):
        _status(form, "Writing interface planes.")
        iface_path = _write_interface_vtk(iface_vtk, min_c, max_c, interlayer_params)

    _cleanup([brep_path, geo_path, msh_path])

    msg = f"Mesh preview written: {geo_vtk}"
    if iface_path:
        msg += f" ; {iface_path}"
    _status(form, msg)
    return {
        "geometry": str(geo_vtk),
        "interfaces": None if iface_path is None else str(iface_path),
        "outDir": str(out_folder),
    }
