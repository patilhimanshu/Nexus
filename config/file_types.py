# Tuple means: (parent_folder, subfolder)
# If subfolder is empty "", files go directly into the parent folder

extension_map = {

    # Media → Images
    ".png":  ("Media", "Images"),
    ".jpg":  ("Media", "Images"),
    ".jpeg": ("Media", "Images"),
    ".gif":  ("Media", "Images"),
    ".bmp":  ("Media", "Images"),
    ".svg":  ("Media", "Images"),
    ".webp": ("Media", "Images"),
    ".ico":  ("Media", "Images"),

    # Media → Videos
    ".mp4":  ("Media", "Videos"),
    ".webm": ("Media", "Videos"),
    ".mkv":  ("Media", "Videos"),
    ".avi":  ("Media", "Videos"),
    ".mov":  ("Media", "Videos"),

    # Media → Audio
    ".mp3":  ("Media", "Audio"),
    ".wav":  ("Media", "Audio"),
    ".flac": ("Media", "Audio"),
    ".aac":  ("Media", "Audio"),
    ".ogg":  ("Media", "Audio"),

    # Documents → PDF
    ".pdf":  ("Documents", "PDF"),

    # Documents → Word
    ".doc":  ("Documents", "Word"),
    ".docx": ("Documents", "Word"),
    ".odt":  ("Documents", "Word"),

    # Documents → Text
    ".txt":  ("Documents", "Text"),

    # Documents → Presentations
    ".pptx": ("Documents", "Presentations"),
    ".ppt":  ("Documents", "Presentations"),

    # Documents → Spreadsheets
    ".xlsx": ("Documents", "Spreadsheets"),
    ".xls":  ("Documents", "Spreadsheets"),
    ".csv":  ("Documents", "Spreadsheets"),

    # Archives (no subfolder needed)
    ".zip":  ("Archives", ""),
    ".rar":  ("Archives", ""),
    ".7z":   ("Archives", ""),
    ".tar":  ("Archives", ""),
    ".gz":   ("Archives", ""),

    # Code → by language
    ".py":   ("Code", "Python"),
    ".js":   ("Code", "JavaScript"),
    ".ts":   ("Code", "TypeScript"),
    ".html": ("Code", "Web"),
    ".css":  ("Code", "Web"),
    ".java": ("Code", "Java"),
    ".cpp":  ("Code", "CPP"),
    ".c":    ("Code", "C"),
    ".json": ("Code", "Data"),

    # Junk / System files
    ".tmp":  ("Junk", ""),
    ".log":  ("Junk", ""),
    ".cache":("Junk", ""),
    ".ini":  ("Junk", ""),
    ".lnk":  ("Junk", ""),

}