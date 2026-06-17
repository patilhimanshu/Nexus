import os
from config.file_types import extension_map

def classify_file(filepath):
    file_name = os.path.basename(filepath)
    name, extension = os.path.splitext(file_name)
    category = extension_map.get(extension, "Unknown")

    print("Filename :" + file_name + "\n")
    print("Category :" + category + "\n")
    print("File extension :" + extension + "\n")
    print("\n")

    # Bug fix: this function used to only print and return None.
    # organizer.py needs (category, override) as a tuple to decide
    # where to move the file — "override" is reserved for a future
    # manual category assignment feature, "Unknown" means "use the
    # extension-based category as-is".
    return category, "Unknown"
