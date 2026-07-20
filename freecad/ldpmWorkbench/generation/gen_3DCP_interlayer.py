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
## Tag facet mF values for 3DCP-LDPM interlayer regions.
##
## ===========================================================================

import numpy as np

_AXIS = {"X": 0, "Y": 1, "Z": 2}
_CANONICAL_AXES = ("X", "Y", "Z")


def _interface_positions(origin, extent, first_layer, layer_thickness):

    if first_layer <= 0 or layer_thickness <= 0 or extent <= first_layer:
        return []

    positions = []
    pos = origin + first_layer
    end = origin + extent
    while pos < end - 1e-9:
        positions.append(pos)
        pos += layer_thickness
    return positions


def _width_interface_positions(origin, extent, layer_width):

    if layer_width <= 0 or extent <= layer_width:
        return []

    positions = []
    pos = origin + layer_width
    end = origin + extent
    while pos < end - 1e-9:
        positions.append(pos)
        pos += layer_width
    return positions


def _band_mask(coords, positions, half_band):

    mask = np.zeros(len(coords), dtype=bool)
    for center in positions:
        mask |= (coords >= center - half_band) & (coords <= center + half_band)
    return mask


def _axis_mf_map(enabled_axes, params=None):

    defaults = {"X": 2, "Y": 3, "Z": 4}
    params = params or {}
    axis_mf = {
        "X": int(params.get("xMf", defaults["X"])),
        "Y": int(params.get("yMf", defaults["Y"])),
        "Z": int(params.get("zMf", defaults["Z"])),
    }
    return {ax: axis_mf[ax] for ax in _CANONICAL_AXES if ax in enabled_axes}


def _merge_direction_configs(multi_directions):

    merged = {}
    for entry in multi_directions:
        if not entry.get("enabled"):
            continue
        axis = str(entry.get("axis", "Z")).strip().upper()
        if axis not in _AXIS:
            continue
        mode = str(entry.get("mode", "Height")).strip().title()
        if mode not in ("Width", "Height"):
            mode = "Height"
        if axis in merged and merged[axis] != mode:
            print(f"3DCP interlayer: axis {axis} has conflicting modes; using first entry.")
            continue
        merged[axis] = mode
    return merged


def apply_unidirectional(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    axis = _AXIS.get(str(params.get("axis", "Z")).strip().upper(), 2)
    minC = np.asarray(minC, dtype=float).reshape(3)
    maxC = np.asarray(maxC, dtype=float).reshape(3)

    origin = minC[axis]
    extent = maxC[axis] - minC[axis]
    first_layer = float(params.get("firstLayerThickness", 1.0))
    layer_thickness = float(params.get("layerThickness", 1.0))
    bulk_mf = int(params.get("bulkMf", 1))
    interlayer_mf = int(params.get("interlayerMf", 2))

    positions = _interface_positions(origin, extent, first_layer, layer_thickness)
    if not positions:
        print("3DCP interlayer: no interfaces found")
        return 0

    half_band = interface_thickness / 2.0
    coords = facetData[:, 6 + axis]
    mask = _band_mask(coords, positions, half_band)

    n_tagged = int(np.count_nonzero(mask))
    if n_tagged > 0:
        facetData[~mask, 18] = bulk_mf
        facetMaterial[~mask] = bulk_mf
        facetData[mask, 18] = interlayer_mf
        facetMaterial[mask] = interlayer_mf
        print(
            f"3DCP interlayer: tagged {n_tagged} facets along {params.get('axis', 'Z')}-axis "
            f"({len(positions)} interfaces, bulk mF={bulk_mf}, interlayer mF={interlayer_mf})"
        )
    else:
        print("3DCP interlayer: no facets tagged")

    return n_tagged


def apply_multidirectional(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    axis_modes = _merge_direction_configs(params.get("multiDirections", []))
    if not axis_modes:
        print("3DCP interlayer: multidirectional enabled but no axis selected; skipping.")
        return 0

    minC = np.asarray(minC, dtype=float).reshape(3)
    maxC = np.asarray(maxC, dtype=float).reshape(3)
    first_layer = float(params.get("firstLayerThickness", 1.0))
    layer_thickness = float(params.get("layerThickness", 1.0))
    layer_width = float(params.get("layerWidth", 1.0))
    bulk_mf = int(params.get("bulkMf", 1))
    overlap_mf = int(params.get("overlapMf", 5))
    half_band = interface_thickness / 2.0

    axis_masks = {}
    axis_counts = {}
    for axis, mode in axis_modes.items():
        axis_idx = _AXIS[axis]
        origin = minC[axis_idx]
        extent = maxC[axis_idx] - minC[axis_idx]
        if mode == "Height":
            positions = _interface_positions(origin, extent, first_layer, layer_thickness)
        else:
            positions = _width_interface_positions(origin, extent, layer_width)
        axis_counts[axis] = len(positions)
        if not positions:
            continue
        coords = facetData[:, 6 + axis_idx]
        axis_masks[axis] = _band_mask(coords, positions, half_band)

    if not axis_masks:
        print("3DCP interlayer: no multidirectional interfaces found")
        return 0

    mf_map = _axis_mf_map(axis_masks.keys(), params)
    n_facets = len(facetData)
    hit_count = np.zeros(n_facets, dtype=int)
    for mask in axis_masks.values():
        hit_count[mask] += 1

    final_mf = np.full(n_facets, bulk_mf, dtype=int)
    for axis, mask in axis_masks.items():
        single = mask & (hit_count == 1)
        final_mf[single] = mf_map[axis]
    overlap = hit_count >= 2
    final_mf[overlap] = overlap_mf

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf

    n_interface = int(np.count_nonzero(hit_count > 0))
    n_overlap = int(np.count_nonzero(overlap))
    axis_summary = ", ".join(f"{ax}={axis_counts.get(ax, 0)}" for ax in mf_map)
    print(
        f"3DCP interlayer: multidirectional tagged {n_interface} facets "
        f"(bulk mF={bulk_mf}, overlap mF={overlap_mf}, overlap facets={n_overlap}, interfaces: {axis_summary})"
    )
    return n_interface


def _footprint_mask(facetData, block):

    a0, a1 = block["planeAxes"]
    a0_idx = _AXIS[a0]
    a1_idx = _AXIS[a1]
    vals0 = [corner[a0] for corner in block["corners"]]
    vals1 = [corner[a1] for corner in block["corners"]]
    c0 = facetData[:, 6 + a0_idx]
    c1 = facetData[:, 6 + a1_idx]
    return (
        (c0 >= min(vals0))
        & (c0 <= max(vals0))
        & (c1 >= min(vals1))
        & (c1 <= max(vals1))
    )


def apply_custom(facetData, facetMaterial, minC, maxC, params):

    interface_thickness = float(params.get("interfaceThickness", 0.0))
    if interface_thickness <= 0:
        return 0

    blocks = params.get("customLayers") or []
    if not blocks and params.get("customDefinition"):
        from freecad.ldpmWorkbench.input.parse_custom_interlayer import parse_custom_interlayer

        blocks = parse_custom_interlayer(params["customDefinition"])
    if not blocks:
        print("3DCP interlayer: no custom layers found")
        return 0

    bulk_mf = int(params.get("bulkMf", 1))
    if bulk_mf not in (1, 2):
        bulk_mf = 1

    half_band = interface_thickness / 2.0
    final_mf = np.full(len(facetData), bulk_mf, dtype=int)

    for block in blocks:
        axis_idx = _AXIS[block["axis"]]
        positions = list(dict.fromkeys(block.get("positions") or []))
        if not positions:
            continue
        coords = facetData[:, 6 + axis_idx]
        mask = _band_mask(coords, positions, half_band) & _footprint_mask(facetData, block)
        interlayer_mf = int(block.get("mf", 2))
        if interlayer_mf not in (1, 2):
            interlayer_mf = 2
        final_mf[mask] = interlayer_mf

    facetData[:, 18] = final_mf
    facetMaterial[:] = final_mf

    n_tagged = int(np.count_nonzero(final_mf != bulk_mf))
    if n_tagged > 0:
        print(
            f"3DCP interlayer: custom tagged {n_tagged} facets "
            f"({len(blocks)} layer blocks, bulk mF={bulk_mf})"
        )
    else:
        print("3DCP interlayer: no custom facets tagged")

    return n_tagged


def apply_3DCP_interlayer(facetData, facetMaterial, minC, maxC, params):

    if not params.get("enabled", False):
        return 0

    interlayer_type = params.get("interlayerType", "")
    if interlayer_type == "Unidirectional Interlayer":
        return apply_unidirectional(facetData, facetMaterial, minC, maxC, params)
    if interlayer_type == "Multidirectional Interlayer":
        return apply_multidirectional(facetData, facetMaterial, minC, maxC, params)
    if interlayer_type == "Custom":
        return apply_custom(facetData, facetMaterial, minC, maxC, params)

    print(f"Interlayer type '{interlayer_type}' is not implemented yet; skipping.")
    return 0
