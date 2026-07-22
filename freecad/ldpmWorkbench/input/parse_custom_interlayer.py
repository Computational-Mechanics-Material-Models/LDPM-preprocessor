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
## This file parses the inputs for Custom Interlayer
##
## ===========================================================================

import re

_PLANE_AXES = {"Z": ("X", "Y"), "X": ("Y", "Z"), "Y": ("X", "Z")}
_LAYER_HEADER = re.compile(r"Layer\(\s*([XYZ])\s*\)\s*\[", re.IGNORECASE)
_CORNER_LINE = re.compile(r"corner\s+\d+\s*:", re.IGNORECASE)
_COORD = re.compile(r"([XYZ])\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", re.IGNORECASE)
_LIST_LINE = re.compile(
    r"^([XYZ])_list\s*=\s*\[([^\]]*)\]\s*,\s*mf\s*=\s*([12])\s*$",
    re.IGNORECASE,
)


def _clean_lines(text):

    lines = []
    for line in str(text or "").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if stripped:
            lines.append(stripped)
    return lines


def _parse_corner(line, axis):

    plane_axes = _PLANE_AXES[axis]
    values = {}
    for match in _COORD.finditer(line):
        key = match.group(1).upper()
        if key in plane_axes:
            values[key] = float(match.group(2))
    if set(values.keys()) != set(plane_axes):
        raise ValueError("Corner must define " + plane_axes[0] + " and " + plane_axes[1])
    return {plane_axes[0]: values[plane_axes[0]], plane_axes[1]: values[plane_axes[1]]}


def _parse_positions(text):

    if not str(text).strip():
        return []
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_custom_interlayer(text):

    lines = _clean_lines(text)
    if not lines:
        return []

    blocks = []
    index = 0
    while index < len(lines):
        header = _LAYER_HEADER.match(lines[index])
        if not header:
            raise ValueError("Expected Layer(...) [ at: " + lines[index])

        axis = header.group(1).upper()
        index += 1
        corner_lines = []
        while index < len(lines) and lines[index] != "]":
            corner_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ValueError("Missing ] for Layer(" + axis + ") block")

        index += 1
        if index >= len(lines):
            raise ValueError("Missing " + axis + "_list for Layer(" + axis + ") block")

        list_match = _LIST_LINE.match(lines[index])
        if not list_match or list_match.group(1).upper() != axis:
            raise ValueError("Expected " + axis + "_list = [...], mf=... after Layer(" + axis + ") block")

        corners = []
        for line in corner_lines:
            if _CORNER_LINE.search(line):
                corners.append(_parse_corner(line, axis))

        if len(corners) != 4:
            raise ValueError("Layer(" + axis + ") requires 4 corners")

        blocks.append(
            {
                "axis": axis,
                "planeAxes": _PLANE_AXES[axis],
                "corners": corners,
                "positions": _parse_positions(list_match.group(2)),
                "mf": int(list_match.group(3)),
            }
        )
        index += 1

    return blocks
