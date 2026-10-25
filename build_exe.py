"""
build_exe.py

This script automates compiling PMD Explorers of the Console to an executable using PyInstaller.
This probably only works on Windows systems. Please let me know!
"""
import os
import sys
import shutil
import subprocess

def build():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(root_dir, "src")
    src_data_dir = os.path.join(src_dir, "data")
    dist_dir = os.path.join(root_dir, "dist")
    dist_data_dir = os.path.join(dist_dir, "data")
    spec_file = os.path.join(root_dir, "PMD_Explorers_of_the_Console.spec")

    print(f"***Starting PyInstaller Build***")
    print(f"Root: {root_dir}")
    print(f"Spec: {spec_file}")

    #1. Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", spec_file]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root_dir)
    if result.returncode != 0:
        print("Error: PyInstaller build failed!", file=sys.stderr)
        sys.exit(result.returncode)

    #2. Copy JSON data files to dist/data/
    print(f"\n*** Copying JSON Data Files to {dist_data_dir}***")
    os.makedirs(dist_data_dir, exist_ok=True)
    json_files = ["items.json", "moves.json", "pokemon.json"]
    for filename in json_files:
        src_file = os.path.join(src_data_dir, filename)
        dest_file = os.path.join(dist_data_dir, filename)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            print(f"  Copied: data/{filename} ({os.path.getsize(dest_file):,} bytes)")
        else:
            print(f"  WARNING: Source data file not found: {src_file}", file=sys.stderr)

    #3. Copy documentation and metadata files to dist/
    print(f"\n***Copying Documentation Files to {dist_dir}***")
    doc_files = ["manual.txt", "CHANGELOG.txt", "CREDITS.txt", "LICENSE"]
    for filename in doc_files:
        src_file = os.path.join(src_dir, filename)
        dest_file = os.path.join(dist_dir, filename)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            print(f"  Copied: {filename}")

    exe_path = os.path.join(dist_dir, "PMD_Explorers_of_the_Console.exe")
    print(f"\n***Build completed successfully!***")
    if os.path.exists(exe_path):
        print(f"Executable: {exe_path} ({os.path.getsize(exe_path):,} bytes)")
    print(f"Data folder: {dist_data_dir}")

if __name__ == "__main__":
    build()
