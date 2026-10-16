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
## Read Reinforcement Inputs
##
## ===========================================================================


from freecad.ldpmWorkbench.generation.gen_reinforcement import cad_heights, parse_height_values

_DEFAULT_REINF_ELEMENT_TYPE = "2DOF-T2D2/LINK1"


def reinforcement_cwpar_values(form):
    panel = _panel(form)
    if panel is None:
        return None
    kind = int(panel.addReinfTypeCB.currentIndex())
    values = {
        "addReinfToggle": "On" if _toggle_on(panel) else "Off",
        "addReinfType": "Cable Reinforcement" if kind == 1 else "Conventional Reinforcement",
        "rebarCadOn": "Yes" if _checked(getattr(panel, "rebarCadGroup", None)) else "No",
        "rebarCadFile": _text(getattr(panel, "rebarCadFile", None)),
        "rebarCadStartX": _float_value(getattr(panel, "rebarCadStartX", None)),
        "rebarCadStartY": _float_value(getattr(panel, "rebarCadStartY", None)),
        "rebarCadHeight": _float_value(getattr(panel, "rebarCadHeight", None)),
        "rebarCadRotation": _float_value(getattr(panel, "rebarCadRotation", None)),
        "rebarCadHeights": _text(getattr(panel, "rebarCadHeights", None)),
        "rebarLinesOn": "Yes" if _checked(getattr(panel, "rebarLinesGroup", None)) else "No",
        "rebarLineStartX": _float_value(getattr(panel, "rebarLineStartX", None)),
        "rebarLineStartY": _float_value(getattr(panel, "rebarLineStartY", None)),
        "cableCadFile": _text(getattr(panel, "cableCadFile", None)),
        "cableCadStartX": _float_value(getattr(panel, "cableCadStartX", None)),
        "cableCadStartY": _float_value(getattr(panel, "cableCadStartY", None)),
        "cableCadHeight": _float_value(getattr(panel, "cableCadHeight", None)),
        "cableCadRotation": _float_value(getattr(panel, "cableCadRotation", None)),
        "cableCadHeights": _text(getattr(panel, "cableCadHeights", None)),
        "elementLength": _float_value(getattr(panel, "elementLength", None), 1.0),
        "elementDiameter": _float_value(getattr(panel, "elementDiameter", None), 1.0),
        "reinfElementType": _element_type(panel),
    }
    for index in (1, 2):
        values["rebarDir" + str(index) + "Distance"] = _float_value(getattr(panel, "rebarDir" + str(index) + "Distance", None))
        axis = _text(getattr(panel, "rebarDir" + str(index) + "Direction", None))
        values["rebarDir" + str(index) + "Direction"] = axis if axis else "X"
        values["rebarDir" + str(index) + "Count"] = int(_float_value(getattr(panel, "rebarDir" + str(index) + "Count", None), 1))
        values["rebarDir" + str(index) + "Spacing"] = _float_value(getattr(panel, "rebarDir" + str(index) + "Spacing", None))
        values["rebarDir" + str(index) + "Height"] = _text(getattr(panel, "rebarDir" + str(index) + "Height", None))
    return values


def read_reinforcement_inputs(form):
    panel = _panel(form)
    if panel is None:
        return None
    if not _toggle_on(panel):
        return None
    grid = None
    cad = None
    if int(panel.addReinfTypeCB.currentIndex()) == 1:
        path = _text(getattr(panel, "cableCadFile", None))
        if path == "":
            raise ValueError("Cable reinforcement CAD file is not set.")
        cad = _cad_source(
            path,
            getattr(panel, "cableCadStartX", None),
            getattr(panel, "cableCadStartY", None),
            getattr(panel, "cableCadRotation", None),
            getattr(panel, "cableCadHeight", None),
            getattr(panel, "cableCadHeights", None),
        )
    else:
        if hasattr(panel, "rebarCadGroup") and panel.rebarCadGroup.isChecked():
            path = _text(getattr(panel, "rebarCadFile", None))
            if path == "":
                raise ValueError("Reinforcement CAD file is not set.")
            cad = _cad_source(
                path,
                getattr(panel, "rebarCadStartX", None),
                getattr(panel, "rebarCadStartY", None),
                getattr(panel, "rebarCadRotation", None),
                getattr(panel, "rebarCadHeight", None),
                getattr(panel, "rebarCadHeights", None),
            )
        if hasattr(panel, "rebarLinesGroup") and panel.rebarLinesGroup.isChecked():
            grid = {
                "start_x": _float_value(getattr(panel, "rebarLineStartX", None)),
                "start_y": _float_value(getattr(panel, "rebarLineStartY", None)),
                "directions": [_direction(panel, 1), _direction(panel, 2)],
            }
    if grid is None and cad is None:
        raise ValueError(
            "Additional Reinforcement is On, but no CAD layout or Lines/Grid source is enabled."
        )
    return {
        "grid": grid,
        "cad": cad,
        "elementLength": _float_value(getattr(panel, "elementLength", None), 1.0),
        "elementDiameter": _float_value(getattr(panel, "elementDiameter", None), 1.0),
        "reinfElementType": _element_type(panel),
    }


def _cad_source(path, start_x, start_y, rotation, first_layer, extra):
    return {
        "path": path,
        "start_x": _float_value(start_x),
        "start_y": _float_value(start_y),
        "rotation_deg": _float_value(rotation),
        "heights": cad_heights(_float_value(first_layer), _text(extra)),
    }


def _panel(form):
    for item in form:
        if hasattr(item, "addReinfTypeCB"):
            return item
    return None


def _toggle_on(panel):
    text = _text(getattr(panel, "addReinfToggle", None)).lower()
    if text == "":
        return False
    return text in ("on", "yes", "y", "true", "1")


def _checked(widget):
    if widget is None or not hasattr(widget, "isChecked"):
        return False
    return bool(widget.isChecked())


def _direction(panel, index):
    axis = _text(getattr(panel, "rebarDir" + str(index) + "Direction", None))
    if axis == "":
        axis = "X"
    return {
        "distance": _float_value(getattr(panel, "rebarDir" + str(index) + "Distance", None)),
        "axis": axis,
        "count": int(_float_value(getattr(panel, "rebarDir" + str(index) + "Count", None), 1)),
        "spacing": _float_value(getattr(panel, "rebarDir" + str(index) + "Spacing", None)),
        "heights": parse_height_values(_text(getattr(panel, "rebarDir" + str(index) + "Height", None))),
    }


def _element_type(panel):
    value = _text(getattr(panel, "reinfElementType", None))
    return value if value else _DEFAULT_REINF_ELEMENT_TYPE


def _float_value(widget, default=0.0):
    if widget is None:
        return default
    try:
        return float(widget.value())
    except (TypeError, ValueError, AttributeError):
        return default


def _text(widget):
    if widget is None:
        return ""
    if hasattr(widget, "currentText"):
        return str(widget.currentText()).strip()
    if hasattr(widget, "text"):
        return str(widget.text()).strip()
    return ""
