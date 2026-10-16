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
## Preview module for surface mesh preview
##
## ===========================================================================


import math
import os

import FreeCADGui as Gui
import FreeCAD as App
import Mesh
import Fem
import Part

try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide import QtCore, QtGui
        QtWidgets = QtCore

from freecad.ldpmWorkbench import ICONPATH
from freecad.ldpmWorkbench.util.cwloadUIfile import cwloadUIfile
from freecad.ldpmWorkbench.util.cwloadUIicon import cwloadUIicon

_pending_launch = None
_PATH_ROLE = int(QtCore.Qt.UserRole)
_CONTROL_W = 150
_CONTROL_H = 24
_UPLOAD_BOX_W = 75
_UPLOAD_BTN_W = 16
_SWATCH = 18
_SURFACE_COLOR = (0.55, 0.55, 0.55)
_EDGE_COLOR = (0.92, 0.92, 0.92)
_INTERFACE_COLOR = (0.55, 0.78, 0.95)


class _ListDeleteFilter(QtCore.QObject):
    def __init__(self, on_delete, parent=None):
        super(_ListDeleteFilter, self).__init__(parent)
        self._on_delete = on_delete

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
                self._on_delete()
                return True
        return False


def _is_interface_path(path):
    name = os.path.basename(str(path)).lower()
    return "interface" in name


def _display_modes(kind, display):
    """Surface is shaded only. Surface with edges uses the FEM mesh wire on the faces."""
    if display == "Wireframe":
        if kind == "vtk":
            return ["Wireframe", "Wireframe & Nodes"]
        return ["Wireframe"]
    if display == "Surface with edges":
        if kind == "vtk":
            return ["Faces & Wireframe", "Faces, Wireframe & Nodes", "Elements"]
        return ["Flat Lines", "Surface with Edges"]
    if kind == "vtk":
        return ["Faces", "Flat", "Surface", "Shaded"]
    return ["Shaded", "Flat", "Surface"]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _length(a):
    return (a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) ** 0.5


def _topology(obj, kind):
    if kind == "stl":
        pts, facets = obj.Mesh.Topology
        points = [(float(p.x), float(p.y), float(p.z)) for p in pts]
        faces = [tuple(int(i) for i in facet) for facet in facets]
        return points, faces
    fem = getattr(obj, "FemMesh", None)
    if fem is None:
        return [], []
    nodes = fem.Nodes
    raw_faces = []
    try:
        face_ids = list(fem.Faces)
    except Exception:
        face_ids = []
    for fid in face_ids:
        try:
            nids = tuple(fem.getElementNodes(fid))
        except Exception:
            continue
        if len(nids) >= 3:
            raw_faces.append(nids)
    if not raw_faces:
        raw_faces = _volume_skin(fem)
    id_to_i = {}
    points = []
    for nid, vec in nodes.items():
        id_to_i[nid] = len(points)
        points.append((float(vec.x), float(vec.y), float(vec.z)))
    faces = []
    for nids in raw_faces:
        try:
            faces.append(tuple(id_to_i[nid] for nid in nids))
        except KeyError:
            continue
    return points, faces


def _volume_skin(fem):
    try:
        vol_ids = list(fem.Volumes)
    except Exception:
        return []
    counts = {}
    tet_faces = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
    for vid in vol_ids:
        try:
            nids = tuple(fem.getElementNodes(vid))
        except Exception:
            continue
        if len(nids) < 4:
            continue
        for loc in tet_faces:
            tri = tuple(sorted(nids[i] for i in loc))
            counts[tri] = counts.get(tri, 0) + 1
    return [tri for tri, count in counts.items() if count == 1]


def _border_segments(points, faces, angle_deg=40.0):
    """Boundary edges and sharp corners only. Shared mesh edges on a smooth face are dropped."""
    edge_normals = {}
    cos_limit = math.cos(math.radians(angle_deg))
    for face in faces:
        idxs = [int(i) for i in face]
        if len(idxs) < 3:
            continue
        p0 = points[idxs[0]]
        p1 = points[idxs[1]]
        p2 = points[idxs[2]]
        normal = _cross(_sub(p1, p0), _sub(p2, p0))
        length = _length(normal)
        if length < 1e-12:
            continue
        normal = (normal[0] / length, normal[1] / length, normal[2] / length)
        count = len(idxs)
        for i in range(count):
            a = idxs[i]
            b = idxs[(i + 1) % count]
            key = (a, b) if a < b else (b, a)
            edge_normals.setdefault(key, []).append(normal)
    segments = []
    for (a, b), normals in edge_normals.items():
        if len(normals) < 2:
            segments.append((a, b))
            continue
        keep = False
        for i in range(len(normals)):
            for j in range(i + 1, len(normals)):
                dot = normals[i][0] * normals[j][0] + normals[i][1] * normals[j][1] + normals[i][2] * normals[j][2]
                if dot < cos_limit:
                    keep = True
                    break
            if keep:
                break
        if keep:
            segments.append((a, b))
    return segments


def _border_shape(points, faces):
    if not points or not faces:
        return None
    segments = _border_segments(points, faces)
    edges = []
    for a, b in segments:
        p0 = App.Vector(points[a][0], points[a][1], points[a][2])
        p1 = App.Vector(points[b][0], points[b][1], points[b][2])
        if p0.distanceToPoint(p1) < 1e-9:
            continue
        edges.append(Part.makeLine(p0, p1))
    if not edges:
        return None
    return Part.Compound(edges)


def _make_border(doc, obj, kind):
    try:
        shape = _border_shape(*_topology(obj, kind))
    except Exception:
        return None
    if shape is None:
        return None
    border = doc.addObject("Part::Feature", obj.Name + "_border")
    border.Label = obj.Label + " border"
    border.Shape = shape
    return border


def _set_prop(view, name, value):
    if view is None:
        return False
    try:
        setattr(view, name, value)
        return True
    except Exception:
        return False


def _css_color(rgb):
    return "#%02x%02x%02x" % (
        int(round(float(rgb[0]) * 255)),
        int(round(float(rgb[1]) * 255)),
        int(round(float(rgb[2]) * 255)),
    )


def _qcolor_tuple(color):
    return (float(color.redF()), float(color.greenF()), float(color.blueF()))


def _tuple_qcolor(rgb):
    return QtGui.QColor(_css_color(rgb))


def _apply_style(view, kind, display, is_interface, surface_color=None, interface_color=None, transparency=0):
    if view is None:
        return
    for mode in _display_modes(kind, display):
        if _set_prop(view, "DisplayMode", mode):
            break
    surface_color = surface_color or _SURFACE_COLOR
    interface_color = interface_color or _INTERFACE_COLOR
    color = interface_color if is_interface else surface_color
    _set_prop(view, "ShapeColor", color)
    _set_prop(view, "PointColor", color)
    try:
        fade = int(transparency)
    except (TypeError, ValueError):
        fade = 0
    if fade < 0:
        fade = 0
    if fade > 100:
        fade = 100
    if is_interface:
        fade = 0
    try:
        if hasattr(view, "ShapeAppearance") and hasattr(view.ShapeAppearance, "DiffuseColor"):
            view.ShapeAppearance.DiffuseColor = color
    except Exception:
        pass
    _set_prop(view, "Transparency", fade)


def _apply_border(view, visible, is_interface):
    if view is None:
        return
    color = (0.12, 0.32, 0.55) if is_interface else (0.12, 0.12, 0.12)
    _set_prop(view, "DisplayMode", "Wireframe")
    _set_prop(view, "LineColor", color)
    _set_prop(view, "LineWidth", 3.0)
    _set_prop(view, "Visibility", bool(visible))


def _gui_view(doc_name, obj):
    try:
        return Gui.getDocument(doc_name).getObject(obj.Name)
    except Exception:
        return getattr(obj, "ViewObject", None)


def _load_stl(doc, path):
    mesh = Mesh.Mesh(path)
    name = os.path.splitext(os.path.basename(path))[0]
    obj = doc.addObject("Mesh::Feature", name)
    obj.Label = name
    obj.Mesh = mesh
    return obj, "stl"


def _load_vtk(doc, path):
    before = set(doc.Objects)
    Fem.insert(str(path), doc.Name)
    added = [obj for obj in doc.Objects if obj not in before]
    if not added:
        raise RuntimeError("VTK import produced no object: %s" % path)
    obj = added[-1]
    try:
        obj.Label = os.path.splitext(os.path.basename(path))[0]
    except Exception:
        pass
    return obj, "vtk"


def _load_path(doc, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".stl":
        return _load_stl(doc, path)
    if ext in (".vtk", ".vtu", ".vtp"):
        return _load_vtk(doc, path)
    raise ValueError("Unsupported mesh file type: %s" % ext)


def preview_mesh(paths, display, surface_color=None, interface_color=None, transparency=0):
    if isinstance(paths, (str, bytes)):
        paths = [paths]
    clean = []
    for item in paths or []:
        if item is None:
            continue
        text = str(item).strip()
        if text == "" or text in clean:
            continue
        clean.append(text)
    if not clean:
        raise ValueError("Mesh file is not set.")
    for item in clean:
        if not os.path.isfile(item):
            raise ValueError("Mesh file is not set: %s" % item)

    doc = App.newDocument("MeshPreview")
    loaded = []
    try:
        App.setActiveDocument(doc.Name)
        Gui.setActiveDocument(doc.Name)
        for item in clean:
            obj, kind = _load_path(doc, item)
            border = _make_border(doc, obj, kind)
            loaded.append((obj, kind, item, border))
        doc.recompute()
        Gui.updateGui()
        show_border = display == "Surface"
        for obj, kind, item, border in loaded:
            is_interface = _is_interface_path(item)
            _apply_style(
                _gui_view(doc.Name, obj),
                kind,
                display,
                is_interface,
                surface_color,
                interface_color,
                transparency,
            )
            if border is not None:
                _apply_border(_gui_view(doc.Name, border), show_border, is_interface)
        Gui.updateGui()
        view3d = Gui.getDocument(doc.Name).activeView()
        if view3d is not None:
            view3d.viewAxonometric()
            view3d.fitAll()
        return doc, loaded
    except Exception:
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass
        raise


def launch_mesh_preview(geometry=None, interfaces=None, auto_preview=True):
    global _pending_launch
    files = []
    if geometry:
        files.append(str(geometry))
    if interfaces:
        files.append(str(interfaces))
    _pending_launch = {
        "files": files,
        "auto_preview": bool(auto_preview),
    }
    try:
        Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(inputWindow_MeshPreview())


class inputWindow_MeshPreview:
    def __init__(self):
        global _pending_launch
        self.form = []
        self._preview_doc_name = None
        self._preview_items = []
        self._surface_color = _SURFACE_COLOR
        self._interface_color = _INTERFACE_COLOR
        self.form.append(cwloadUIfile("ui_MeshPreview.ui"))
        self.form[0].setWindowTitle("Mesh Preview")
        cwloadUIicon(self.form[0], "mesh_preview.svg")
        self._style_file_widgets()
        QtCore.QObject.connect(self.form[0].meshFileButton, QtCore.SIGNAL("clicked()"), self.openMeshFile)
        QtCore.QObject.connect(self.form[0].previewButton, QtCore.SIGNAL("clicked()"), self.previewMesh)
        QtCore.QObject.connect(
            self.form[0].meshDisplayCB,
            QtCore.SIGNAL("currentIndexChanged(int)"),
            self.applyDisplayMode,
        )
        QtCore.QObject.connect(
            self.form[0].transparencySlider,
            QtCore.SIGNAL("valueChanged(int)"),
            self.onTransparency,
        )
        QtCore.QObject.connect(
            self.form[0].surfaceColorButton, QtCore.SIGNAL("clicked()"), self.pickSurfaceColor
        )
        QtCore.QObject.connect(
            self.form[0].interfaceColorButton, QtCore.SIGNAL("clicked()"), self.pickInterfaceColor
        )
        QtCore.QObject.connect(
            self.form[0].meshFileList,
            QtCore.SIGNAL("itemSelectionChanged()"),
            self._sync_path_box,
        )
        self._list_delete_filter = _ListDeleteFilter(self.removeSelectedFiles, self.form[0].meshFileList)
        self.form[0].meshFileList.installEventFilter(self._list_delete_filter)

        pending = _pending_launch
        _pending_launch = None
        if pending and pending.get("files"):
            self.form[0].meshSourceCB.setCurrentText("VTK")
            for path in pending["files"]:
                self._add_file(path)
            if pending.get("auto_preview", True):
                self.previewMesh()

    def _style_file_widgets(self):
        form = self.form[0]
        try:
            form.gridLayout_meshPreview.setVerticalSpacing(10)
            form.gridLayout_meshPreview.setHorizontalSpacing(4)
            form.gridLayout_meshPreview.setColumnStretch(0, 1)
        except Exception:
            pass
        for layout_name in (
            "horizontalLayout_meshType",
            "horizontalLayout_meshFile",
            "horizontalLayout_meshDisplay",
            "horizontalLayout_transparency",
            "horizontalLayout_preview",
        ):
            layout = getattr(form, layout_name, None)
            if layout is None:
                continue
            try:
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)
            except Exception:
                pass
        lst = form.meshFileList
        try:
            lst.setFrameShape(QtWidgets.QFrame.Box)
            lst.setFrameShadow(QtWidgets.QFrame.Plain)
            lst.setLineWidth(1)
        except Exception:
            pass
        try:
            lst.setStyleSheet(
                "QListWidget {"
                " background-color: #ffffff;"
                " color: #000000;"
                " border: 1px solid #7a7a7a;"
                "}"
            )
        except Exception:
            pass
        for name in ("meshSourceCB", "meshDisplayCB", "previewButton"):
            widget = getattr(form, name, None)
            if widget is None:
                continue
            try:
                widget.setFixedSize(_CONTROL_W, _CONTROL_H)
            except Exception:
                pass
        try:
            form.meshFilePath.setFixedSize(_UPLOAD_BOX_W, _CONTROL_H)
            form.meshFilePath.setStyleSheet(
                "QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #7a7a7a; }"
            )
        except Exception:
            pass
        try:
            form.meshFileButton.setFixedSize(_UPLOAD_BTN_W, _CONTROL_H)
            form.meshFileButton.setStyleSheet("QPushButton { padding: 0px; }")
        except Exception:
            pass
        try:
            form.transparencySlider.setFixedSize(108, _CONTROL_H)
            form.transparencyValue.setText("%d%%" % int(form.transparencySlider.value()))
        except Exception:
            pass
        self._paint_swatch(form.surfaceColorButton, self._surface_color)
        self._paint_swatch(form.interfaceColorButton, self._interface_color)

    def _paint_swatch(self, button, rgb):
        try:
            button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            button.setFixedSize(_SWATCH, _SWATCH)
            button.setStyleSheet(
                "QPushButton {"
                " background-color: %s;"
                " border: 1px solid #7a7a7a;"
                " padding: 0px;"
                " min-width: %dpx; max-width: %dpx;"
                " min-height: %dpx; max-height: %dpx;"
                "}" % (_css_color(rgb), _SWATCH, _SWATCH, _SWATCH, _SWATCH)
            )
            button.setFixedSize(_SWATCH, _SWATCH)
        except Exception:
            pass

    def _pick_color(self, current, title):
        color = QtWidgets.QColorDialog.getColor(_tuple_qcolor(current), None, title)
        if color is None or not color.isValid():
            return None
        return _qcolor_tuple(color)

    def pickSurfaceColor(self):
        picked = self._pick_color(self._surface_color, "Surface color")
        if picked is None:
            return
        self._surface_color = picked
        self._paint_swatch(self.form[0].surfaceColorButton, picked)
        self.applyDisplayMode()

    def pickInterfaceColor(self):
        picked = self._pick_color(self._interface_color, "Interface color")
        if picked is None:
            return
        self._interface_color = picked
        self._paint_swatch(self.form[0].interfaceColorButton, picked)
        self.applyDisplayMode()

    def _sync_path_box(self):
        lst = self.form[0].meshFileList
        selected = lst.selectedItems()
        if selected:
            path = selected[-1].data(_PATH_ROLE) or ""
            self.form[0].meshFilePath.setText(os.path.basename(str(path)))
            self.form[0].meshFilePath.setToolTip(str(path))
            return
        if lst.count() <= 0:
            self.form[0].meshFilePath.clear()
            self.form[0].meshFilePath.setToolTip("")
            return
        last = lst.item(lst.count() - 1)
        path = last.data(_PATH_ROLE) if last is not None else ""
        if lst.count() == 1:
            self.form[0].meshFilePath.setText(os.path.basename(str(path or "")))
        else:
            self.form[0].meshFilePath.setText("%d files" % lst.count())
        self.form[0].meshFilePath.setToolTip(str(path or ""))

    def _add_file(self, path):
        path = str(path).strip()
        if path == "" or not os.path.isfile(path):
            return
        for i in range(self.form[0].meshFileList.count()):
            item = self.form[0].meshFileList.item(i)
            if item is not None and item.data(_PATH_ROLE) == path:
                return
        item = QtWidgets.QListWidgetItem(os.path.basename(path))
        item.setData(_PATH_ROLE, path)
        item.setToolTip(path)
        self.form[0].meshFileList.addItem(item)
        self.form[0].meshFileList.setCurrentItem(item)
        self._sync_path_box()

    def removeSelectedFiles(self):
        selected = list(self.form[0].meshFileList.selectedItems())
        if not selected:
            return
        for item in selected:
            row = self.form[0].meshFileList.row(item)
            self.form[0].meshFileList.takeItem(row)
        self._sync_path_box()

    def _selected_or_all_paths(self):
        selected = self.form[0].meshFileList.selectedItems()
        items = selected if selected else [
            self.form[0].meshFileList.item(i)
            for i in range(self.form[0].meshFileList.count())
        ]
        paths = []
        for item in items:
            if item is None:
                continue
            path = item.data(_PATH_ROLE)
            if path and path not in paths:
                paths.append(path)
        return paths

    def openMeshFile(self):
        path = App.ConfigGet("UserHomePath")
        kind = self.form[0].meshSourceCB.currentText()
        if kind == "VTK":
            filetype = "VTK (*.vtu *.vtp *.vtk);;All Files (*.*)"
        else:
            filetype = "Surface mesh (*.stl *.obj *.ply *.off);;All Files (*.*)"
        names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Read mesh files", path, filetype
        )
        if not names:
            App.Console.PrintMessage("Process aborted" + "\n")
            return
        for name in names:
            self._add_file(name)
        self._sync_path_box()

    def transparencyPercent(self):
        try:
            return int(self.form[0].transparencySlider.value())
        except Exception:
            return 0

    def onTransparency(self, value):
        try:
            self.form[0].transparencyValue.setText("%d%%" % int(value))
        except Exception:
            pass
        self.applyDisplayMode()

    def applyDisplayMode(self, _index=None):
        if not self._preview_items or not self._preview_doc_name:
            return
        display = self.form[0].meshDisplayCB.currentText()
        show_border = display == "Surface"
        transparency = self.transparencyPercent()
        for item in self._preview_items:
            obj, kind, path = item[0], item[1], item[2]
            border = item[3] if len(item) > 3 else None
            try:
                if obj is None or getattr(obj, "isDerivedFrom", None) is None:
                    continue
            except Exception:
                continue
            is_interface = _is_interface_path(path)
            _apply_style(
                _gui_view(self._preview_doc_name, obj),
                kind,
                display,
                is_interface,
                self._surface_color,
                self._interface_color,
                transparency,
            )
            if border is not None:
                try:
                    _apply_border(
                        _gui_view(self._preview_doc_name, border),
                        show_border,
                        is_interface,
                    )
                except Exception:
                    pass
        Gui.updateGui()

    def previewMesh(self):
        paths = self._selected_or_all_paths()
        if not paths:
            App.Console.PrintError("Mesh file is not set.\n")
            return
        display = self.form[0].meshDisplayCB.currentText()
        try:
            doc, loaded = preview_mesh(
                paths,
                display,
                self._surface_color,
                self._interface_color,
                self.transparencyPercent(),
            )
            self._preview_doc_name = doc.Name
            self._preview_items = loaded
        except Exception as exc:
            self._preview_doc_name = None
            self._preview_items = []
            App.Console.PrintError("Mesh preview failed: %s\n" % exc)

    def reject(self):
        try:
            Gui.ActiveDocument.resetEdit()
            Gui.Control.closeDialog()
        except Exception:
            Gui.Control.closeDialog()


class input_MeshPreview_Class:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "mesh_preview.svg"),
            "MenuText": "Mesh Preview",
            "ToolTip": "Preview an uploaded mesh",
        }

    def Activated(self):
        try:
            Gui.Control.closeDialog()
        except Exception:
            pass
        Gui.Control.showDialog(inputWindow_MeshPreview())
        return

    def IsActive(self):
        return True


Gui.addCommand("mod_MeshPreview", input_MeshPreview_Class())
