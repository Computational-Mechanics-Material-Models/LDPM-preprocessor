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
## Update workbench with new release from GitHub repository
##
## ===========================================================================

import argparse
import ctypes
import os
import shutil
import time


def _process_alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        access = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _wait_until_closed(pid):
    while _process_alive(pid):
        time.sleep(0.5)
    time.sleep(1.0)


def _replace_folder(source, dest):
    parent = os.path.dirname(dest)
    os.makedirs(parent, exist_ok=True)
    backup = dest + "_previous"
    if os.path.isdir(backup):
        shutil.rmtree(backup)
    if os.path.isdir(dest):
        os.rename(dest, backup)
    try:
        shutil.move(source, dest)
    except Exception:
        if os.path.isdir(backup) and not os.path.isdir(dest):
            os.rename(backup, dest)
        raise
    if os.path.isdir(backup):
        shutil.rmtree(backup, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    log_path = os.path.join(os.path.dirname(args.dest), "chronoConcrete_update.log")
    try:
        _wait_until_closed(args.pid)
        _replace_folder(args.source, args.dest)
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write("Updated LDPM workbench at %s\n" % args.dest)
    except Exception as exc:
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write("LDPM workbench update failed: %s\n" % exc)
        raise


if __name__ == "__main__":
    main()
