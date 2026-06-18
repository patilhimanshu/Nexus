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

    metadata = {
        "name": os.path.basename(filepath),
        "size": {
            "raw": size_file,
            "formatted": format_size(size_file),
        },

        "last_modified" : {
            "raw": modified_timestamp,
            "formatted": format_time(modified_timestamp),
        },

        "created": {
            "raw": created_timestamp,
            "formatted": format_time(created_timestamp),
        }
    }

    return metadata



