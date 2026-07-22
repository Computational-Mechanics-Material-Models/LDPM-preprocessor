## ================================================================================
## LDPM WORKBENCH:github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor
##
## Copyright (c) 2023 
## All rights reserved. 
##
## Use of this source code is governed by a BSD-style license that can be found
## in the LICENSE file at the top level of the distribution and at
## github.com/Computational-Mechanics-Material-Models/LDPM-preprocessor/blob/main/LICENSE
##
## ================================================================================
##
## This file contains the function to create external meshes for LDPM-CSL
##
## ================================================================================




import os
import platform
import shutil
import subprocess
from pathlib import Path

import numpy as np

from freecad.ldpmWorkbench.generation.calc_LDPMCSL_meshVolume import calc_LDPMCSL_meshVolume


def find_gmsh_binary(preferred=None):
    candidates = []
    if preferred:
        candidates.append(Path(preferred))
    env = os.environ.get("CHRONO_GMSH", "").strip()
    if env:
        candidates.append(Path(env))
    for name in ("gmsh", "gmsh.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    if platform.system() == "Windows":
        freecad_versions = ("1.1", "1.0", "0.21", "0.20", "0.19", "0.18")
        program_roots = [
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
        ]
        local_programs = Path.home() / "AppData" / "Local" / "Programs"
        if local_programs.is_dir():
            program_roots.append(local_programs)
        for root in program_roots:
            for ver in freecad_versions:
                candidates.append(root / f"FreeCAD {ver}" / "bin" / "gmsh.exe")
            candidates.append(root / "FreeCAD" / "bin" / "gmsh.exe")
    else:
        candidates.extend(
            [
                Path("/usr/bin/gmsh"),
                Path("/usr/local/bin/gmsh"),
            ]
        )

    for path in candidates:
        try:
            if path.is_file():
                return str(path.resolve())
        except OSError:
            continue
    raise FileNotFoundError(
        "Gmsh binary not found. Set CHRONO_GMSH or install Gmsh / use FreeCAD's bin/gmsh."
    )


def write_brep_geo(brep_path, geo_path, min_par):
    brep = Path(brep_path).resolve().as_posix()
    min_par = float(min_par)
    max_par = 2.0 * min_par
    with open(geo_path, "w", encoding="utf-8") as f:
        f.write('SetFactory("OpenCASCADE");\n')
        f.write(f'Merge "{brep}";\n')
        f.write("Coherence;\n")
        f.write(f"Mesh.CharacteristicLengthMin = {min_par};\n")
        f.write(f"Mesh.CharacteristicLengthMax = {max_par};\n")
        f.write("Mesh.ElementOrder = 1;\n")
        f.write("Mesh.Algorithm = 5;\n")
        f.write("Mesh.Algorithm3D = 1;\n")


def run_gmsh(gmsh_bin, geo_path, msh_path):
    cmd = [
        str(gmsh_bin),
        str(geo_path),
        "-3",
        "-format",
        "msh2",
        "-o",
        str(msh_path),
        "-v",
        "1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not Path(msh_path).is_file():
        raise RuntimeError(
            "Gmsh meshing failed.\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
        )
    return result


def _parse_msh2(msh_path):
    nodes = {}
    tets = []
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
                    tag = int(parts[0])
                    nodes[tag] = [float(parts[1]), float(parts[2]), float(parts[3])]
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
                if etype == 4 and len(parts) >= start + 4:
                    tets.append([int(parts[start + i]) for i in range(4)])
                elif etype == 2 and len(parts) >= start + 3:
                    tris.append([int(parts[start + i]) for i in range(3)])
                continue

    if not nodes:
        raise RuntimeError(f"No nodes found in mesh file: {msh_path}")
    if not tets:
        raise RuntimeError(f"No tetrahedra found in mesh file: {msh_path}")

    tags = sorted(nodes.keys())
    tag_to_idx = {tag: i + 1 for i, tag in enumerate(tags)}
    meshVertices = np.array([nodes[tag] for tag in tags], dtype=float)
    meshTets = np.array([[tag_to_idx[n] for n in tet] for tet in tets], dtype=int)

    if tris:
        surface_tris_vol = np.array([[tag_to_idx[n] for n in tri] for tri in tris], dtype=int)
    else:
        surface_tris_vol = _boundary_faces_from_tets(meshTets)

    surfaceNodes, surfaceFaces = _compact_surface(meshVertices, surface_tris_vol)
    return meshVertices, meshTets, surfaceNodes, surfaceFaces


def _boundary_faces_from_tets(meshTets):
    face_count = {}
    for tet in meshTets:
        faces = (
            (tet[0], tet[1], tet[2]),
            (tet[0], tet[1], tet[3]),
            (tet[0], tet[2], tet[3]),
            (tet[1], tet[2], tet[3]),
        )
        for face in faces:
            key = tuple(sorted(face))
            if key in face_count:
                face_count[key] = None
            else:
                face_count[key] = face

    boundary = [face for face in face_count.values() if face is not None]
    if not boundary:
        raise RuntimeError("Could not extract boundary faces from tetrahedra.")
    return np.array(boundary, dtype=int)


def _compact_surface(meshVertices, surface_tris_vol):
    used = np.unique(surface_tris_vol.reshape(-1))
    vol_to_surf = {int(v): i for i, v in enumerate(used)}
    surfaceNodes = meshVertices[used - 1]
    surfaceFaces = np.array(
        [[vol_to_surf[int(a)], vol_to_surf[int(b)], vol_to_surf[int(c)]] for a, b, c in surface_tris_vol],
        dtype=int,
    )
    return surfaceNodes, surfaceFaces


def _max_edge_length_surface(surfaceNodes, surfaceFaces):
    faces = np.asarray(surfaceFaces, dtype=int)
    verts = np.asarray(surfaceNodes, dtype=float)
    e1 = np.linalg.norm(verts[faces[:, 1]] - verts[faces[:, 0]], axis=1)
    e2 = np.linalg.norm(verts[faces[:, 2]] - verts[faces[:, 1]], axis=1)
    e3 = np.linalg.norm(verts[faces[:, 2]] - verts[faces[:, 0]], axis=1)
    return float(np.max(np.concatenate((e1, e2, e3))))


def mesh_geometry_with_gmsh(bundle_dir, gmsh_bin, geometry_file, min_par, geo_name="external"):
    bundle = Path(bundle_dir).resolve()
    geometry_file = Path(geometry_file)
    if not geometry_file.is_file():
        geometry_file = bundle / geometry_file.name
    if not geometry_file.is_file():
        raise FileNotFoundError(f"Geometry file not found for external meshing: {geometry_file}")

    gmsh_bin = find_gmsh_binary(gmsh_bin)
    geo_path = bundle / f"{geo_name}_external.geo"
    msh_path = bundle / f"{geo_name}_external.msh"

    write_brep_geo(geometry_file, geo_path, min_par)
    print(f"External Gmsh: meshing {geometry_file.name} with {gmsh_bin}")
    run_gmsh(gmsh_bin, geo_path, msh_path)
    meshVertices, meshTets, surfaceNodes, surfaceFaces = _parse_msh2(msh_path)

    tetVolume = float(calc_LDPMCSL_meshVolume(meshVertices, meshTets))
    maxEdgeLength = _max_edge_length_surface(surfaceNodes, surfaceFaces)
    verts = meshVertices[np.array(meshTets).flatten() - 1]
    max_dist = float(np.max(np.sqrt(np.sum(verts ** 2, axis=1))))
    minC = meshVertices.min(axis=0).astype(float)
    maxC = meshVertices.max(axis=0).astype(float)

    coord1 = meshVertices[meshTets[:, 0] - 1]
    coord2 = meshVertices[meshTets[:, 1] - 1]
    coord3 = meshVertices[meshTets[:, 2] - 1]
    coord4 = meshVertices[meshTets[:, 3] - 1]

    temp = str(bundle).replace("\\", "/")
    if not temp.endswith("/"):
        temp += "/"

    np.save(temp + "meshVertices.npy", meshVertices)
    np.save(temp + "meshTets.npy", meshTets)
    np.save(temp + "surfaceNodes.npy", surfaceNodes)
    np.save(temp + "surfaceFaces.npy", surfaceFaces)
    np.save(temp + "coord1.npy", coord1)
    np.save(temp + "coord2.npy", coord2)
    np.save(temp + "coord3.npy", coord3)
    np.save(temp + "coord4.npy", coord4)

    try:
        geo_path.unlink(missing_ok=True)
        msh_path.unlink(missing_ok=True)
    except TypeError:
        for p in (geo_path, msh_path):
            try:
                os.remove(p)
            except OSError:
                pass

    print(
        f"External Gmsh complete: {len(meshVertices)} nodes, {len(meshTets)} tets, "
        f"volume={tetVolume:.6g}"
    )

    return {
        "meshVertices": meshVertices,
        "meshTets": meshTets,
        "surfaceNodes": surfaceNodes,
        "surfaceFaces": surfaceFaces,
        "coord1": coord1,
        "coord2": coord2,
        "coord3": coord3,
        "coord4": coord4,
        "tetVolume": tetVolume,
        "maxEdgeLength": maxEdgeLength,
        "max_dist": max_dist,
        "minC": [float(minC[0]), float(minC[1]), float(minC[2])],
        "maxC": [float(maxC[0]), float(maxC[1]), float(maxC[2])],
    }


def export_shape_brep(shape_obj, target_path):
    import FreeCAD as App

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shape = shape_obj.Shape if hasattr(shape_obj, "Shape") else shape_obj
    shape.exportBrep(str(target_path))
    return str(target_path)


def freecad_gmsh_binary():
    import FreeCAD as App

    home = Path(App.ConfigGet("AppHomePath"))
    for name in ("gmsh.exe", "gmsh"):
        candidate = home / "bin" / name
        if candidate.is_file():
            return str(candidate.resolve())
    return find_gmsh_binary()
