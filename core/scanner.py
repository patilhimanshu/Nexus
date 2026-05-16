def start_scan():
    import os
    from core.pipeline import process_file
    from config.settings import path

    files = os.listdir(path)
    for file in files:
        full_path = os.path.join(path, file)
        process_file(full_path)


