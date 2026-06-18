import os
from core.classifier import classify_file
from core.organizer import organize_file
from core.metadata import get_metadata

def process_file(filepath):
    # Skip folders — only process actual files
    if os.path.isdir(filepath):
        return

    metadata = get_metadata(filepath)
    print(f"--- Processing: {metadata['name']} | {metadata['size']['formatted']} | Modified: {metadata['last_modified']['formatted']}")
    ext_info = classify_file(filepath)
    organize_file(filepath, ext_info)