"""
data_utils.py

Functions to assist with compiling the game with PyInstaller
"""
#Copyright (C) 2026 C437RP13 (GitHub: Axolotl and Fish)
#Licensed under the GNU General Public License v3. See LICENSE for more info

import os
import sys


def get_app_base_dir() -> str:
    """Returns the base application directory.
    When running as a PyInstaller frozen executable, returns the directory containing the .exe.
    Otherwise, returns the current working directory or game root directory
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    
    #In source mode, locate the directory containing 'src' (project root) or src directory itself
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    return project_root


def get_data_file_path(filename: str) -> str:
    """Finds the absolute path to a data file in the data/ folder.
    """
    candidates: list[str] = []

    #1. If running in a frozen bundle (PyInstaller)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "data", filename))
        candidates.append(os.path.join(exe_dir, "src", "data", filename))
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "data", filename))

    #2. Current working directory
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "data", filename))
    candidates.append(os.path.join(cwd, "src", "data", filename))

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
            
    #3. Source-level directories
    src_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(src_dir, "data", filename))

    project_root = os.path.dirname(src_dir)
    candidates.append(os.path.join(project_root, "data", filename))
    candidates.append(os.path.join(project_root, "src", "data", filename))

    #Return the preferred candidate if not found
    return os.path.abspath(candidates[0]) if candidates else os.path.abspath(os.path.join("data", filename))
