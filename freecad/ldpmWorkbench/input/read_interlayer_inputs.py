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
## This file read the inputs for Interlayer
##
## ===========================================================================


from freecad.ldpmWorkbench.input.read_LDPMCSL_inputs import sweep3dp_path_stored_index
from freecad.ldpmWorkbench.input.read_custom_interlayer import (
    build_custom_surfaces,
    parse_custom_interlayer,
)


def _toggle_on(text):
    return text in ["Yes", "yes", "Y", "y", "On", "on"]


def _qty_float(widget, default=0.0):
    if widget is None:
        return default
    try:
        raw = widget.property("rawValue")
        if raw is not None:
            return float(raw)
    except Exception:
        pass
    try:
        v = widget.value()
        if hasattr(v, "Value"):
            return float(v.Value)
        return float(v)
    except Exception:
        pass
    try:
        return float(str(widget.text()).split()[0])
    except Exception:
        return float(default)


def _read_multi_direction(il, index):
    toggle = getattr(il, "multiDir" + str(index) + "Toggle").currentText()
    axis = getattr(il, "multiDir" + str(index) + "Axis").currentText().strip().upper()
    mode = getattr(il, "multiDir" + str(index) + "Mode").currentText().strip().title()
    if axis not in ("X", "Y", "Z"):
        axis = "X"
    if mode not in ("Width", "Height"):
        mode = "Height"
    return {
        "enabled": _toggle_on(toggle),
        "axis": axis,
        "mode": mode,
    }


def read_interlayer_inputs(form):

    il = None
    for item in form:
        if hasattr(item, "interlayerToggle"):
            il = item
            break

    if il is None:
        return {
            "enabled": False,
            "interlayerType": "Unidirectional Interlayer",
            "firstLayerThickness": 1.0,
            "layerThickness": 1.0,
            "layerWidth": 1.0,
            "interfaceThickness": 1.0,
            "axis": "Z",
            "bulkMf": 1,
            "overlapMf": 5,
            "xMf": 2,
            "yMf": 3,
            "zMf": 4,
            "interlayerMf": 2,
            "multiDirections": [],
            "customDefinition": "",
            "customLayers": [],
            "customMode": "fourPoint",
            "customSurfaces": [],
            "customSurfaceNotes": [],
            "customPathRibbonDefinition": "",
            "customPathRibbonPlane": "XY",
            "customPathRibbonType": "Polyline",
            "customPathRibbonPlaneHeight": 0.0,
            "customDxfCadFile": "",
            "customDxfPlane": "XY",
            "customDxfPlaneHeight": 0.0,
            "customDxfStartPosition": "0, 0, 0",
            "customDxfMf": 2,
        }

    enabled = _toggle_on(il.interlayerToggle.currentText())
    interlayer_type = il.interlayerType.currentText()

    if interlayer_type == "Multidirectional Interlayer":
        bulk_mf = int(il.multiBulkMf.value() or 1)
        overlap_mf = int(il.multiOverlapMf.value() or 5)
        x_mf = int(il.multiXmF.value() or 2)
        y_mf = int(il.multiYmF.value() or 3)
        z_mf = int(il.multiZmF.value() or 4)
        return {
            "enabled": enabled,
            "interlayerType": interlayer_type,
            "firstLayerThickness": _qty_float(il.multiFirstLayerThickness, 1.0),
            "layerThickness": _qty_float(il.multiLayerThickness, 1.0),
            "layerWidth": _qty_float(il.multiLayerWidth, 1.0),
            "interfaceThickness": _qty_float(il.multiInterfaceThickness, 1.0),
            "bulkMf": bulk_mf,
            "overlapMf": overlap_mf,
            "xMf": x_mf,
            "yMf": y_mf,
            "zMf": z_mf,
            "multiDirections": [
                _read_multi_direction(il, 1),
                _read_multi_direction(il, 2),
            ],
        }

    if interlayer_type == "Custom":
        custom_mode = "fourPoint"
        if hasattr(il, "customInterlayerMode"):
            mode_text = il.customInterlayerMode.currentText().strip()
            if mode_text == "Path Ribbon (Planar)":
                custom_mode = "pathRibbon"
            elif mode_text in ("DXF / CAD Import", "DXF / CAD / Sketch Import"):
                custom_mode = "dxfImport"

        custom_definition = ""
        path_ribbon_definition = ""
        if custom_mode == "fourPoint" and hasattr(il, "customInterlayerDefinition"):
            custom_definition = il.customInterlayerDefinition.toPlainText()
        elif custom_mode == "pathRibbon" and hasattr(il, "customPathRibbonDefinition"):
            path_ribbon_definition = il.customPathRibbonDefinition.toPlainText()

        bulk_mf = int(il.customBulkMf.value() or 1)
        custom_layers = parse_custom_interlayer(custom_definition) if custom_mode == "fourPoint" else []

        path_plane = "XY"
        path_type = "Polyline"
        path_plane_height = 0.0
        if custom_mode == "pathRibbon":
            if hasattr(il, "customPathRibbonPlane"):
                path_plane = il.customPathRibbonPlane.currentText().strip() or "XY"
            if hasattr(il, "customPathRibbonType"):
                path_type = il.customPathRibbonType.currentText().strip() or "Polyline"
                if path_type not in ("Line", "Polyline", "Spline"):
                    path_type = "Polyline"
            if hasattr(il, "customPathRibbonPlaneHeight"):
                path_plane_height = _qty_float(il.customPathRibbonPlaneHeight, 0.0)

        dxf_file = ""
        dxf_plane = "XY"
        dxf_plane_height = 0.0
        dxf_start_position = "0, 0, 0"
        dxf_mf = 2
        if custom_mode == "dxfImport":
            if hasattr(il, "customDxfCadFile"):
                dxf_file = il.customDxfCadFile.text().strip()
            if hasattr(il, "customDxfPlane"):
                dxf_plane = il.customDxfPlane.currentText().strip() or "XY"
            if hasattr(il, "customDxfPlaneHeight"):
                dxf_plane_height = _qty_float(il.customDxfPlaneHeight, 0.0)
            if hasattr(il, "customDxfStartPosition"):
                dxf_start_position = il.customDxfStartPosition.text().strip() or "0, 0, 0"
            if hasattr(il, "customDxfMf"):
                dxf_mf = int(il.customDxfMf.value() or 2)

        custom_params = {
            "customMode": custom_mode,
            "customPathRibbonDefinition": path_ribbon_definition,
            "customPathRibbonPlane": path_plane,
            "customPathRibbonType": path_type,
            "customPathRibbonPlaneHeight": path_plane_height,
            "customDxfCadFile": dxf_file,
            "customDxfPlane": dxf_plane,
            "customDxfPlaneHeight": dxf_plane_height,
            "customDxfStartPosition": dxf_start_position,
            "customDxfMf": dxf_mf,
        }
        custom_surfaces = []
        custom_surface_notes = []
        if custom_mode in ("pathRibbon", "dxfImport"):
            try:
                custom_surfaces, custom_surface_notes = build_custom_surfaces(custom_params)
            except Exception as exc:
                custom_surface_notes = [str(exc)]

        return {
            "enabled": enabled,
            "interlayerType": interlayer_type,
            "interfaceThickness": _qty_float(il.customInterfaceThickness, 1.0),
            "bulkMf": bulk_mf,
            "customMode": custom_mode,
            "customDefinition": custom_definition,
            "customPathRibbonDefinition": path_ribbon_definition,
            "customPathRibbonPlane": path_plane,
            "customPathRibbonType": path_type,
            "customPathRibbonPlaneHeight": path_plane_height,
            "customLayers": custom_layers,
            "customSurfaces": custom_surfaces,
            "customSurfaceNotes": custom_surface_notes,
            "customDxfCadFile": dxf_file,
            "customDxfPlane": dxf_plane,
            "customDxfPlaneHeight": dxf_plane_height,
            "customDxfStartPosition": dxf_start_position,
            "customDxfMf": dxf_mf,
        }

    if interlayer_type in ("Fused Surfaces", "Interlayer at Fused Surfaces"):
        geo = None
        for item in form:
            if hasattr(item, "sweep3dpLayerWidth"):
                geo = item
                break

        def _geo_qty(name, default=0.0):
            if geo is None or not hasattr(geo, name):
                return float(default)
            return _qty_float(getattr(geo, name), default)

        def _geo_int(name, default=1):
            if geo is None or not hasattr(geo, name):
                return int(default)
            try:
                return int(getattr(geo, name).value() or default)
            except Exception:
                return int(default)

        path_idx = 0
        if hasattr(il, "fuseSweepGeometryType"):
            path_idx = sweep3dp_path_stored_index(int(il.fuseSweepGeometryType.currentIndex()))

        circular_seam = False
        circular_mode = "Aligned"
        circular_distance = 0.0
        if path_idx == 0:
            num_layers = _geo_int("sweep3dpNumLayers", 1)
            path_distance = _geo_qty("sweep3dpPathDistance", 100.0)
            sketch_name = ""
        elif path_idx == 6:
            num_layers = _geo_int("sweep3dpNumLayersCircular", 1)
            path_distance = _geo_qty("sweep3dpCircularDiameter", 100.0)
            sketch_name = ""
            if geo is not None and hasattr(geo, "sweep3dpCircularSeam"):
                circular_seam = bool(geo.sweep3dpCircularSeam.isChecked())
            if geo is not None and hasattr(geo, "sweep3dpCircularSeamPosition"):
                circular_mode = geo.sweep3dpCircularSeamPosition.currentText() or "Aligned"
            circular_distance = _geo_qty("sweep3dpCircularSeamDistance", 1.0)
        elif path_idx == 1:
            num_layers = _geo_int("sweep3dpNumLayersSquare", 1)
            path_distance = _geo_qty("sweep3dpPathSide", 50.0)
            sketch_name = ""
        elif path_idx == 2:
            num_layers = _geo_int("sweep3dpNumLayersSketch", 1)
            path_distance = 0.0
            sketch_name = ""
            if geo is not None and hasattr(geo, "sweep3dpPathSketchName"):
                sketch_name = geo.sweep3dpPathSketchName.text()
        else:
            num_layers = max(1, min(8, _geo_int("sweep3dpNumSlicesRaster", 1)))
            path_distance = _geo_qty("sweep3dpRasterPathLength", 100.0)
            sketch_name = ""

        raster_loops = 1
        raster_spacing = 0.0
        raster_angles = []
        if path_idx == 3:
            raster_loops = max(1, _geo_int("sweep3dpRasterLoops", 1))
            raster_spacing = _geo_qty("sweep3dpRasterSpacing", 5.0)
            default_dirs = [0.0, 90.0, 0.0, 90.0, 0.0, 90.0, 0.0, 90.0]
            for i in range(num_layers):
                box = getattr(geo, "sweep3dpSliceDir" + str(i + 1), None) if geo is not None else None
                if box is None:
                    raster_angles.append(default_dirs[i])
                    continue
                try:
                    raster_angles.append(float(box.value()))
                except Exception:
                    raster_angles.append(default_dirs[i])

        xy_on = bool(il.fuseInterfaceXY.isChecked()) if hasattr(il, "fuseInterfaceXY") else False
        return {
            "enabled": enabled,
            "interlayerType": interlayer_type,
            "fusePathType": path_idx,
            "fuseInterfaceX": xy_on,
            "fuseInterfaceY": xy_on,
            "fuseInterfaceZ": bool(il.fuseInterfaceZ.isChecked()) if hasattr(il, "fuseInterfaceZ") else True,
            "interfaceThickness": _qty_float(il.fuseInterfaceThickness, 0.0),
            "bulkMf": int(il.fuseBulkMf.value() or 1),
            "xMf": int(il.fuseXmF.value() or 2),
            "yMf": int(il.fuseYmF.value() or 3),
            "zMf": int(il.fuseZmF.value() or 4),
            "overlapMf": int(il.fuseOverlapMf.value() or 5),
            "layerWidth": _geo_qty("sweep3dpLayerWidth", 1.0),
            "layerHeight": _geo_qty("sweep3dpLayerHeight", 1.0),
            "numLayers": num_layers,
            "pathDistance": path_distance,
            "fuseSketchName": sketch_name,
            "rasterLoops": raster_loops,
            "rasterSpacing": raster_spacing,
            "rasterAngles": raster_angles,
            "circularDiameter": path_distance if path_idx == 6 else 0.0,
            "circularSeam": circular_seam,
            "circularSeamMode": circular_mode,
            "circularSeamDistance": circular_distance,
        }

    bulk_mf = int(il.uniBulkMf.value() or 1)
    interlayer_mf = int(il.uniInterlayerMf.value() or 2)
    return {
        "enabled": enabled,
        "interlayerType": interlayer_type,
        "firstLayerThickness": _qty_float(il.uniFirstLayerThickness, 1.0),
        "layerThickness": _qty_float(il.uniLayerThickness, 1.0),
        "interfaceThickness": _qty_float(il.uniInterfaceThickness, 1.0),
        "axis": il.uniInterlayerAxis.currentText(),
        "bulkMf": bulk_mf,
        "interlayerMf": interlayer_mf,
    }
