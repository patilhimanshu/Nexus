import os
import datetime
def get_metadata(filepath):
    size_file = os.path.getsize(filepath)
    modified_timestamp = os.path.getmtime(filepath)
    created_timestamp = os.path.getctime(filepath)

    def format_size(size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{round(size / 1024, 2)} KB"
        else:
            return f"{round(size / (1024 * 1024), 2)} MB"
    def format_time(time):
        return datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%d")

    ''' raw_metadata = {
        "size": size_file ,
        "name": os.path.basename(filepath),
        "last_modified": modified_timestamp,
        "created": created_timestamp,
    }'''

    metadata = {
        "size": format_size(size_file),
        "name": os.path.basename(filepath),
        "last_modified": format_time(modified_timestamp),
        "created": format_time(created_timestamp),
    }
    return metadata



