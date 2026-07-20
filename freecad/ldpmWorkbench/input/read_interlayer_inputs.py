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
        from freecad.ldpmWorkbench.input.parse_custom_interlayer import parse_custom_interlayer

        custom_definition = ""
        if hasattr(il, "customInterlayerDefinition"):
            custom_definition = il.customInterlayerDefinition.toPlainText()
        bulk_mf = int(il.customBulkMf.value() or 1)
        return {
            "enabled": enabled,
            "interlayerType": interlayer_type,
            "interfaceThickness": _qty_float(il.customInterfaceThickness, 1.0),
            "bulkMf": bulk_mf,
            "customDefinition": custom_definition,
            "customLayers": parse_custom_interlayer(custom_definition),
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
