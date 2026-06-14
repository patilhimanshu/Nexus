import os
import shutil
def organize_file(filepath, ext_info):
    category, ignored = ext_info
    if category == "Unknown" and ignored == "Unknown":
        destination = "Unknown"
    elif ignored != "Unknown":
        destination = ignored
    else:
        destination = category

    parent_dir = os.path.dirname(filepath)
    dest_dir = os.path.join(parent_dir, destination)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(filepath, dest_dir)