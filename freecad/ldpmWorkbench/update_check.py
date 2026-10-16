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
## Update check for LDPM workbench
##
## ===========================================================================


import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

import FreeCAD as App
import FreeCADGui as Gui

try:
    from PySide import QtCore, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtWidgets
    except ImportError:
        from PySide import QtGui, QtCore

        QtWidgets = QtGui

from freecad.ldpmWorkbench.version import __version__

GITHUB_REPOSITORY = "Computational-Mechanics-Material-Models/LDPM-preprocessor"
_MOD_FOLDER_NAME = "chronoConcrete"
_PREFERENCE_GROUP = "User parameter:BaseApp/Preferences/Mod/chronoConcrete"
_SKIPPED_KEY = "SkippedRelease"
_checked_this_session = False


def check_for_update():
    global _checked_this_session
    if _checked_this_session:
        return
    _checked_this_session = True
    try:
        release = _latest_release()
    except Exception as exc:
        App.Console.PrintMessage(
            "LDPM workbench update check skipped: %s\n"
            % exc
        )
        return
    if release is None:
        return
    remote = release["version"]
    if _version_key(remote) <= _version_key(__version__):
        return
    if _skipped_release() == remote:
        return
    _offer_update(release)


def _latest_release():
    url = "https://api.github.com/repos/%s/releases/latest" % GITHUB_REPOSITORY
    try:
        payload = _read_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    tag = str(payload.get("tag_name") or "").strip()
    version = tag[1:] if tag.lower().startswith("v") else tag
    if not version:
        return None
    return {
        "version": version,
        "tag": tag or version,
        "notes": str(payload.get("body") or "").strip(),
        "zip_url": str(payload.get("zipball_url") or "").strip(),
    }


def _offer_update(release):
    notes = release["notes"]
    if len(notes) > 500:
        notes = notes[:500].rstrip() + "..."
    box = QtWidgets.QMessageBox(Gui.getMainWindow())
    box.setWindowTitle("LDPM workbench")
    box.setIcon(QtWidgets.QMessageBox.Information)
    box.setText("LDPM workbench new updates available.")
    detail = "Installed version: %s\nNew version: %s" % (__version__, release["version"])
    if notes:
        detail = detail + "\n\n" + notes
    detail = detail + "\n\nUpdate now downloads the release and replaces the chronoConcrete folder after FreeCAD closes."
    box.setInformativeText(detail)
    skip_button = box.addButton("Skip", QtWidgets.QMessageBox.RejectRole)
    update_button = box.addButton("Update now", QtWidgets.QMessageBox.AcceptRole)
    box.setDefaultButton(skip_button)
    box.exec_()
    if box.clickedButton() is not update_button:
        _remember_skip(release["version"])
        return
    try:
        source = _download_release(release)
        _start_replace_after_exit(source)
    except Exception as exc:
        QtWidgets.QMessageBox.warning(
            Gui.getMainWindow(),
            "LDPM workbench",
            "The new version could not be downloaded.\n\n%s" % exc,
        )
        return
    QtWidgets.QMessageBox.information(
        Gui.getMainWindow(),
        "LDPM workbench",
        "Version %s is ready.\n\nFreeCAD will close so the chronoConcrete folder can be replaced. Reopen FreeCAD after it exits."
        % release["version"],
    )
    QtCore.QTimer.singleShot(300, lambda: Gui.runCommand("Std_Quit"))


def _download_release(release):
    if not release["zip_url"]:
        raise RuntimeError("The latest release has no zip download.")
    staging = tempfile.mkdtemp(prefix="chronoConcrete-update-")
    archive_path = os.path.join(staging, "release.zip")
    request = urllib.request.Request(release["zip_url"], headers={"User-Agent": "chronoConcrete-update"})
    with urllib.request.urlopen(request, timeout=120) as response:
        with open(archive_path, "wb") as handle:
            shutil.copyfileobj(response, handle)
    unpack = os.path.join(staging, "unpack")
    os.makedirs(unpack)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(unpack)
    root = _find_workbench_root(unpack)
    if root is None:
        shutil.rmtree(staging, ignore_errors=True)
        raise RuntimeError("The release zip does not contain freecad/ldpmWorkbench.")
    return root


def _start_replace_after_exit(source):
    dest = os.path.join(_mod_dir(), _MOD_FOLDER_NAME)
    script = os.path.join(tempfile.gettempdir(), "chronoConcrete_update.py")
    shutil.copyfile(os.path.join(os.path.dirname(__file__), "update.py"), script)
    command = [
        _python_executable(),
        script,
        "--pid",
        str(os.getpid()),
        "--source",
        source,
        "--dest",
        dest,
    ]
    flags = 0
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    subprocess.Popen(command, close_fds=True, creationflags=flags)


def _find_workbench_root(folder):
    if os.path.isdir(os.path.join(folder, "freecad", "ldpmWorkbench")):
        return folder
    for name in os.listdir(folder):
        candidate = os.path.join(folder, name)
        if os.path.isdir(os.path.join(candidate, "freecad", "ldpmWorkbench")):
            return candidate
    return None


def _mod_dir():
    user_dir = ""
    try:
        user_dir = App.getUserAppDataDir()
    except Exception:
        user_dir = ""
    if user_dir:
        return os.path.join(user_dir, "Mod")
    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        return os.path.join(appdata, "FreeCAD", "Mod")
    return os.path.join(os.path.expanduser("~"), ".FreeCAD", "Mod")


def _python_executable():
    folder = os.path.dirname(sys.executable)
    name = os.path.basename(sys.executable).lower()
    if name.startswith("freecad"):
        for candidate_name in ("python.exe", "pythonw.exe", "python", "python3"):
            candidate = os.path.join(folder, candidate_name)
            if os.path.isfile(candidate):
                return candidate
    return sys.executable


def _read_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "chronoConcrete-update",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _version_key(value):
    parts = []
    for piece in str(value).strip().lstrip("vV").split("."):
        number = ""
        for char in piece:
            if char.isdigit():
                number += char
            else:
                break
        parts.append(int(number or "0"))
    return tuple(parts)


def _preference():
    return App.ParamGet(_PREFERENCE_GROUP)


def _skipped_release():
    try:
        return str(_preference().GetString(_SKIPPED_KEY, "")).strip()
    except Exception:
        return ""


def _remember_skip(version):
    try:
        _preference().SetString(_SKIPPED_KEY, version)
    except Exception:
        pass
