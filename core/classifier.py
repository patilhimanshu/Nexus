import os
from config.file_types import extension_map

def classify_file(filepath):
    file_name = os.path.basename(filepath)
    name, extension = os.path.splitext(file_name)
    ext_info = extension_map.get(extension.lower(), ("Unknown", ""))
    parent_folder, subfolder = ext_info

    print(f"File     : {file_name}")
    print(f"Extension: {extension}")
    print(f"Folder   : {parent_folder}/{subfolder}" if subfolder else f"Folder   : {parent_folder}/")
    print()

    return ext_info