from core.classifier import classify_file
from core.organizer import organize_file

def process_file(filepath):
    """
    Bug fix: this used to only classify and print, never actually
    organize. Now it classifies, then ASKS before moving anything.
    Auto-moving files silently is risky — wrong classification could
    move something mid-use, or somewhere the user didn't expect.
    A confirmation step costs one keypress and prevents that class
    of problem entirely.
    """
    import os

    ext_info = classify_file(filepath)
    category, _ = ext_info

    if category == "Unknown":
        # Don't even ask for files we can't confidently classify —
        # there's nothing useful to do with "Unknown" yet.
        return

    file_name = os.path.basename(filepath)
    answer = input(f"Move '{file_name}' into the '{category}' folder? (y/n): ").strip().lower()

    if answer == "y":
        organize_file(filepath, ext_info)
        print(f"Moved {file_name} into {category}/")
    else:
        print(f"Skipped {file_name}")
