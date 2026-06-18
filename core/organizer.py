import os
import shutil
from config.settings import path as root_path

def organize_file(filepath, ext_info):
    parent_folder, subfolder = ext_info

    base_dir = root_path
    if subfolder:
        dest_dir = os.path.join(base_dir, parent_folder, subfolder)
    else:
        dest_dir = os.path.join(base_dir, parent_folder)

    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(filepath, dest_dir)
    print(f"Moved to → {dest_dir}")